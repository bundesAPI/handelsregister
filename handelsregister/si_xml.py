"""Parser for SI (Strukturierter Inhalt) XML from the Handelsregister.

The SI XML format is the machine-readable, structured version of register
content. Unlike the HTML views, this format is stable and well-defined.
"""

import logging
import re
import xml.etree.ElementTree as ET
from typing import ClassVar, Optional

from .models import Address, CompanyDetails, Owner, Representative

logger = logging.getLogger(__name__)


class SIXMLParser:
    """Parses SI XML content into CompanyDetails objects.

    The SI XML format contains structured register information including:
    - Company name and legal form
    - Registration details (court, number, date)
    - Share capital
    - Business address
    - Business purpose
    - Representatives (directors, board members)
    - Owners/shareholders

    Usage:
        parser = SIXMLParser()
        details = parser.parse(xml_content)
    """

    # Common namespace prefixes used in SI XML
    NAMESPACES: ClassVar[dict[str, str]] = {
        "xjustiz": "http://www.xjustiz.de",
        "hr": "http://www.handelsregister.de",
    }

    def parse(self, xml_content: str) -> CompanyDetails:
        """Parses SI XML content into a CompanyDetails object.

        Args:
            xml_content: Raw XML string from the SI endpoint.

        Returns:
            CompanyDetails with all parsed information.

        Raises:
            ValueError: If the XML is malformed or cannot be parsed.
        """
        try:
            # Handle potential BOM and whitespace
            xml_content = xml_content.strip()
            if xml_content.startswith("\ufeff"):
                xml_content = xml_content[1:]

            root = ET.fromstring(xml_content)
        except ET.ParseError as e:
            msg = f"Failed to parse SI XML: {e}"
            raise ValueError(msg) from e

        # Initialize with empty values
        details = CompanyDetails(
            name="",
            register_num="",
            court="",
            state="",
            status="",
        )

        # Parse different sections
        details = self._parse_company_info(root, details)
        details = self._parse_capital(root, details)
        details = self._parse_address(root, details)
        details = self._parse_purpose(root, details)
        details = self._parse_representatives(root, details)
        details = self._parse_owners(root, details)

        return self._parse_dates(root, details)

    def _parse_company_info(self, root: ET.Element, details: CompanyDetails) -> CompanyDetails:
        """Extracts basic company information from the XML."""
        # Try common element names for company name
        name_tags = ["Firma", "firma", "Name", "name", "Bezeichnung"]
        for tag in name_tags:
            elem = self._find_element(root, tag)
            if elem is not None and elem.text:
                details.name = elem.text.strip()
                break

        # Register number
        reg_tags = ["Registernummer", "registernummer", "Aktenzeichen", "RegNr"]
        for tag in reg_tags:
            elem = self._find_element(root, tag)
            if elem is not None and elem.text:
                details.register_num = elem.text.strip()
                break

        # Registration court
        court_tags = ["Registergericht", "registergericht", "Gericht", "Amtsgericht"]
        for tag in court_tags:
            elem = self._find_element(root, tag)
            if elem is not None and elem.text:
                details.court = elem.text.strip()
                break

        # Legal form
        form_tags = ["Rechtsform", "rechtsform", "LegalForm"]
        for tag in form_tags:
            elem = self._find_element(root, tag)
            if elem is not None and elem.text:
                details.legal_form = elem.text.strip()
                break

        # Status
        status_tags = ["Status", "status", "Eintragungsstatus"]
        for tag in status_tags:
            elem = self._find_element(root, tag)
            if elem is not None and elem.text:
                details.status = elem.text.strip()
                break

        return details

    def _parse_capital(self, root: ET.Element, details: CompanyDetails) -> CompanyDetails:
        """Extracts share capital information."""
        capital_tags = ["Stammkapital", "Grundkapital", "Kapital", "kapital"]
        for tag in capital_tags:
            elem = self._find_element(root, tag)
            if elem is not None:
                # Capital might be in text or child elements
                if elem.text and elem.text.strip():
                    capital_text = elem.text.strip()
                else:
                    # Check for Betrag/Waehrung children
                    betrag = elem.find("Betrag")
                    if betrag is None:
                        betrag = elem.find("betrag")
                    if betrag is not None and betrag.text:
                        capital_text = betrag.text.strip()
                    else:
                        capital_text = "".join(elem.itertext()).strip()

                # Parse amount and currency
                parsed = self._parse_capital_string(capital_text)
                if parsed:
                    details.capital = parsed[0]
                    details.currency = parsed[1]
                break

        return details

    def _parse_capital_string(self, text: str) -> Optional[tuple[str, str]]:
        """Parses a capital string into (amount, currency) tuple."""
        if not text:
            return None

        # Match patterns like "25.000,00 EUR" or "25000 EUR" or "25.000 Euro"
        pattern = r"([\d.,]+)\s*(EUR|Euro|DM)?"
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            amount = match.group(1).strip()
            currency = match.group(2) or "EUR"
            # Normalize currency to uppercase EUR
            currency = currency.upper().replace("EURO", "EUR")
            return (amount, currency)
        return None

    def _parse_address(self, root: ET.Element, details: CompanyDetails) -> CompanyDetails:
        """Extracts business address information."""
        addr_tags = ["Geschaeftsanschrift", "Anschrift", "Adresse", "Sitz"]
        for tag in addr_tags:
            elem = self._find_element(root, tag)
            if elem is not None:
                address = Address()

                # Street
                street_elem = self._find_child(elem, ["Strasse", "strasse", "Strassenname"])
                if street_elem is not None and street_elem.text:
                    address.street = street_elem.text.strip()

                # Postal code
                plz_elem = self._find_child(elem, ["PLZ", "Postleitzahl", "plz"])
                if plz_elem is not None and plz_elem.text:
                    address.postal_code = plz_elem.text.strip()

                # City
                city_elem = self._find_child(elem, ["Ort", "Stadt", "ort"])
                if city_elem is not None and city_elem.text:
                    address.city = city_elem.text.strip()

                # Country
                country_elem = self._find_child(elem, ["Land", "Staat"])
                if country_elem is not None and country_elem.text:
                    address.country = country_elem.text.strip()

                # If no structured address, try to parse from text
                if not address.city and elem.text:
                    address = self._parse_address_string(elem.text.strip())

                details.address = address
                break

        return details

    def _find_child(self, parent: ET.Element, tags: list[str]) -> Optional[ET.Element]:
        """Finds a child element by trying multiple tag names."""
        for tag in tags:
            elem = parent.find(tag)
            if elem is not None:
                return elem
        return None

    def _parse_address_string(self, text: str) -> Address:
        """Parses an address from a single string."""
        address = Address()

        # Try to find PLZ and city pattern like "10965 Berlin"
        plz_match = re.search(r"(\d{5})\s+(\S+.*?)(?:,|$)", text)
        if plz_match:
            address.postal_code = plz_match.group(1)
            address.city = plz_match.group(2).strip()
            # Street is whatever comes before the PLZ
            street_part = text[: plz_match.start()].strip().rstrip(",")
            if street_part:
                address.street = street_part
        else:
            # Just use the whole thing as city
            address.city = text

        return address

    def _parse_purpose(self, root: ET.Element, details: CompanyDetails) -> CompanyDetails:
        """Extracts business purpose."""
        purpose_tags = ["Gegenstand", "Unternehmensgegenstand", "Zweck", "gegenstand"]
        for tag in purpose_tags:
            elem = self._find_element(root, tag)
            if elem is not None:
                # Purpose might be in text or nested
                if elem.text and elem.text.strip():
                    details.purpose = elem.text.strip()
                else:
                    # Collect all text content
                    text = "".join(elem.itertext()).strip()
                    if text:
                        details.purpose = text
                break

        return details

    def _parse_representatives(self, root: ET.Element, details: CompanyDetails) -> CompanyDetails:
        """Extracts company representatives (Geschaeftsfuehrer, Vorstand, etc.)."""
        rep_containers = [
            "Vertretung",
            "Geschaeftsfuehrung",
            "Vorstand",
            "Prokura",
            "Vertreter",
        ]

        for container_tag in rep_containers:
            container = self._find_element(root, container_tag)
            if container is not None:
                # Look for individual person entries - only direct children
                person_tags = ["Person", "Vertreter", "Mitglied", "person"]
                found_persons = False
                for person_tag in person_tags:
                    for person in container.findall(person_tag):
                        rep = self._parse_person(person, container_tag)
                        if rep:
                            details.representatives.append(rep)
                            found_persons = True

                # If no structured persons, try to parse from text
                if not found_persons:
                    text = "".join(container.itertext()).strip()
                    reps = self._parse_representatives_text(text, container_tag)
                    details.representatives.extend(reps)

        return details

    def _parse_person(self, elem: ET.Element, role_hint: str) -> Optional[Representative]:
        """Parses a person element into a Representative."""
        name = None
        role = self._normalize_role(role_hint)
        location = None

        # Try to build name from Vorname + Name/Nachname
        vorname_elem = self._find_child(elem, ["Vorname", "vorname"])
        name_elem = self._find_child(elem, ["Name", "name", "Nachname", "Bezeichnung"])

        if name_elem is not None and name_elem.text:
            nachname = name_elem.text.strip()
            if vorname_elem is not None and vorname_elem.text:
                name = f"{vorname_elem.text.strip()} {nachname}"
            else:
                name = nachname
        elif elem.text and elem.text.strip():
            # Try to get name from element text
            name = elem.text.strip()

        if not name:
            return None

        # Location/city
        loc_elem = self._find_child(elem, ["Ort", "Wohnort", "ort"])
        if loc_elem is not None and loc_elem.text:
            location = loc_elem.text.strip()

        # Role override if specified
        role_elem = self._find_child(elem, ["Funktion", "Rolle", "rolle"])
        if role_elem is not None and role_elem.text:
            role = role_elem.text.strip()

        return Representative(name=name, role=role, location=location)

    def _normalize_role(self, role: str) -> str:
        """Normalizes role names to standard German terms."""
        role_map = {
            "Geschaeftsfuehrung": "Geschaeftsfuehrer",
            "Vorstand": "Vorstand",
            "Prokura": "Prokurist",
            "Vertretung": "Vertretungsberechtigter",
            "Vertreter": "Vertretungsberechtigter",
        }
        return role_map.get(role, role)

    def _parse_representatives_text(self, text: str, role_hint: str) -> list[Representative]:
        """Parses representatives from free-form text."""
        representatives = []
        role = self._normalize_role(role_hint)

        # Split on common delimiters
        parts = re.split(r"[;,\n]", text)
        for raw_part in parts:
            name_part = raw_part.strip()
            if not name_part or len(name_part) < 3:
                continue

            # Skip common non-name phrases
            skip_phrases = ["einzelvertretungsberechtigt", "mit der Befugnis", "befreit"]
            if any(phrase.lower() in name_part.lower() for phrase in skip_phrases):
                continue

            # Extract location if in parentheses
            location = None
            loc_match = re.search(r"\(([^)]+)\)", name_part)
            if loc_match:
                location = loc_match.group(1)
                name_part = name_part[: loc_match.start()].strip()

            if name_part:
                representatives.append(Representative(name=name_part, role=role, location=location))

        return representatives

    def _parse_owners(self, root: ET.Element, details: CompanyDetails) -> CompanyDetails:
        """Extracts owner/shareholder information."""
        owner_containers = ["Gesellschafter", "Kommanditisten", "Inhaber", "Eigentuemer"]

        for container_tag in owner_containers:
            container = self._find_element(root, container_tag)
            if container is not None:
                # Look for Person elements as direct children
                person_tags = ["Person", "Gesellschafter", "Kommanditist"]
                for person_tag in person_tags:
                    for person in container.findall(person_tag):
                        owner = self._parse_owner(person, container_tag)
                        if owner:
                            details.owners.append(owner)

        return details

    def _parse_owner(self, elem: ET.Element, type_hint: str) -> Optional[Owner]:
        """Parses an owner element."""
        name = None
        share = None
        owner_type = type_hint

        # Try to build name from Vorname + Name
        vorname_elem = self._find_child(elem, ["Vorname", "vorname"])
        name_elem = self._find_child(elem, ["Name", "name", "Firma"])

        if name_elem is not None and name_elem.text:
            nachname = name_elem.text.strip()
            if vorname_elem is not None and vorname_elem.text:
                name = f"{vorname_elem.text.strip()} {nachname}"
            else:
                name = nachname
        elif elem.text and elem.text.strip():
            name = elem.text.strip()

        if not name:
            return None

        # Share/Einlage
        share_elem = self._find_child(elem, ["Anteil", "Einlage", "Haftsumme"])
        if share_elem is not None and share_elem.text:
            share = share_elem.text.strip()

        return Owner(name=name, share=share, owner_type=owner_type)

    def _parse_dates(self, root: ET.Element, details: CompanyDetails) -> CompanyDetails:
        """Extracts registration and update dates."""
        # Registration date
        reg_date_tags = ["Eintragungsdatum", "Registerdatum", "ErsteEintragung"]
        for tag in reg_date_tags:
            elem = self._find_element(root, tag)
            if elem is not None and elem.text:
                details.registration_date = elem.text.strip()
                break

        # Last update
        update_tags = ["Aenderungsdatum", "LetzteAenderung", "Aktualisierung"]
        for tag in update_tags:
            elem = self._find_element(root, tag)
            if elem is not None and elem.text:
                details.last_update = elem.text.strip()
                break

        # Deletion date
        del_tags = ["Loeschungsdatum", "Loeschung"]
        for tag in del_tags:
            elem = self._find_element(root, tag)
            if elem is not None and elem.text:
                details.deletion_date = elem.text.strip()
                break

        return details

    def _find_element(self, root: ET.Element, tag: str) -> Optional[ET.Element]:
        """Finds an element by tag name, handling namespaces."""
        # Try direct match
        elem = root.find(f".//{tag}")
        if elem is not None:
            return elem

        # Try with common namespace prefixes
        for _prefix, ns in self.NAMESPACES.items():
            elem = root.find(f".//{{{ns}}}{tag}")
            if elem is not None:
                return elem

        # Try case-insensitive search
        for elem in root.iter():
            if elem.tag.lower() == tag.lower():
                return elem
            # Handle namespaced tags
            if "}" in elem.tag:
                local_name = elem.tag.split("}")[1]
                if local_name.lower() == tag.lower():
                    return elem

        return None


def parse_si_xml(xml_content: str) -> CompanyDetails:
    """Convenience function to parse SI XML.

    Args:
        xml_content: Raw XML string from the SI endpoint.

    Returns:
        CompanyDetails with parsed information.
    """
    parser = SIXMLParser()
    return parser.parse(xml_content)
