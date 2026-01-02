"""Command-line interface for the Handelsregister package."""

import argparse
import json
import logging
import sys
from typing import Optional

from .client import HandelsRegister
from .constants import REGISTER_TYPES, RESULTS_PER_PAGE_OPTIONS, STATE_CODES
from .exceptions import (
    CacheError,
    FormError,
    HandelsregisterError,
    NetworkError,
    ParseError,
)
from .models import CompanyDetails, SearchOptions


def pr_company_info(c: dict) -> None:
    """Prints company information to stdout.
    
    Args:
        c: Dictionary containing company information.
    """
    for tag in ('name', 'court', 'register_num', 'district', 'state', 'statusCurrent'):
        print(f"{tag}: {c.get(tag, '-')}")
    print('history:')
    for name, loc in c.get('history', []):
        print(name, loc)


def parse_args() -> argparse.Namespace:
    """Parses command-line arguments.
    
    Returns:
        Parsed arguments namespace.
    """
    state_codes_help = ", ".join(f"{k}={v}" for k, v in sorted(STATE_CODES.items()))
    
    parser = argparse.ArgumentParser(
        description='A handelsregister CLI for the German commercial register',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  %(prog)s -s "Deutsche Bahn" -so all
  %(prog)s -s "GASAG AG" -so exact --json
  %(prog)s -s "Munich" --states BE,BY --register-type HRB
  %(prog)s -s "Bank" --include-deleted --similar-sounding

State codes: {state_codes_help}
        """
    )
    
    # General options
    parser.add_argument(
        "-d", "--debug",
        help="Enable debug mode and activate logging",
        action="store_true"
    )
    parser.add_argument(
        "-f", "--force",
        help="Force a fresh pull and skip the cache",
        action="store_true"
    )
    parser.add_argument(
        "-j", "--json",
        help="Return response as JSON",
        action="store_true"
    )
    
    # Search parameters
    search_group = parser.add_argument_group('Search parameters')
    search_group.add_argument(
        "-s", "--schlagwoerter",
        help="Search for the provided keywords (required)",
        required=True,
        metavar="KEYWORDS"
    )
    search_group.add_argument(
        "-so", "--schlagwortOptionen",
        help="Keyword matching: all=all keywords; min=at least one; exact=exact name",
        choices=["all", "min", "exact"],
        default="all",
        metavar="OPTION"
    )
    search_group.add_argument(
        "--states",
        help="Comma-separated list of state codes to filter by (e.g., BE,BY,HH)",
        metavar="CODES"
    )
    search_group.add_argument(
        "--register-type",
        dest="register_type",
        help="Filter by register type",
        choices=REGISTER_TYPES,
        metavar="TYPE"
    )
    search_group.add_argument(
        "--register-number",
        dest="register_number",
        help="Search for a specific register number",
        metavar="NUMBER"
    )
    search_group.add_argument(
        "--include-deleted",
        dest="include_deleted",
        help="Include deleted/historical entries in results",
        action="store_true"
    )
    search_group.add_argument(
        "--similar-sounding",
        dest="similar_sounding",
        help="Use phonetic/similarity search (Kölner Phonetik)",
        action="store_true"
    )
    search_group.add_argument(
        "--results-per-page",
        dest="results_per_page",
        help="Number of results per page",
        type=int,
        choices=RESULTS_PER_PAGE_OPTIONS,
        default=100,
        metavar="N"
    )
    
    # Detail options
    detail_group = parser.add_argument_group('Detail options')
    detail_group.add_argument(
        "--details",
        help="Fetch detailed information for each company result",
        action="store_true"
    )
    detail_group.add_argument(
        "--detail-type",
        dest="detail_type",
        help="Type of details to fetch: SI=structured, AD=printout, UT=owners",
        choices=["SI", "AD", "UT"],
        default="SI",
        metavar="TYPE"
    )
    
    args = parser.parse_args()
    
    if args.debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            stream=sys.stdout
        )
        mechanize_logger = logging.getLogger("mechanize")
        mechanize_logger.setLevel(logging.DEBUG)
    else:
        logging.basicConfig(
            level=logging.WARNING,
            format='%(levelname)s: %(message)s'
        )
    
    return args


def search(
    keywords: str,
    keyword_option: str = "all",
    states: Optional[list[str]] = None,
    register_type: Optional[str] = None,
    register_number: Optional[str] = None,
    include_deleted: bool = False,
    similar_sounding: bool = False,
    results_per_page: int = 100,
    force_refresh: bool = False,
    debug: bool = False,
) -> list[dict]:
    """Durchsucht das Handelsregister nach Unternehmen.
    
    Dies ist die Haupt-API für die programmatische Nutzung des Packages.
    
    Args:
        keywords: Suchbegriffe (erforderlich).
        keyword_option: Suchmodus - "all" (alle Begriffe), "min" (mindestens einer), 
                       "exact" (exakter Firmenname). Standard: "all".
        states: Liste von Bundesland-Codes zum Filtern (z.B. ["BE", "BY", "HH"]).
        register_type: Registerart-Filter (HRA, HRB, GnR, PR, VR).
        register_number: Spezifische Registernummer suchen.
        include_deleted: Auch gelöschte Einträge anzeigen.
        similar_sounding: Phonetische Suche (Kölner Phonetik) verwenden.
        results_per_page: Ergebnisse pro Seite (10, 25, 50, 100). Standard: 100.
        force_refresh: Cache ignorieren und neue Daten abrufen.
        debug: Debug-Logging aktivieren.
        
    Returns:
        Liste von Dictionaries mit Unternehmensdaten. Jedes Dictionary enthält:
        - name: Firmenname
        - court: Registergericht
        - register_num: Registernummer (z.B. "HRB 12345 B")
        - state: Bundesland
        - status: Aktueller Status
        - statusCurrent: Normalisierter Status (z.B. "CURRENTLY_REGISTERED")
        - documents: Verfügbare Dokumente
        - history: Liste von (Name, Ort) Tupeln mit historischen Einträgen
        
    Raises:
        NetworkError: Bei Netzwerkfehlern.
        FormError: Wenn die Website-Struktur sich geändert hat.
        ParseError: Bei Fehlern beim Parsen der Ergebnisse.
        
    Beispiel:
        >>> from handelsregister import search
        >>> 
        >>> # Einfache Suche
        >>> companies = search("Deutsche Bahn")
        >>> 
        >>> # Mit Filtern
        >>> banks = search("Bank", states=["BE", "HH"], register_type="HRB")
        >>> 
        >>> for company in banks:
        ...     print(f"{company['name']} - {company['register_num']}")
    """
    # Configure logging if debug mode
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Build args namespace for HandelsRegister
    args = argparse.Namespace(
        debug=debug,
        force=force_refresh,
        json=False,
        schlagwoerter=keywords,
        schlagwortOptionen=keyword_option,
        states=",".join(states) if states else None,
        register_type=register_type,
        register_number=register_number,
        include_deleted=include_deleted,
        similar_sounding=similar_sounding,
        results_per_page=results_per_page,
    )
    
    hr = HandelsRegister(args)
    hr.open_startpage()
    return hr.search_company()


def search_batch(
    keywords_list: list[str],
    states: Optional[list[str]] = None,
    register_type: Optional[str] = None,
    show_progress: Optional[bool] = None,
    **kwargs
) -> dict[str, list[dict]]:
    """Performs multiple searches with progress indicators.
    
    Useful for batch processing multiple keywords or search terms.
    
    Args:
        keywords_list: List of keywords to search for.
        states: List of state codes to filter by.
        register_type: Register type filter.
        show_progress: Show progress bar (auto-detected if None).
        **kwargs: Additional arguments passed to search().
        
    Returns:
        Dictionary mapping keywords to their search results.
        
    Example:
        >>> from handelsregister import search_batch
        >>> 
        >>> keywords = ["Bank", "Versicherung", "Immobilien"]
        >>> results = search_batch(keywords, states=["BE", "HH"])
        >>> for keyword, companies in results.items():
        ...     print(f"{keyword}: {len(companies)} companies")
    """
    import sys
    from tqdm import tqdm
    
    # Auto-detect if we should show progress
    if show_progress is None:
        show_progress = sys.stdout.isatty() and len(keywords_list) > 1
    
    results: dict[str, list[dict]] = {}
    iterator = tqdm(keywords_list, desc="Searching", unit="keyword", disable=not show_progress)
    
    for keyword in iterator:
        if show_progress:
            iterator.set_postfix(keyword=keyword[:30])
        try:
            results[keyword] = search(
                keyword,
                states=states,
                register_type=register_type,
                **kwargs
            )
        except Exception as e:
            # Log error but continue with other searches
            import logging
            logger = logging.getLogger(__name__)
            logger.error("Failed to search for '%s': %s", keyword, e)
            results[keyword] = []
    
    return results


def get_details(
    company: dict,
    detail_type: str = "SI",
    force_refresh: bool = False,
    debug: bool = False,
) -> CompanyDetails:
    """Ruft detaillierte Unternehmensinformationen ab.
    
    Diese Funktion ruft erweiterte Informationen zu einem Unternehmen ab,
    das zuvor über search() gefunden wurde.
    
    Args:
        company: Unternehmen-Dictionary aus den Suchergebnissen.
        detail_type: Art der Details:
            - "SI": Strukturierter Registerinhalt (empfohlen)
            - "AD": Aktueller Abdruck
            - "UT": Unternehmensträger
        force_refresh: Cache ignorieren.
        debug: Debug-Logging aktivieren.
        
    Returns:
        CompanyDetails mit allen verfügbaren Informationen.
        
    Beispiel:
        >>> from handelsregister import search, get_details
        >>> 
        >>> # Erst suchen
        >>> companies = search("GASAG AG", keyword_option="exact")
        >>> 
        >>> # Dann Details abrufen
        >>> if companies:
        ...     details = get_details(companies[0])
        ...     print(f"Kapital: {details.capital} {details.currency}")
        ...     print(f"Rechtsform: {details.legal_form}")
    """
    if debug:
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    hr = HandelsRegister(debug=debug)
    hr.open_startpage()
    
    register_num = company.get('register_num', '')
    name = company.get('name', '')
    
    if register_num:
        search_opts = SearchOptions(
            keywords=name,
            keyword_option="exact",
        )
    else:
        search_opts = SearchOptions(
            keywords=name,
            keyword_option="all",
        )
    
    hr.search_with_options(search_opts, force_refresh=force_refresh)
    company['row_index'] = 0
    return hr.get_company_details(company, detail_type, force_refresh)


def pr_company_details(details: CompanyDetails) -> None:
    """Prints detailed company information to stdout.
    
    Args:
        details: CompanyDetails object with all information.
    """
    print(f"{'='*60}")
    print(f"Firma: {details.name}")
    print(f"Registernummer: {details.register_num}")
    print(f"Gericht: {details.court}")
    print(f"Bundesland: {details.state}")
    print(f"Status: {details.status}")
    
    if details.legal_form:
        print(f"Rechtsform: {details.legal_form}")
    
    if details.capital:
        currency = details.currency or "EUR"
        print(f"Kapital: {details.capital} {currency}")
    
    if details.address:
        print(f"Adresse: {details.address}")
    
    if details.purpose:
        print(f"Gegenstand: {details.purpose[:100]}{'...' if len(details.purpose) > 100 else ''}")
    
    if details.representatives:
        print("Vertretung:")
        for rep in details.representatives:
            loc = f" ({rep.location})" if rep.location else ""
            print(f"  - {rep.role}: {rep.name}{loc}")
    
    if details.owners:
        print("Gesellschafter:")
        for owner in details.owners:
            share = f" - {owner.share}" if owner.share else ""
            print(f"  - {owner.name}{share}")
    
    if details.registration_date:
        print(f"Eingetragen: {details.registration_date}")
    
    print()


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        Exit code (0 for success, non-zero for errors).
    """
    args = parse_args()
    
    try:
        hr = HandelsRegister(args)
        hr.open_startpage()
        
        fetch_details = getattr(args, 'details', False)
        detail_type = getattr(args, 'detail_type', 'SI')
        
        if fetch_details:
            search_opts = hr._build_search_options()
            companies_details = hr.search_with_details(
                search_opts,
                fetch_details=True,
                detail_type=detail_type,
                force_refresh=getattr(args, 'force', False),
                show_progress=not args.json,  # Show progress unless JSON output
            )
            
            if companies_details:
                if args.json:
                    print(json.dumps([d.to_dict() for d in companies_details]))
                else:
                    for details in companies_details:
                        pr_company_details(details)
        else:
            companies = hr.search_company()
            
            if companies:
                if args.json:
                    print(json.dumps(companies))
                else:
                    for c in companies:
                        pr_company_info(c)
        
        return 0
        
    except NetworkError as e:
        print(f"Network error: {e}", file=sys.stderr)
        if args.debug and e.original_error:
            print(f"Original error: {e.original_error}", file=sys.stderr)
        return 1
        
    except FormError as e:
        print(f"Form error: {e}", file=sys.stderr)
        return 2
        
    except ParseError as e:
        print(f"Parse error: {e}", file=sys.stderr)
        if args.debug and e.html_snippet:
            print(f"HTML snippet: {e.html_snippet}", file=sys.stderr)
        return 3
        
    except CacheError as e:
        print(f"Cache error: {e}", file=sys.stderr)
        return 4
        
    except HandelsregisterError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

