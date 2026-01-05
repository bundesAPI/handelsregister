"""Tests for the SI XML parser."""

from pathlib import Path

import pytest

from handelsregister.si_xml import SIXMLParser, parse_si_xml

FIXTURES_DIR = Path(__file__).parent / "fixtures" / "si_xml"


class TestSIXMLParser:
    """Tests for SIXMLParser class."""

    @pytest.fixture
    def parser(self):
        return SIXMLParser()

    def test_parse_gmbh_basic(self, parser):
        """Test parsing a basic GmbH company."""
        xml = (FIXTURES_DIR / "gmbh_basic.xml").read_text()
        details = parser.parse(xml)

        assert details.name == "Test GmbH"
        assert details.legal_form == "Gesellschaft mit beschraenkter Haftung"
        assert details.register_num == "HRB 12345 B"
        assert details.court == "Amtsgericht Berlin (Charlottenburg)"
        assert details.status == "aktuell eingetragen"

    def test_parse_gmbh_capital(self, parser):
        """Test parsing capital information."""
        xml = (FIXTURES_DIR / "gmbh_basic.xml").read_text()
        details = parser.parse(xml)

        assert details.capital == "25000,00"
        assert details.currency == "EUR"

    def test_parse_gmbh_address(self, parser):
        """Test parsing address information."""
        xml = (FIXTURES_DIR / "gmbh_basic.xml").read_text()
        details = parser.parse(xml)

        assert details.address is not None
        assert details.address.street == "Musterstrasse 123"
        assert details.address.postal_code == "10115"
        assert details.address.city == "Berlin"
        assert details.address.country == "Deutschland"

    def test_parse_gmbh_purpose(self, parser):
        """Test parsing business purpose."""
        xml = (FIXTURES_DIR / "gmbh_basic.xml").read_text()
        details = parser.parse(xml)

        assert details.purpose == "Entwicklung und Vertrieb von Software"

    def test_parse_gmbh_representatives(self, parser):
        """Test parsing representatives."""
        xml = (FIXTURES_DIR / "gmbh_basic.xml").read_text()
        details = parser.parse(xml)

        assert len(details.representatives) == 1
        rep = details.representatives[0]
        assert rep.name == "Max Mustermann"
        assert rep.role == "Geschaeftsfuehrer"
        assert rep.location == "Berlin"

    def test_parse_gmbh_owners(self, parser):
        """Test parsing owners."""
        xml = (FIXTURES_DIR / "gmbh_basic.xml").read_text()
        details = parser.parse(xml)

        assert len(details.owners) == 1
        owner = details.owners[0]
        assert owner.name == "Holding GmbH"
        assert owner.share == "100%"

    def test_parse_gmbh_dates(self, parser):
        """Test parsing dates."""
        xml = (FIXTURES_DIR / "gmbh_basic.xml").read_text()
        details = parser.parse(xml)

        assert details.registration_date == "15.03.2020"

    def test_parse_ag_large(self, parser):
        """Test parsing a large AG company."""
        xml = (FIXTURES_DIR / "ag_large.xml").read_text()
        details = parser.parse(xml)

        assert details.name == "GASAG AG"
        assert details.legal_form == "Aktiengesellschaft"
        assert details.register_num == "HRB 44343 B"

    def test_parse_ag_capital_inline(self, parser):
        """Test parsing inline capital format."""
        xml = (FIXTURES_DIR / "ag_large.xml").read_text()
        details = parser.parse(xml)

        assert "307200000" in details.capital
        assert details.currency == "EUR"

    def test_parse_ag_multiple_representatives(self, parser):
        """Test parsing multiple board members."""
        xml = (FIXTURES_DIR / "ag_large.xml").read_text()
        details = parser.parse(xml)

        assert len(details.representatives) == 2
        names = [r.name for r in details.representatives]
        assert "Georg Friedrichs" in names
        assert "Stefan Krampitz" in names

    def test_parse_ag_update_date(self, parser):
        """Test parsing update date."""
        xml = (FIXTURES_DIR / "ag_large.xml").read_text()
        details = parser.parse(xml)

        assert details.last_update == "15.06.2024"

    def test_parse_gmbh_co_kg(self, parser):
        """Test parsing GmbH & Co. KG company."""
        xml = (FIXTURES_DIR / "gmbh_co_kg.xml").read_text()
        details = parser.parse(xml)

        assert details.name == "Muster GmbH und Co. KG"
        assert "KG" in details.legal_form
        assert details.register_num == "HRA 98765"

    def test_parse_gmbh_co_kg_kommanditisten(self, parser):
        """Test parsing Kommanditisten as owners."""
        xml = (FIXTURES_DIR / "gmbh_co_kg.xml").read_text()
        details = parser.parse(xml)

        assert len(details.owners) == 2
        names = [o.name for o in details.owners]
        assert "Hans Muster" in names
        assert "Anna Muster" in names

    def test_parse_minimal(self, parser):
        """Test parsing minimal XML with only required fields."""
        xml = (FIXTURES_DIR / "minimal.xml").read_text()
        details = parser.parse(xml)

        assert details.name == "Minimal e.K."
        assert details.register_num == "HRA 1234"
        assert details.court == "Amtsgericht Hamburg"
        # Optional fields should be None or empty
        assert details.capital is None
        assert details.address is None
        assert len(details.representatives) == 0

    def test_parse_empty_xml_raises(self, parser):
        """Test that empty XML raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse"):
            parser.parse("")

    def test_parse_invalid_xml_raises(self, parser):
        """Test that invalid XML raises ValueError."""
        with pytest.raises(ValueError, match="Failed to parse"):
            parser.parse("<not valid xml")

    def test_parse_bom_handling(self, parser):
        """Test that BOM at start of XML is handled."""
        xml = "\ufeff" + (FIXTURES_DIR / "minimal.xml").read_text()
        details = parser.parse(xml)
        assert details.name == "Minimal e.K."


class TestParseSiXmlFunction:
    """Tests for the convenience parse_si_xml function."""

    def test_parse_si_xml_function(self):
        """Test that the convenience function works."""
        xml = (FIXTURES_DIR / "gmbh_basic.xml").read_text()
        details = parse_si_xml(xml)

        assert details.name == "Test GmbH"
        assert details.register_num == "HRB 12345 B"


class TestCapitalParsing:
    """Tests for capital string parsing."""

    @pytest.fixture
    def parser(self):
        return SIXMLParser()

    def test_parse_capital_with_comma(self, parser):
        result = parser._parse_capital_string("25.000,00 EUR")
        assert result == ("25.000,00", "EUR")

    def test_parse_capital_without_currency(self, parser):
        result = parser._parse_capital_string("50000")
        assert result == ("50000", "EUR")

    def test_parse_capital_with_euro_symbol(self, parser):
        result = parser._parse_capital_string("100.000 Euro")
        assert result == ("100.000", "EUR")

    def test_parse_capital_empty(self, parser):
        result = parser._parse_capital_string("")
        assert result is None


class TestAddressParsing:
    """Tests for address string parsing."""

    @pytest.fixture
    def parser(self):
        return SIXMLParser()

    def test_parse_address_full(self, parser):
        result = parser._parse_address_string("Musterstrasse 1, 10115 Berlin")
        assert result.street == "Musterstrasse 1"
        assert result.postal_code == "10115"
        assert result.city == "Berlin"

    def test_parse_address_city_only(self, parser):
        result = parser._parse_address_string("Hamburg")
        assert result.city == "Hamburg"
        assert result.street is None
