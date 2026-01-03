"""Main client class for interacting with the Handelsregister portal."""

import argparse
import logging
import pathlib
import sys
import time
import urllib.error
from typing import Any, Literal, Optional

import mechanize
from ratelimit import limits, sleep_and_retry
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from tqdm import tqdm

from .cache import SearchCache
from .constants import KEYWORD_OPTIONS, RESULTS_PER_PAGE_OPTIONS, STATE_CODES
from .exceptions import FormError, NetworkError, ParseError, PartialResultError
from .models import CacheEntry, Company, CompanyDetails, SearchOptions
from .parser import DetailsParser, ResultParser
from .settings import (
    BASE_URL,
    MAX_RETRIES,
    RATE_LIMIT_CALLS,
    RATE_LIMIT_PERIOD,
    REQUEST_TIMEOUT,
    RETRY_WAIT_MAX,
    RETRY_WAIT_MIN,
)

logger = logging.getLogger(__name__)


def _with_retry_and_rate_limit(func):
    """Decorator that applies rate limiting and retry logic to a method.
    
    Combines rate limiting (60 calls/hour) with exponential backoff retry
    logic for network operations. This decorator stack is reused across
    all network operations in HandelsRegister.
    """
    decorated = sleep_and_retry(
        limits(calls=RATE_LIMIT_CALLS, period=RATE_LIMIT_PERIOD)(
            retry(
                stop=stop_after_attempt(MAX_RETRIES),
                wait=wait_exponential(multiplier=1, min=RETRY_WAIT_MIN, max=RETRY_WAIT_MAX),
                retry=retry_if_exception_type(urllib.error.URLError),
                before_sleep=before_sleep_log(logger, logging.WARNING),
                reraise=True,
            )(func)
        )
    )
    return decorated


class HandelsRegister:
    """Browser-Automatisierung für die Handelsregister-Suche.
    
    Verwaltet die Interaktion mit der Handelsregister-Website, Navigation,
    Formular-Übermittlung und Ergebnis-Abruf.
    
    Beispiel:
        >>> hr = HandelsRegister(debug=False)
        >>> hr.open_startpage()
        >>> results = hr.search_with_options(SearchOptions(keywords="Bank", states=["BE"]))
    """
    
    def __init__(
        self,
        args: Optional[argparse.Namespace] = None,
        cache: Optional[SearchCache] = None,
        debug: bool = False,
    ) -> None:
        """Initialisiert den HandelsRegister-Client.
        
        Args:
            args: CLI-Argumente (optional, für Rückwärtskompatibilität).
            cache: Cache-Instanz (optional, wird automatisch erstellt).
            debug: Debug-Logging aktivieren.
        """
        self.args = args
        self.cache = cache or SearchCache()
        self._debug = debug if args is None else getattr(args, 'debug', False)
        self.browser = self._create_browser(debug=self._debug)
    
    @classmethod
    def from_options(
        cls,
        options: SearchOptions,
        cache: Optional[SearchCache] = None,
        debug: bool = False,
    ) -> 'HandelsRegister':
        """Erstellt einen Client mit SearchOptions.
        
        Args:
            options: Suchoptionen.
            cache: Cache-Instanz (optional).
            debug: Debug-Logging aktivieren.
            
        Returns:
            Konfigurierte HandelsRegister-Instanz.
        """
        instance = cls(args=None, cache=cache, debug=debug)
        instance._default_options = options
        return instance
    
    def _create_browser(self, debug: bool = False) -> mechanize.Browser:
        """Creates and configures a mechanize browser instance.
        
        Args:
            debug: Enable debug output for HTTP requests.
            
        Returns:
            Configured Browser instance.
        """
        browser = mechanize.Browser()
        
        browser.set_debug_http(debug)
        browser.set_debug_responses(debug)
        
        browser.set_handle_robots(False)
        browser.set_handle_equiv(True)
        browser.set_handle_gzip(True)
        browser.set_handle_refresh(False)
        browser.set_handle_redirect(True)
        browser.set_handle_referer(True)
        
        browser.addheaders = [
            ("User-Agent", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                          "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15"),
            ("Accept-Language", "en-GB,en;q=0.9"),
            ("Accept-Encoding", "gzip, deflate, br"),
            ("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
            ("Connection", "keep-alive"),
        ]
        
        return browser
    
    # Backward compatibility: expose cachedir
    @property
    def cachedir(self) -> pathlib.Path:
        """Gets the cache directory path."""
        return self.cache.cache_dir
    
    @_with_retry_and_rate_limit
    def open_startpage(self) -> None:
        """Opens the Handelsregister start page with automatic retries.
        
        Uses exponential backoff for retries on network failures.
        Rate limited to 60 requests per hour per portal terms of service.
        
        Raises:
            NetworkError: If the connection fails after all retry attempts.
        """
        try:
            self.browser.open(str(BASE_URL), timeout=REQUEST_TIMEOUT)
        except urllib.error.URLError as e:
            raise NetworkError(
                f"Failed to connect to handelsregister.de: {e.reason}",
                original_error=e
            ) from e
        except mechanize.BrowserStateError as e:
            raise NetworkError(
                f"Browser state error: {e}",
                original_error=e
            ) from e
    
    def _build_search_options(self) -> SearchOptions:
        """Builds SearchOptions from command-line arguments.
        
        Returns:
            SearchOptions instance with all search parameters.
        """
        states = None
        if hasattr(self.args, 'states') and self.args.states:
            states = [s.strip().upper() for s in self.args.states.split(',')]
        
        return SearchOptions(
            keywords=self.args.schlagwoerter,
            keyword_option=self.args.schlagwortOptionen,
            states=states,
            register_type=getattr(self.args, 'register_type', None),
            register_number=getattr(self.args, 'register_number', None),
            include_deleted=getattr(self.args, 'include_deleted', False),
            similar_sounding=getattr(self.args, 'similar_sounding', False),
            results_per_page=getattr(self.args, 'results_per_page', 100),
        )
    
    def search_with_options(
        self,
        options: SearchOptions,
        force_refresh: bool = False,
    ) -> list[Company]:
        """Führt eine Suche mit SearchOptions durch.
        
        Args:
            options: Suchoptionen.
            force_refresh: Cache ignorieren.
            
        Returns:
            Liste von Dictionaries mit Unternehmensdaten.
            
        Raises:
            NetworkError: Bei Netzwerkfehlern.
            FormError: Bei Formular-Problemen.
            ParseError: Bei Parse-Fehlern.
        """
        cache_key = options.cache_key()
        
        # Try to load from cache
        if not force_refresh:
            cached_html = self.cache.get(cache_key, "")
            if cached_html is not None:
                logger.info("Cache-Treffer für: %s", options.keywords)
                return ResultParser.parse_search_results(cached_html)
        
        # Fetch fresh data from website
        html = self._fetch_search_results(options)
        
        # Save to cache
        self.cache.set(cache_key, "", html)
        
        return ResultParser.parse_search_results(html)
    
    def search_company(self) -> list[Company]:
        """Sucht nach Unternehmen basierend auf CLI-Argumenten.
        
        Hinweis: Für programmatische Nutzung wird search_with_options() empfohlen.
        
        Returns:
            Liste von Dictionaries mit Unternehmensdaten.
            
        Raises:
            NetworkError: Bei Netzwerkfehlern.
            FormError: Bei Formular-Problemen.
            ParseError: Bei Parse-Fehlern.
        """
        if self.args is None:
            raise ValueError("search_company() benötigt args. Nutze search_with_options() stattdessen.")
        
        search_opts = self._build_search_options()
        force_refresh = getattr(self.args, 'force', False)
        return self.search_with_options(search_opts, force_refresh=force_refresh)
    
    def _fetch_search_results(self, search_opts: SearchOptions) -> str:
        """Fetches search results from the website.
        
        Args:
            search_opts: Search options specifying all search parameters.
            
        Returns:
            HTML content of search results page.
            
        Raises:
            NetworkError: If network requests fail.
            FormError: If form selection or submission fails.
        """
        self._navigate_to_search()
        return self._submit_search(search_opts)
    
    @_with_retry_and_rate_limit
    def _navigate_to_search(self) -> None:
        """Navigates from start page to extended search form with retries.
        
        Uses exponential backoff for retries on network failures.
        Rate limited to 60 requests per hour per portal terms of service.
        
        Raises:
            FormError: If navigation form is not found.
            NetworkError: If form submission fails after all retries.
        """
        try:
            self.browser.select_form(name="naviForm")
        except mechanize.FormNotFoundError as e:
            raise FormError(
                f"Navigation form not found. The website structure may have changed: {e}"
            ) from e
        
        self.browser.form.new_control(
            'hidden', 
            'naviForm:erweiterteSucheLink', 
            {'value': 'naviForm:erweiterteSucheLink'}
        )
        self.browser.form.new_control('hidden', 'target', {'value': 'erweiterteSucheLink'})
        
        try:
            self.browser.submit()
        except urllib.error.URLError as e:
            raise NetworkError(
                f"Failed to submit navigation form: {e.reason}", 
                original_error=e
            ) from e
        
        logger.debug("Page title after navigation: %s", self.browser.title())
    
    @_with_retry_and_rate_limit
    def _submit_search(self, search_opts: SearchOptions) -> str:
        """Submits the search form and returns results HTML with retries.
        
        Uses exponential backoff for retries on network failures.
        Rate limited to 60 requests per hour per portal terms of service.
        
        Args:
            search_opts: Search options specifying all search parameters.
            
        Returns:
            HTML content of search results page.
            
        Raises:
            FormError: If search form is not found.
            NetworkError: If form submission fails after all retries.
        """
        try:
            self.browser.select_form(name="form")
        except mechanize.FormNotFoundError as e:
            raise FormError(
                f"Search form not found. The website structure may have changed: {e}"
            ) from e
        
        self.browser["form:schlagwoerter"] = search_opts.keywords
        option_id = KEYWORD_OPTIONS.get(search_opts.keyword_option)
        self.browser["form:schlagwortOptionen"] = [str(option_id)]
        
        if search_opts.states:
            for state_code in search_opts.states:
                if state_code in STATE_CODES:
                    try:
                        state_name = STATE_CODES[state_code]
                        control_name = f"form:{state_name}_input"
                        self.browser.form.find_control(control_name).value = ["on"]
                        logger.debug("Enabled state filter: %s (%s)", state_code, state_name)
                    except mechanize.ControlNotFoundError:
                        logger.warning("State control not found: %s", control_name)
        
        if search_opts.register_type:
            try:
                self.browser["form:registerArt_input"] = [search_opts.register_type]
                logger.debug("Set register type: %s", search_opts.register_type)
            except mechanize.ControlNotFoundError:
                logger.warning("Register type control not found")
        
        if search_opts.register_number:
            try:
                self.browser["form:registerNummer"] = search_opts.register_number
                logger.debug("Set register number: %s", search_opts.register_number)
            except mechanize.ControlNotFoundError:
                logger.warning("Register number control not found")
        
        if search_opts.include_deleted:
            try:
                self.browser.form.find_control("form:auchGeloeschte_input").value = ["on"]
                logger.debug("Enabled include deleted option")
            except mechanize.ControlNotFoundError:
                logger.warning("Include deleted control not found")
        
        if search_opts.similar_sounding:
            try:
                self.browser.form.find_control("form:aenlichLautendeSchlagwoerterBoolChkbox_input").value = ["on"]
                logger.debug("Enabled similar sounding option")
            except mechanize.ControlNotFoundError:
                logger.warning("Similar sounding control not found")
        
        if search_opts.results_per_page in RESULTS_PER_PAGE_OPTIONS:
            try:
                self.browser["form:ergebnisseProSeite_input"] = [str(search_opts.results_per_page)]
                logger.debug("Set results per page: %d", search_opts.results_per_page)
            except mechanize.ControlNotFoundError:
                logger.warning("Results per page control not found")
        
        try:
            response = self.browser.submit()
        except urllib.error.URLError as e:
            raise NetworkError(
                f"Failed to submit search form: {e.reason}", 
                original_error=e
            ) from e
        
        logger.debug("Page title after search: %s", self.browser.title())
        
        return response.read().decode("utf-8")
    
    # =========================================================================
    # Detail Fetching Methods
    # =========================================================================
    
    def get_company_details(
        self,
        company: Company,
        detail_type: Literal["SI", "AD", "UT", "CD", "HD", "VÖ"] = "SI",
        force_refresh: bool = False,
        fallback_types: Optional[list[Literal["SI", "AD", "UT", "CD", "HD", "VÖ"]]] = None,
    ) -> CompanyDetails:
        """Fetches detailed company information with optional fallback strategies.
        
        Args:
            company: Company dict from search results (must contain row_index).
            detail_type: Type of details to fetch:
                - "SI": Strukturierter Registerinhalt (structured, recommended)
                - "AD": Aktueller Abdruck (current printout)
                - "UT": Unternehmensträger (company owners)
            force_refresh: Skip cache and fetch fresh data.
            fallback_types: List of alternative detail types to try if primary fails.
                If None, defaults to ["AD", "UT"] for graceful degradation.
            
        Returns:
            CompanyDetails with all available information.
            
        Raises:
            NetworkError: If the request fails after all retries and fallbacks.
            ParseError: If parsing fails for all attempted types.
            ValueError: If company dict is missing required fields.
        """
        valid_types = ["SI", "AD", "UT", "CD", "HD", "VÖ"]
        if detail_type not in valid_types:
            raise ValueError(f"Invalid detail_type: {detail_type}. Must be one of {valid_types}")
        
        # Default fallback types if not specified
        if fallback_types is None:
            fallback_types = ["AD", "UT"]
        
        # Try primary detail type first
        types_to_try = [detail_type] + [ft for ft in fallback_types if ft != detail_type and ft in valid_types]
        last_error: Optional[Exception] = None
        
        for attempt_type in types_to_try:
            cache_key = f"details:{attempt_type}:{company.register_num or ''}:{company.court}"
            
            try:
                if not force_refresh:
                    cached_html = self.cache.get(cache_key, "")
                    if cached_html is not None:
                        logger.info("Cache hit for details: %s", cache_key)
                        return self._parse_details(cached_html, company, attempt_type)
                
                html = self._fetch_detail_page(company, attempt_type)
                self.cache.set(cache_key, "", html)
                
                return self._parse_details(html, company, attempt_type)
                
            except (NetworkError, ParseError) as e:
                last_error = e
                if attempt_type != types_to_try[-1]:  # Not the last attempt
                    logger.warning(
                        "Failed to fetch %s details for %s, trying fallback: %s",
                        attempt_type,
                        company.name or 'unknown',
                        e
                    )
                else:
                    # Last attempt failed, re-raise with context
                    raise
            except Exception as e:
                last_error = e
                if attempt_type != types_to_try[-1]:
                    logger.warning(
                        "Unexpected error fetching %s details for %s, trying fallback: %s",
                        attempt_type,
                        company.name or 'unknown',
                        e
                    )
                else:
                    raise
        
        # Should never reach here, but just in case
        if last_error:
            raise last_error
        raise NetworkError("Failed to fetch company details after all attempts")
    
    @_with_retry_and_rate_limit
    def _fetch_detail_page(self, company: Company, detail_type: str) -> str:
        """Fetches a detail page for a company with retries.
        
        The Handelsregister uses JSF/PrimeFaces which requires specific
        form parameters. We reconstruct these based on the search results.
        Uses exponential backoff for retries on network failures.
        Rate limited to 60 requests per hour per portal terms of service.
        
        Args:
            company: Company dict with at least 'row_index' from search.
            detail_type: Type of detail page (SI, AD, UT, etc.).
            
        Returns:
            HTML content of the detail page.
        """
        row_index = company.row_index or 0
        
        detail_type_mapping = {
            'AD': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:0:fade',
            'CD': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:1:fade',
            'HD': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:2:fade',
            'UT': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:4:fade',
            'VÖ': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:5:fade',
            'SI': 'ergebnissForm:selectedSuchErgebnisFormTable:{row}:j_idt161:6:fade',
        }
        
        control_name = detail_type_mapping.get(detail_type, detail_type_mapping['SI'])
        control_name = control_name.format(row=row_index)
        
        try:
            self.browser.select_form(name="ergebnissForm")
            self.browser.form.new_control('hidden', control_name, {'value': control_name})
            response = self.browser.submit()
            return response.read().decode("utf-8")
            
        except mechanize.FormNotFoundError:
            logger.warning("Results form not found, using alternative fetch method")
            return self._fetch_detail_alternative(company, detail_type)
        except urllib.error.URLError as e:
            raise NetworkError(
                f"Failed to fetch detail page: {e.reason}",
                original_error=e
            ) from e
    
    def _fetch_detail_alternative(self, company: Company, detail_type: str) -> str:
        """Alternative method to fetch details when form is not available.
        
        This method constructs a direct request based on company information.
        Full implementation requires JSF viewstate handling.
        """
        register_num = company.register_num or ''
        _court = company.court
        _state = company.state
        
        logger.warning(
            "Alternative fetch not fully implemented for %s %s", 
            register_num, detail_type
        )
        return ""
    
    def _parse_details(
        self, 
        html: str, 
        company: Company, 
        detail_type: str
    ) -> CompanyDetails:
        """Parses detail HTML into CompanyDetails.
        
        Args:
            html: HTML content of detail page.
            company: Base company info from search.
            detail_type: Type of detail page.
            
        Returns:
            Parsed CompanyDetails.
        """
        if detail_type == "SI":
            return DetailsParser.parse_si(html, company)
        elif detail_type == "AD":
            return DetailsParser.parse_ad(html, company)
        elif detail_type == "UT":
            return DetailsParser.parse_ut(html, company)
        else:
            return DetailsParser.parse_si(html, company)
    
    def search_with_details(
        self,
        options: SearchOptions,
        fetch_details: bool = True,
        detail_type: Literal["SI", "AD", "UT", "CD", "HD", "VÖ"] = "SI",
        force_refresh: bool = False,
        show_progress: Optional[bool] = None,
        continue_on_error: bool = True,
        raise_partial: bool = False,
    ) -> list[CompanyDetails]:
        """Searches for companies and optionally fetches details.
        
        Args:
            options: Search options.
            fetch_details: Whether to fetch details for each result.
            detail_type: Type of details to fetch (SI, AD, UT).
            force_refresh: Skip cache.
            show_progress: Show progress bar (auto-detected if None based on TTY).
            continue_on_error: Continue processing other companies if one fails.
            raise_partial: Raise PartialResultError if any failures occur.
            
        Returns:
            List of CompanyDetails with full information.
            
        Raises:
            PartialResultError: If raise_partial=True and some operations failed.
        """
        companies = self.search_with_options(options, force_refresh=force_refresh)
        
        if not fetch_details:
            return [CompanyDetails.from_company(c) for c in companies]
        
        # Auto-detect if we should show progress (only if TTY and more than 1 item)
        if show_progress is None:
            show_progress = sys.stdout.isatty() and len(companies) > 1
        
        results: list[CompanyDetails] = []
        failed: list[tuple[Company, Exception]] = []
        iterator = tqdm(companies, desc="Fetching details", unit="company", disable=not show_progress)
        
        for i, company in enumerate(iterator):
            company.row_index = i
            company_name = company.name
            if show_progress:
                iterator.set_postfix(name=company_name[:30])
            
            try:
                details = self.get_company_details(
                    company, 
                    detail_type=detail_type,
                    force_refresh=force_refresh
                )
                results.append(details)
            except (NetworkError, ParseError) as e:
                if not continue_on_error:
                    raise
                
                logger.warning(
                    "Failed to fetch details for %s (%s): %s",
                    company_name,
                    company.register_num or 'N/A',
                    e
                )
                
                # Try fallback: use basic company info
                try:
                    fallback = CompanyDetails.from_company(company)
                    results.append(fallback)
                except Exception as fallback_error:
                    logger.error(
                        "Failed to create fallback for %s: %s",
                        company_name,
                        fallback_error
                    )
                    failed.append((company, e))
            except Exception as e:
                # Unexpected error
                logger.error(
                    "Unexpected error fetching details for %s: %s",
                    company_name,
                    e,
                    exc_info=True
                )
                if not continue_on_error:
                    raise
                failed.append((company, e))
                # Still try to add basic info
                try:
                    results.append(CompanyDetails.from_company(company))
                except Exception:
                    pass
        
        # Raise partial result error if requested and there were failures
        if raise_partial and failed:
            raise PartialResultError(
                f"Batch operation completed with {len(failed)} failures out of {len(companies)} total",
                successful=results,
                failed=failed,
            )
        
        return results
    
    def _get_cache_key(self, query: str, options: str) -> str:
        """Generates cache key. Deprecated: use cache.get/set instead."""
        return self.cache._get_cache_key(query, options)
    
    def _get_cache_path(self, query: str, options: str) -> pathlib.Path:
        """Gets cache path. Deprecated: use cache.get/set instead."""
        return self.cache._get_cache_path(query, options)
    
    def _load_from_cache(self, query: str, options: str) -> Optional[CacheEntry]:
        """Loads from cache. Deprecated: use cache.get instead."""
        html = self.cache.get(query, options)
        if html is None:
            return None
        return CacheEntry(query=query, options=options, timestamp=time.time(), html=html)
    
    def _save_to_cache(self, query: str, options: str, html: str) -> None:
        """Saves to cache. Deprecated: use cache.set instead."""
        self.cache.set(query, options, html)

