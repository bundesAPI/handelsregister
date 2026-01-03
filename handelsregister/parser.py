"""HTML parsing layer for the Handelsregister package."""

import re
from typing import Any, Literal, Optional

from bs4 import BeautifulSoup
from bs4.element import Tag
from dateutil import parser as dateutil_parser
from dateutil.parser import ParserError

from .constants import SUFFIX_MAP
from .exceptions import ParseError
from .models import Address, Company, CompanyDetails, HistoryEntry, Owner, Representative


class DetailsParser:
    """Parses detail view HTML (SI, AD, UT) into CompanyDetails objects."""
    
    # Common patterns for extracting data
    CAPITAL_PATTERN = re.compile(
        r'(?:Stamm|Grund)kapital[:\s]*([0-9.,]+)\s*(EUR|€|DM)?',
        re.IGNORECASE
    )
    DATE_PATTERN = re.compile(r'\d{1,2}\.\d{1,2}\.\d{4}')
    
    @classmethod
    def parse_date(cls, text: str, output_format: str = "%d.%m.%Y") -> Optional[str]:
        """Parses a date from text using dateutil.
        
        Handles German date formats (DD.MM.YYYY) and various other formats.
        Returns the date in a normalized format.
        
        Args:
            text: Text containing a date.
            output_format: Output format for the date string.
            
        Returns:
            Normalized date string, or None if no date found.
        """
        # First try to find a German-style date pattern
        date_match = cls.DATE_PATTERN.search(text)
        if date_match:
            date_str = date_match.group(0)
            try:
                # Parse with dayfirst=True for German DD.MM.YYYY format
                parsed = dateutil_parser.parse(date_str, dayfirst=True)
                return parsed.strftime(output_format)
            except (ParserError, ValueError):
                # If dateutil fails, return the original match
                return date_str
        
        # Try dateutil on the entire text as fallback
        try:
            parsed = dateutil_parser.parse(text, dayfirst=True, fuzzy=True)
            return parsed.strftime(output_format)
        except (ParserError, ValueError):
            return None
    
    @classmethod
    def parse_si(cls, html: str, base_info: Optional[Company] = None) -> CompanyDetails:
        """Parses structured register content (SI - Strukturierter Registerinhalt).
        
        Args:
            html: HTML content of the SI detail view.
            base_info: Optional base company info from search results.
            
        Returns:
            CompanyDetails with parsed information.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        # Initialize with base info or empty
        if base_info:
            details = CompanyDetails(
                name=base_info.name,
                register_num=base_info.register_num or '',
                court=base_info.court,
                state=base_info.state,
                status=base_info.status,
            )
        else:
            details = CompanyDetails(
                name='',
                register_num='',
                court='',
                state='',
                status='',
            )
        
        # Parse structured content - typically in tables or definition lists
        details = cls._parse_si_tables(soup, details)
        details = cls._parse_si_sections(soup, details)
        
        return details
    
    @classmethod
    def _parse_si_tables(cls, soup: BeautifulSoup, details: CompanyDetails) -> CompanyDetails:
        """Extracts data from SI tables."""
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)
                    
                    details = cls._map_field(label, value, details)
        
        return details
    
    @classmethod
    def _parse_si_sections(cls, soup: BeautifulSoup, details: CompanyDetails) -> CompanyDetails:
        """Extracts data from SI sections (divs, panels, etc.)."""
        for div in soup.find_all(['div', 'span', 'p']):
            text = div.get_text(strip=True)
            
            if details.capital is None:
                capital_match = cls.CAPITAL_PATTERN.search(text)
                if capital_match:
                    details.capital = capital_match.group(1)
                    if capital_match.group(2):
                        details.currency = capital_match.group(2).replace('€', 'EUR')
            
            if details.legal_form is None:
                details.legal_form = cls._extract_legal_form(text)
            
            reps = cls._extract_representatives(div)
            if reps:
                details.representatives.extend(reps)
        
        return details
    
    @classmethod
    def _map_field(cls, label: str, value: str, details: CompanyDetails) -> CompanyDetails:
        """Maps a label-value pair to the appropriate CompanyDetails field."""
        if not value:
            return details
        
        if any(x in label for x in ['firma', 'name']) and not details.name:
            details.name = value
        elif 'rechtsform' in label:
            details.legal_form = value
        elif 'sitz' in label or 'geschäftsanschrift' in label:
            details.address = cls._parse_address(value)
        elif 'kapital' in label:
            amount_pattern = re.match(r'([0-9.,]+)\s*(EUR|€|DM)?', value)
            if amount_pattern:
                details.capital = amount_pattern.group(1).strip()
                if amount_pattern.group(2):
                    details.currency = amount_pattern.group(2).replace('€', 'EUR')
            else:
                details.capital = value
        elif 'gegenstand' in label or 'unternehmensgegenstand' in label:
            details.purpose = value
        elif 'registernummer' in label or 'aktenzeichen' in label:
            if not details.register_num:
                details.register_num = value
        elif 'eintrag' in label and 'datum' in label:
            details.registration_date = cls.parse_date(value) or value
        elif 'lösch' in label:
            details.deletion_date = cls.parse_date(value) or value
        elif 'änderung' in label or 'aktualisiert' in label:
            details.last_update = cls.parse_date(value) or value
        
        return details
    
    @classmethod
    def _parse_address(cls, text: str) -> Address:
        """Parses an address string into an Address object."""
        plz_city_match = re.search(r'(\d{5})\s+(.+?)(?:,|$)', text)
        
        if plz_city_match:
            postal_code = plz_city_match.group(1)
            city = plz_city_match.group(2).strip()
            street_part = text[:plz_city_match.start()].strip().rstrip(',')
            return Address(
                street=street_part if street_part else None,
                postal_code=postal_code,
                city=city,
            )
        else:
            return Address(city=text)
    
    @classmethod
    def _extract_legal_form(cls, text: str) -> Optional[str]:
        """Extracts legal form from text.
        
        Order matters: more specific forms (like GmbH & Co. KG) must be
        checked before less specific ones (like GmbH or KG).
        """
        legal_forms = [
            ('GmbH & Co. KG', 'GmbH & Co. KG'),
            ('GmbH & Co. OHG', 'GmbH & Co. OHG'),
            ('UG (haftungsbeschränkt) & Co. KG', 'UG & Co. KG'),
            ('Europäische Aktiengesellschaft', 'SE'),
            ('Aktiengesellschaft', 'AG'),
            ('Gesellschaft mit beschränkter Haftung', 'GmbH'),
            ('UG (haftungsbeschränkt)', 'UG'),
            ('Kommanditgesellschaft', 'KG'),
            ('Offene Handelsgesellschaft', 'OHG'),
            ('Eingetragene Genossenschaft', 'eG'),
            ('Eingetragener Verein', 'e.V.'),
            ('Partnerschaftsgesellschaft', 'PartG'),
            ('Einzelkaufmann', 'e.K.'),
            ('Einzelkauffrau', 'e.Kfr.'),
        ]
        
        text_lower = text.lower()
        for full_name, abbreviation in legal_forms:
            if full_name.lower() in text_lower:
                return full_name
            if f' {abbreviation}' in text or text.endswith(abbreviation):
                return full_name
            if abbreviation in text and '&' in abbreviation:
                return full_name
        
        return None
    
    @classmethod
    def _extract_representatives(cls, element: Tag) -> list[Representative]:
        """Extracts representative information from an element."""
        representatives = []
        text = element.get_text()
        
        role_patterns = [
            (r'Geschäftsführer(?:in)?[:\s]+([^,;]+)', 'Geschäftsführer'),
            (r'Vorstand[:\s]+([^,;]+)', 'Vorstand'),
            (r'Prokurist(?:in)?[:\s]+([^,;]+)', 'Prokurist'),
            (r'Inhaber(?:in)?[:\s]+([^,;]+)', 'Inhaber'),
            (r'Persönlich haftende(?:r)? Gesellschafter(?:in)?[:\s]+([^,;]+)', 
             'Persönlich haftender Gesellschafter'),
        ]
        
        for pattern, role in role_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                name = match.group(1).strip()
                if name and len(name) > 2:
                    location = None
                    loc_match = re.search(r'\(([^)]+)\)', name)
                    if loc_match:
                        location = loc_match.group(1)
                        name = name[:loc_match.start()].strip()
                    
                    representatives.append(Representative(
                        name=name,
                        role=role,
                        location=location,
                    ))
        
        return representatives
    
    @classmethod
    def parse_ad(cls, html: str, base_info: Optional[Company] = None) -> CompanyDetails:
        """Parses current printout (AD - Aktueller Abdruck).
        
        The AD view contains the current state of the register entry as
        formatted text rather than structured tables.
        
        Args:
            html: HTML content of the AD detail view.
            base_info: Optional base company info from search results.
            
        Returns:
            CompanyDetails with parsed information.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        details = CompanyDetails(
            name=base_info.get('name', '') if base_info else '',
            register_num=base_info.get('register_num', '') if base_info else '',
            court=base_info.get('court', '') if base_info else '',
            state=base_info.get('state', '') if base_info else '',
            status=base_info.get('status', '') if base_info else '',
        )
        
        content_div = soup.find('div', class_=re.compile(r'content|abdruck|register', re.I))
        if content_div is None:
            content_div = soup.find('body')
        
        if content_div:
            text = content_div.get_text()
            
            details.legal_form = cls._extract_legal_form(text)
            
            capital_match = cls.CAPITAL_PATTERN.search(text)
            if capital_match:
                details.capital = capital_match.group(1)
                if capital_match.group(2):
                    details.currency = capital_match.group(2).replace('€', 'EUR')
            
            purpose_match = re.search(
                r'Gegenstand(?:\s+des\s+Unternehmens)?[:\s]*(.+?)(?:Stammkapital|Grundkapital|Geschäftsführer|Vorstand|Vertretung|$)',
                text, re.IGNORECASE | re.DOTALL
            )
            if purpose_match:
                details.purpose = purpose_match.group(1).strip()
            
            details.representatives = cls._extract_representatives_from_text(text)
            details = cls._parse_si_tables(soup, details)
        
        return details
    
    @classmethod
    def parse_ut(cls, html: str, base_info: Optional[Company] = None) -> CompanyDetails:
        """Parses company owner information (UT - Unternehmensträger).
        
        The UT view focuses on ownership and shareholder information.
        
        Args:
            html: HTML content of the UT detail view.
            base_info: Optional base company info from search results.
            
        Returns:
            CompanyDetails with owner information.
        """
        soup = BeautifulSoup(html, 'html.parser')
        
        if base_info:
            details = CompanyDetails(
                name=base_info.name,
                register_num=base_info.register_num or '',
                court=base_info.court,
                state=base_info.state,
                status=base_info.status,
            )
        else:
            details = CompanyDetails(
                name='',
                register_num='',
                court='',
                state='',
                status='',
            )
        
        details = cls._parse_si_tables(soup, details)
        text = soup.get_text()
        details.owners = cls._extract_owners(text)
        details.representatives = cls._extract_representatives_from_text(text)
        
        return details
    
    @classmethod
    def _extract_representatives_from_text(cls, text: str) -> list[Representative]:
        """Extracts all representatives from free-form text."""
        representatives = []
        seen_names = set()
        
        patterns = [
            (r'Geschäftsführer(?:in)?[:\s]*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)', 
             'Geschäftsführer'),
            (r'Vorstand[:\s]*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)', 
             'Vorstand'),
            (r'Prokurist(?:in)?[:\s]*([A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß]+)+)', 
             'Prokurist'),
            (r'Persönlich\s+haftende[r]?\s+Gesellschafter(?:in)?[:\s]*([A-ZÄÖÜ][^\n,;]+)', 
             'Persönlich haftender Gesellschafter'),
        ]
        
        for pattern, role in patterns:
            for match in re.finditer(pattern, text):
                name = match.group(1).strip()
                name = re.sub(r'\s*\([^)]*\)\s*', '', name).strip()
                name = re.sub(r'\s+', ' ', name)
                
                if name and len(name) > 3 and name not in seen_names:
                    seen_names.add(name)
                    location = None
                    full_match = match.group(0)
                    loc_match = re.search(r'\(([^)]+)\)', full_match)
                    if loc_match:
                        location = loc_match.group(1)
                    
                    representatives.append(Representative(
                        name=name,
                        role=role,
                        location=location,
                    ))
        
        return representatives
    
    @classmethod
    def _extract_owners(cls, text: str) -> list[Owner]:
        """Extracts owner/shareholder information from text."""
        owners = []
        seen_names = set()
        
        owner_patterns = [
            (r'Gesellschafter[:\s]+([^,\n]+?)(?:[,\s]+(?:Anteil|Einlage)[:\s]*([0-9.,]+\s*(?:EUR|€|%)))?(?:\n|$|,)',
             'Gesellschafter'),
            (r'Kommanditist(?:in)?[:\s]+([^,\n]+?)(?:[,\s]+(?:Anteil|Einlage|Haftsumme)[:\s]*([0-9.,]+\s*(?:EUR|€|%)))?(?:\n|$|,)',
             'Kommanditist'),
            (r'Komplementär(?:in)?[:\s]+([^,\n]+)',
             'Komplementär'),
        ]
        
        for pattern, owner_type in owner_patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                name = match.group(1).strip()
                name = re.sub(r'\s+', ' ', name)
                share = None
                if len(match.groups()) > 1 and match.group(2):
                    share = match.group(2).strip()
                
                if name and len(name) > 2 and name not in seen_names:
                    seen_names.add(name)
                    owners.append(Owner(
                        name=name,
                        share=share,
                        owner_type=owner_type,
                    ))
        
        return owners


class ResultParser:
    """Parses HTML search results into structured company data."""
    
    @staticmethod
    def parse_search_results(html: str) -> list[Company]:
        """Extracts company records from search results HTML.
        
        Args:
            html: HTML content of the search results page.
            
        Returns:
            List of Company objects with company information.
        """
        soup = BeautifulSoup(html, 'html.parser')
        grid = soup.find('table', role='grid')
        
        results: list[Company] = []
        if grid is None:
            return results
            
        for row in grid.find_all('tr'):
            data_ri = row.get('data-ri')
            if data_ri is not None:
                company_data = ResultParser.parse_result_row(row)
                results.append(Company.model_validate(company_data))
                
        return results
    
    @staticmethod
    def parse_result_row(row: Tag) -> dict[str, Any]:
        """Parses a single search result row into a company dictionary.
        
        This returns a dict that can be validated into a Company model.
        Use parse_search_results() to get Company objects directly.
        
        Args:
            row: BeautifulSoup Tag representing a table row.
            
        Returns:
            Dictionary containing company information (ready for Company.model_validate).
            
        Raises:
            ParseError: If the result row has unexpected structure.
        """
        cells: list[str] = [cell.text.strip() for cell in row.find_all('td')]
        
        if len(cells) < 6:
            raise ParseError(
                f"Expected at least 6 cells in result row, got {len(cells)}",
                html_snippet=str(row)[:500]
            )
        
        court = cells[1]
        state = cells[3]
        status = cells[4].strip()
        
        # Extract register number
        register_num = ResultParser._extract_register_number(court, state)
        
        # Parse history entries
        history_tuples = ResultParser._parse_history(cells)
        history = [HistoryEntry(name=name, location=location) for name, location in history_tuples]
        
        return {
            'court': court,
            'register_num': register_num,
            'name': cells[2],
            'state': state,
            'status': status,
            'statusCurrent': status.upper().replace(' ', '_'),
            'documents': cells[5],
            'history': history
        }
    
    @staticmethod
    def _extract_register_number(court: str, state: str) -> Optional[str]:
        """Extracts and normalizes the register number from court string.
        
        Args:
            court: Court field containing the register number.
            state: State, used to add appropriate suffix.
            
        Returns:
            Normalized register number, or None if not found.
        """
        reg_match = re.search(r'(HRA|HRB|GnR|VR|PR)\s*\d+(\s+[A-Z])?(?!\w)', court)
        
        if not reg_match:
            return None
            
        register_num = reg_match.group(0)
        reg_type = register_num.split()[0]
        suffix = SUFFIX_MAP.get(state, {}).get(reg_type)
        if suffix and not register_num.endswith(suffix):
            register_num += suffix
            
        return register_num
    
    @staticmethod
    def _parse_history(cells: list[str]) -> list[tuple[str, str]]:
        """Parses history entries from cell data.
        
        Args:
            cells: List of cell text content.
            
        Returns:
            List of (name, location) tuples.
        """
        history: list[tuple[str, str]] = []
        hist_start = 8
        
        for i in range(hist_start, len(cells), 3):
            if i + 1 >= len(cells):
                break
            if "Branches" in cells[i] or "Niederlassungen" in cells[i]:
                break
            history.append((cells[i], cells[i + 1]))
            
        return history


# Backward-compatible function aliases
def parse_result(result: Tag) -> Company:
    """Parses a single search result row into a Company object.
    
    Deprecated: Use ResultParser.parse_result_row() and Company.model_validate() instead.
    """
    data = ResultParser.parse_result_row(result)
    return Company.model_validate(data)


def get_companies_in_searchresults(html: str) -> list[Company]:
    """Extracts company records from search results HTML.
    
    Deprecated: Use ResultParser.parse_search_results() instead.
    """
    return ResultParser.parse_search_results(html)

