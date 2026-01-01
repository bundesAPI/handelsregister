"""Tests for the handelsregister module.

Unit tests run without network access and use mocked responses.
Integration tests hit the live API and are marked with @pytest.mark.integration.
"""

import argparse
import json
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from handelsregister import (
    Address,
    CacheEntry,
    Company,
    CompanyDetails,
    DetailsParser,
    HandelsRegister,
    HistoryEntry,
    Owner,
    ParseError,
    Representative,
    ResultParser,
    SearchCache,
    SearchOptions,
    get_companies_in_searchresults,
    get_details,
    parse_result,
    search,
    SUFFIX_MAP,
    STATE_CODES,
    REGISTER_TYPES,
    DEFAULT_CACHE_TTL_SECONDS,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_search_html():
    """Sample HTML response from a search result."""
    return '<html><body><table role="grid"><thead></thead><tbody id="ergebnissForm:selectedSuchErgebnisFormTable_data" class="ui-datatable-data ui-widget-content"><tr data-ri="0" class="ui-widget-content ui-datatable-even" role="row"><td role="gridcell" colspan="9" class="borderBottom3"><table id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt147" class="ui-panelgrid ui-widget" role="grid"><tbody><tr class="ui-widget-content ui-panelgrid-even borderBottom1" role="row"><td role="gridcell" class="ui-panelgrid-cell fontTableNameSize" colspan="5">Berlin  <span class="fontWeightBold"> District court Berlin (Charlottenburg) HRB 44343  </span></td></tr><tr class="ui-widget-content ui-panelgrid-odd" role="row"><td role="gridcell" class="ui-panelgrid-cell paddingBottom20Px" colspan="5"><span class="marginLeft20">GASAG AG</span></td><td role="gridcell" class="ui-panelgrid-cell sitzSuchErgebnisse"><span class="verticalText ">Berlin</span></td><td role="gridcell" class="ui-panelgrid-cell" style="text-align: center;padding-bottom: 20px;"><span class="verticalText">currently registered</span></td><td role="gridcell" class="ui-panelgrid-cell textAlignLeft paddingBottom20Px" colspan="2"><div id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt160" class="ui-outputpanel ui-widget linksPanel"><script type="text/javascript" src="/rp_web/javax.faces.resource/jsf.js.xhtml?ln=javax.faces"></script><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:0:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:0:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:0:popupLink" class="underlinedText">AD</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:1:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:1:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:1:popupLink" class="underlinedText">CD</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:2:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:2:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:2:popupLink" class="underlinedText">HD</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:3:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:3:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:3:popupLink" class="underlinedText">DK</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:4:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:4:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:4:popupLink" class="underlinedText">UT</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:5:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:5:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:5:popupLink" class="underlinedText">VÖ</span></a><a id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:6:fade" href="#" class="dokumentList" aria-describedby="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:6:toolTipFade"><span id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt161:6:popupLink" class="underlinedText">SI</span></a></div></td></tr><tr class="ui-widget-content ui-panelgrid-even" role="row"><td role="gridcell" class="ui-panelgrid-cell" colspan="7"><table id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt172" class="ui-panelgrid ui-widget marginLeft20" role="grid"><tbody><tr class="ui-widget-content ui-panelgrid-even borderBottom1 RegPortErg_Klein" role="row"><td role="gridcell" class="ui-panelgrid-cell padding0Px">History</td></tr></tbody></table><table id="ergebnissForm:selectedSuchErgebnisFormTable:0:j_idt176" class="ui-panelgrid ui-widget" role="grid"><tbody><tr class="ui-widget-content" role="row"><td role="gridcell" class="ui-panelgrid-cell RegPortErg_HistorieZn marginLeft20 padding0Px" colspan="5"><span class="marginLeft20 fontSize85">1.) Gasag Berliner Gaswerke Aktiengesellschaft</span></td><td role="gridcell" class="ui-panelgrid-cell RegPortErg_SitzStatus "><span class="fontSize85">1.) Berlin</span></td><td role="gridcell" class="ui-panelgrid-cell textAlignCenter"></td></tr></tbody></table></td></tr></tbody></table></td></tr></tbody></table></body></html>'


@pytest.fixture
def mock_args():
    """Create mock arguments for HandelsRegister."""
    return argparse.Namespace(
        debug=False,
        force=False,
        schlagwoerter='Test Company',
        schlagwortOptionen='all',
        json=False
    )


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create a temporary cache directory."""
    cache_dir = tmp_path / "handelsregister_cache"
    cache_dir.mkdir()
    return cache_dir


# =============================================================================
# Unit Tests - Parsing
# =============================================================================

class TestParseSearchResults:
    """Unit tests for HTML parsing functions."""

    def test_parse_search_result_gasag(self, sample_search_html):
        """Test parsing a search result for GASAG AG."""
        result = get_companies_in_searchresults(sample_search_html)
        
        assert len(result) == 1
        company = result[0]
        
        assert company['name'] == 'GASAG AG'
        assert company['state'] == 'Berlin'
        assert company['register_num'] == 'HRB 44343 B'
        assert company['status'] == 'currently registered'
        assert company['statusCurrent'] == 'CURRENTLY_REGISTERED'
        assert len(company['history']) == 1
        assert company['history'][0] == ('1.) Gasag Berliner Gaswerke Aktiengesellschaft', '1.) Berlin')

    def test_parse_empty_html(self):
        """Test parsing empty HTML returns empty list."""
        result = get_companies_in_searchresults('<html><body></body></html>')
        assert result == []

    def test_parse_no_grid_table(self):
        """Test parsing HTML without grid table returns empty list."""
        html = '<html><body><table><tr><td>No grid</td></tr></table></body></html>'
        result = get_companies_in_searchresults(html)
        assert result == []


class TestDetailsParser:
    """Unit tests for DetailsParser (SI/AD/UT parsing)."""
    
    @pytest.fixture
    def sample_si_html(self):
        """Sample HTML from structured register content (SI)."""
        return '''
        <html>
        <body>
        <table>
            <tr><td>Firma:</td><td>GASAG AG</td></tr>
            <tr><td>Rechtsform:</td><td>Aktiengesellschaft</td></tr>
            <tr><td>Sitz:</td><td>Berlin</td></tr>
            <tr><td>Geschäftsanschrift:</td><td>GASAG-Platz 1, 10965 Berlin</td></tr>
            <tr><td>Stammkapital:</td><td>307.200.000,00 EUR</td></tr>
            <tr><td>Gegenstand:</td><td>Versorgung der Bevölkerung mit Gas und anderen Energien</td></tr>
            <tr><td>Registernummer:</td><td>HRB 44343 B</td></tr>
        </table>
        <div>Vorstand: Dr. Gerhard Holtmeier (Berlin)</div>
        </body>
        </html>
        '''
    
    @pytest.fixture
    def sample_si_gmbh_html(self):
        """Sample HTML for a GmbH."""
        return '''
        <html>
        <body>
        <table>
            <tr><td>Firma:</td><td>Test GmbH</td></tr>
            <tr><td>Rechtsform:</td><td>Gesellschaft mit beschränkter Haftung</td></tr>
            <tr><td>Stammkapital:</td><td>25.000 EUR</td></tr>
        </table>
        <p>Geschäftsführer: Max Mustermann</p>
        </body>
        </html>
        '''
    
    def test_parse_si_basic(self, sample_si_html):
        """Test parsing basic SI content."""
        details = DetailsParser.parse_si(sample_si_html)
        
        assert details.name == "GASAG AG"
        assert details.legal_form == "Aktiengesellschaft"
        assert "307.200.000" in details.capital
        assert details.currency == "EUR"
    
    def test_parse_si_with_base_info(self, sample_si_html):
        """Test parsing SI with base company info."""
        base_info = {
            'name': 'GASAG AG',
            'register_num': 'HRB 44343 B',
            'court': 'Amtsgericht Berlin',
            'state': 'Berlin',
            'status': 'aktuell',
        }
        details = DetailsParser.parse_si(sample_si_html, base_info)
        
        assert details.court == "Amtsgericht Berlin"
        assert details.state == "Berlin"
        assert details.status == "aktuell"
    
    def test_parse_si_address(self, sample_si_html):
        """Test parsing address from SI."""
        details = DetailsParser.parse_si(sample_si_html)
        
        assert details.address is not None
        assert details.address.street == "GASAG-Platz 1"
        assert details.address.postal_code == "10965"
        assert details.address.city == "Berlin"
    
    def test_parse_si_purpose(self, sample_si_html):
        """Test parsing company purpose from SI."""
        details = DetailsParser.parse_si(sample_si_html)
        
        assert details.purpose is not None
        assert "Versorgung" in details.purpose
        assert "Gas" in details.purpose
    
    def test_parse_si_representatives(self, sample_si_html):
        """Test parsing representatives from SI."""
        details = DetailsParser.parse_si(sample_si_html)
        
        assert len(details.representatives) >= 1
        vorstand = next((r for r in details.representatives if r.role == "Vorstand"), None)
        assert vorstand is not None
        assert "Holtmeier" in vorstand.name
    
    def test_parse_si_gmbh(self, sample_si_gmbh_html):
        """Test parsing GmbH company."""
        details = DetailsParser.parse_si(sample_si_gmbh_html)
        
        assert details.name == "Test GmbH"
        assert details.legal_form == "Gesellschaft mit beschränkter Haftung"
        assert "25.000" in details.capital
        assert details.currency == "EUR"
    
    def test_parse_si_gmbh_geschaeftsfuehrer(self, sample_si_gmbh_html):
        """Test parsing Geschäftsführer from GmbH."""
        details = DetailsParser.parse_si(sample_si_gmbh_html)
        
        gf = next((r for r in details.representatives if r.role == "Geschäftsführer"), None)
        assert gf is not None
        assert "Mustermann" in gf.name
    
    def test_parse_address_full(self):
        """Test _parse_address with full address."""
        addr = DetailsParser._parse_address("Musterstraße 123, 10115 Berlin")
        
        assert addr.street == "Musterstraße 123"
        assert addr.postal_code == "10115"
        assert addr.city == "Berlin"
    
    def test_parse_address_city_only(self):
        """Test _parse_address with city only."""
        addr = DetailsParser._parse_address("Hamburg")
        
        assert addr.city == "Hamburg"
        assert addr.street is None
        assert addr.postal_code is None
    
    def test_extract_legal_form_ag(self):
        """Test extracting Aktiengesellschaft."""
        result = DetailsParser._extract_legal_form("Eine Aktiengesellschaft")
        assert result == "Aktiengesellschaft"
    
    def test_extract_legal_form_gmbh(self):
        """Test extracting GmbH."""
        result = DetailsParser._extract_legal_form("Test GmbH")
        assert result == "Gesellschaft mit beschränkter Haftung"
    
    def test_extract_legal_form_kg(self):
        """Test extracting Kommanditgesellschaft."""
        result = DetailsParser._extract_legal_form("Muster GmbH & Co. KG")
        assert result == "GmbH & Co. KG"
    
    def test_extract_legal_form_none(self):
        """Test no legal form found."""
        result = DetailsParser._extract_legal_form("Some random text")
        assert result is None
    
    def test_parse_empty_html(self):
        """Test parsing empty HTML."""
        details = DetailsParser.parse_si("<html><body></body></html>")
        
        assert details.name == ""
        assert details.capital is None
        assert details.representatives == []


# =============================================================================
# Unit Tests - Data Classes
# =============================================================================

class TestDataClasses:
    """Unit tests for dataclass functionality."""

    def test_history_entry_creation(self):
        """Test creating a HistoryEntry."""
        entry = HistoryEntry(name="Old Name", location="Old Location")
        assert entry.name == "Old Name"
        assert entry.location == "Old Location"

    def test_company_to_dict(self):
        """Test Company.to_dict() method."""
        company = Company(
            court="Test Court",
            name="Test Company",
            state="Berlin",
            status="active",
            status_normalized="ACTIVE",
            documents="AD",
            register_num="HRB 12345",
            history=[HistoryEntry(name="Old", location="Berlin")]
        )
        
        d = company.to_dict()
        
        assert d['court'] == "Test Court"
        assert d['name'] == "Test Company"
        assert d['state'] == "Berlin"
        assert d['register_num'] == "HRB 12345"
        assert d['statusCurrent'] == "ACTIVE"
        assert d['history'] == [("Old", "Berlin")]

    def test_cache_entry_not_expired(self):
        """Test CacheEntry.is_expired() returns False for fresh entry."""
        entry = CacheEntry(
            query="test",
            options="all",
            timestamp=time.time(),
            html="<html></html>"
        )
        assert not entry.is_expired()

    def test_cache_entry_expired(self):
        """Test CacheEntry.is_expired() returns True for old entry."""
        entry = CacheEntry(
            query="test",
            options="all",
            timestamp=time.time() - DEFAULT_CACHE_TTL_SECONDS - 1,
            html="<html></html>"
        )
        assert entry.is_expired()

    def test_cache_entry_serialization(self):
        """Test CacheEntry to_dict and from_dict."""
        original = CacheEntry(
            query="test query",
            options="exact",
            timestamp=1234567890.0,
            html="<html>test</html>"
        )
        
        serialized = original.to_dict()
        restored = CacheEntry.from_dict(serialized)
        
        assert restored.query == original.query
        assert restored.options == original.options
        assert restored.timestamp == original.timestamp
        assert restored.html == original.html

    def test_search_options_cache_key(self):
        """Test SearchOptions.cache_key() generates unique keys."""
        opts1 = SearchOptions(keywords="test", keyword_option="all")
        opts2 = SearchOptions(keywords="test", keyword_option="all")
        opts3 = SearchOptions(keywords="test", keyword_option="exact")
        opts4 = SearchOptions(keywords="test", keyword_option="all", states=["BE"])
        
        assert opts1.cache_key() == opts2.cache_key()
        assert opts1.cache_key() != opts3.cache_key()
        assert opts1.cache_key() != opts4.cache_key()

    def test_search_options_defaults(self):
        """Test SearchOptions default values."""
        opts = SearchOptions(keywords="test")
        
        assert opts.keyword_option == "all"
        assert opts.states is None
        assert opts.register_type is None
        assert opts.register_number is None
        assert opts.include_deleted is False
        assert opts.similar_sounding is False
        assert opts.results_per_page == 100


class TestAddress:
    """Unit tests for Address dataclass."""
    
    def test_address_str_full(self):
        """Test Address.__str__() with all fields."""
        addr = Address(
            street="Musterstraße 123",
            postal_code="10115",
            city="Berlin",
            country="Deutschland"
        )
        assert str(addr) == "Musterstraße 123, 10115 Berlin"
    
    def test_address_str_minimal(self):
        """Test Address.__str__() with minimal fields."""
        addr = Address(city="Hamburg")
        assert str(addr) == "Hamburg"
    
    def test_address_str_empty(self):
        """Test Address.__str__() with no fields."""
        addr = Address()
        assert str(addr) == ""
    
    def test_address_str_foreign(self):
        """Test Address.__str__() with foreign country."""
        addr = Address(city="Wien", country="Österreich")
        assert str(addr) == "Wien, Österreich"
    
    def test_address_to_dict(self):
        """Test Address.to_dict()."""
        addr = Address(street="Test 1", postal_code="12345", city="Berlin")
        d = addr.to_dict()
        assert d['street'] == "Test 1"
        assert d['postal_code'] == "12345"
        assert d['city'] == "Berlin"
        assert d['country'] == "Deutschland"


class TestRepresentative:
    """Unit tests for Representative dataclass."""
    
    def test_representative_creation(self):
        """Test creating a Representative."""
        rep = Representative(
            name="Max Mustermann",
            role="Geschäftsführer",
            location="Berlin",
            restrictions="einzelvertretungsberechtigt"
        )
        assert rep.name == "Max Mustermann"
        assert rep.role == "Geschäftsführer"
        assert rep.location == "Berlin"
        assert rep.restrictions == "einzelvertretungsberechtigt"
    
    def test_representative_to_dict(self):
        """Test Representative.to_dict()."""
        rep = Representative(name="Test", role="Vorstand")
        d = rep.to_dict()
        assert d['name'] == "Test"
        assert d['role'] == "Vorstand"
        assert d['location'] is None


class TestOwner:
    """Unit tests for Owner dataclass."""
    
    def test_owner_creation(self):
        """Test creating an Owner."""
        owner = Owner(
            name="Holding GmbH",
            share="100%",
            owner_type="Gesellschafter",
            location="München"
        )
        assert owner.name == "Holding GmbH"
        assert owner.share == "100%"
        assert owner.owner_type == "Gesellschafter"
    
    def test_owner_to_dict(self):
        """Test Owner.to_dict()."""
        owner = Owner(name="Test GmbH", share="50.000 EUR")
        d = owner.to_dict()
        assert d['name'] == "Test GmbH"
        assert d['share'] == "50.000 EUR"


class TestCompanyDetails:
    """Unit tests for CompanyDetails dataclass."""
    
    def test_company_details_creation(self):
        """Test creating CompanyDetails with all fields."""
        details = CompanyDetails(
            name="GASAG AG",
            register_num="HRB 44343 B",
            court="Amtsgericht Berlin (Charlottenburg)",
            state="Berlin",
            status="aktuell",
            legal_form="Aktiengesellschaft",
            capital="307.200.000",
            currency="EUR",
            address=Address(street="GASAG-Platz 1", postal_code="10965", city="Berlin"),
            purpose="Versorgung mit Energie",
            representatives=[
                Representative(name="Dr. Gerhard Holtmeier", role="Vorstand")
            ],
        )
        assert details.name == "GASAG AG"
        assert details.legal_form == "Aktiengesellschaft"
        assert details.capital == "307.200.000"
        assert len(details.representatives) == 1
    
    def test_company_details_to_dict(self):
        """Test CompanyDetails.to_dict()."""
        details = CompanyDetails(
            name="Test GmbH",
            register_num="HRB 12345",
            court="Amtsgericht Berlin",
            state="Berlin",
            status="aktuell",
            legal_form="GmbH",
            capital="25.000",
            currency="EUR",
        )
        d = details.to_dict()
        assert d['name'] == "Test GmbH"
        assert d['legal_form'] == "GmbH"
        assert d['capital'] == "25.000"
        assert d['representatives'] == []
        assert d['owners'] == []
    
    def test_company_details_from_company(self):
        """Test CompanyDetails.from_company() class method."""
        company = {
            'name': 'GASAG AG',
            'register_num': 'HRB 44343 B',
            'court': 'Berlin Amtsgericht',
            'state': 'Berlin',
            'status': 'aktuell',
        }
        details = CompanyDetails.from_company(company)
        assert details.name == "GASAG AG"
        assert details.register_num == "HRB 44343 B"
        assert details.legal_form is None  # Not set from basic company
    
    def test_company_details_defaults(self):
        """Test CompanyDetails default values."""
        details = CompanyDetails(
            name="Test",
            register_num="HRB 1",
            court="AG Berlin",
            state="Berlin",
            status="aktuell",
        )
        assert details.legal_form is None
        assert details.capital is None
        assert details.address is None
        assert details.representatives == []
        assert details.owners == []


# =============================================================================
# Unit Tests - Configuration
# =============================================================================

class TestConfiguration:
    """Unit tests for configuration constants."""

    def test_state_codes_complete(self):
        """Test that all 16 German states are defined."""
        assert len(STATE_CODES) == 16
        assert 'BE' in STATE_CODES  # Berlin
        assert 'BY' in STATE_CODES  # Bayern
        assert 'NW' in STATE_CODES  # Nordrhein-Westfalen

    def test_register_types(self):
        """Test that all register types are defined."""
        assert 'HRA' in REGISTER_TYPES
        assert 'HRB' in REGISTER_TYPES
        assert 'GnR' in REGISTER_TYPES
        assert 'VR' in REGISTER_TYPES
        assert 'PR' in REGISTER_TYPES


# =============================================================================
# Unit Tests - Cache
# =============================================================================

class TestCache:
    """Unit tests for caching functionality."""

    def test_cache_key_generation(self, temp_cache_dir):
        """Test that cache keys are deterministic."""
        cache = SearchCache(cache_dir=temp_cache_dir)
        
        key1 = cache._get_cache_key("Test", "all")
        key2 = cache._get_cache_key("Test", "all")
        key3 = cache._get_cache_key("Test", "exact")
        
        assert key1 == key2  # Same inputs = same key
        assert key1 != key3  # Different options = different key

    def test_cache_key_is_hash(self, temp_cache_dir):
        """Test that cache keys are valid hex hashes."""
        cache = SearchCache(cache_dir=temp_cache_dir)
        
        key = cache._get_cache_key("Company with spaces / special chars!", "all")
        
        # Should be a 64-character hex string (SHA-256)
        assert len(key) == 64
        assert all(c in '0123456789abcdef' for c in key)
    
    def test_cache_get_set(self, temp_cache_dir):
        """Test cache get/set operations."""
        cache = SearchCache(cache_dir=temp_cache_dir)
        
        # Initially empty
        assert cache.get("test", "all") is None
        
        # Set value
        cache.set("test", "all", "<html>cached</html>")
        
        # Get returns the value
        assert cache.get("test", "all") == "<html>cached</html>"
    
    def test_cache_ttl_expiration(self, temp_cache_dir):
        """Test that expired cache entries are not returned."""
        cache = SearchCache(cache_dir=temp_cache_dir, ttl_seconds=0)
        
        cache.set("test", "all", "<html>cached</html>")
        time.sleep(0.1)  # Wait for expiration
        
        # Expired entry should return None
        assert cache.get("test", "all") is None
    
    def test_cache_details_ttl(self, temp_cache_dir):
        """Test that details cache uses longer TTL."""
        cache = SearchCache(
            cache_dir=temp_cache_dir, 
            ttl_seconds=0,  # Search TTL expired
            details_ttl_seconds=3600,  # Details TTL not expired
        )
        
        # Set a details cache entry
        cache.set("details:SI:HRB123", "", "<html>details</html>")
        time.sleep(0.1)
        
        # Details should still be available (longer TTL)
        assert cache.get("details:SI:HRB123", "") == "<html>details</html>"
        
        # But search cache would be expired
        cache.set("search", "all", "<html>search</html>")
        time.sleep(0.1)
        assert cache.get("search", "all") is None
    
    def test_cache_clear(self, temp_cache_dir):
        """Test clearing the cache."""
        cache = SearchCache(cache_dir=temp_cache_dir)
        
        # Add some entries
        cache.set("search1", "all", "<html>1</html>")
        cache.set("search2", "all", "<html>2</html>")
        cache.set("details:SI:HRB1", "", "<html>d1</html>")
        
        # Clear all
        count = cache.clear()
        assert count == 3
        
        # Verify all cleared
        assert cache.get("search1", "all") is None
        assert cache.get("details:SI:HRB1", "") is None
    
    def test_cache_clear_details_only(self, temp_cache_dir):
        """Test clearing only details cache."""
        cache = SearchCache(cache_dir=temp_cache_dir)
        
        # Add entries
        cache.set("search1", "all", "<html>search</html>")
        cache.set("details:SI:HRB1", "", "<html>details</html>")
        
        # Clear details only
        count = cache.clear(details_only=True)
        assert count == 1
        
        # Search should still exist, details should be gone
        assert cache.get("search1", "all") == "<html>search</html>"
        assert cache.get("details:SI:HRB1", "") is None
    
    def test_cache_stats(self, temp_cache_dir):
        """Test cache statistics."""
        cache = SearchCache(cache_dir=temp_cache_dir)
        
        # Add entries
        cache.set("search1", "all", "<html>search</html>")
        cache.set("details:SI:HRB1", "", "<html>details</html>")
        cache.set("details:AD:HRB2", "", "<html>details2</html>")
        
        stats = cache.get_stats()
        
        assert stats['total_files'] == 3
        assert stats['search_files'] == 1
        assert stats['details_files'] == 2
        assert stats['total_size_bytes'] > 0


# =============================================================================
# Unit Tests - Suffix Map
# =============================================================================

class TestSuffixMap:
    """Unit tests for register number suffix handling."""

    def test_berlin_suffix(self):
        """Test Berlin HRB suffix mapping."""
        assert SUFFIX_MAP['Berlin']['HRB'] == ' B'

    def test_bremen_suffix(self):
        """Test Bremen suffix mapping."""
        assert SUFFIX_MAP['Bremen']['HRB'] == ' HB'
        assert SUFFIX_MAP['Bremen']['HRA'] == ' HB'
        assert SUFFIX_MAP['Bremen']['VR'] == ' HB'


# =============================================================================
# Unit Tests - Public API
# =============================================================================

class TestPublicAPI:
    """Unit tests for the public search() function."""

    def test_search_function_exists(self):
        """Test that the search function is importable."""
        assert callable(search)

    def test_search_options_from_parameters(self):
        """Test that SearchOptions can be created with all parameters."""
        opts = SearchOptions(
            keywords="Test",
            keyword_option="exact",
            states=["BE", "HH"],
            register_type="HRB",
            register_number="12345",
            include_deleted=True,
            similar_sounding=True,
            results_per_page=50,
        )
        
        assert opts.keywords == "Test"
        assert opts.keyword_option == "exact"
        assert opts.states == ["BE", "HH"]
        assert opts.register_type == "HRB"
        assert opts.register_number == "12345"
        assert opts.include_deleted is True
        assert opts.similar_sounding is True
        assert opts.results_per_page == 50


class TestHandelsRegisterClass:
    """Unit tests for HandelsRegister class initialization."""

    def test_init_without_args(self):
        """Test that HandelsRegister can be initialized without args."""
        hr = HandelsRegister(debug=False)
        assert hr.args is None
        assert hr.cache is not None
        assert hr.browser is not None

    def test_init_with_debug(self):
        """Test that debug flag is stored correctly."""
        hr = HandelsRegister(debug=True)
        assert hr._debug is True

    def test_init_with_custom_cache(self, temp_cache_dir):
        """Test that custom cache is used."""
        cache = SearchCache(cache_dir=temp_cache_dir)
        hr = HandelsRegister(cache=cache)
        assert hr.cache is cache

    def test_from_options_classmethod(self):
        """Test the from_options class method."""
        opts = SearchOptions(keywords="Test")
        hr = HandelsRegister.from_options(opts, debug=True)
        
        assert hr._debug is True
        assert hasattr(hr, '_default_options')
        assert hr._default_options.keywords == "Test"

    def test_search_company_requires_args(self):
        """Test that search_company raises error without args."""
        hr = HandelsRegister()
        
        with pytest.raises(ValueError, match="benötigt args"):
            hr.search_company()
    
    def test_get_company_details_invalid_type(self):
        """Test that invalid detail_type raises ValueError."""
        hr = HandelsRegister(debug=False)
        company = {'name': 'Test', 'register_num': 'HRB 123'}
        
        with pytest.raises(ValueError, match="Invalid detail_type"):
            hr.get_company_details(company, detail_type="INVALID")


class TestDetailsParserAD:
    """Unit tests for DetailsParser AD (Aktueller Abdruck) parsing."""
    
    @pytest.fixture
    def sample_ad_html(self):
        """Sample HTML from current printout (AD)."""
        return '''
        <html>
        <body>
        <div class="content">
            <h1>Aktueller Abdruck</h1>
            <p>Firma: Test GmbH</p>
            <p>Rechtsform: Gesellschaft mit beschränkter Haftung</p>
            <p>Sitz: Berlin</p>
            <p>Stammkapital: 50.000,00 EUR</p>
            <p>Gegenstand des Unternehmens: Entwicklung von Software</p>
            <p>Geschäftsführer: Hans Schmidt (Berlin), einzelvertretungsberechtigt</p>
        </div>
        </body>
        </html>
        '''
    
    def test_parse_ad_basic(self, sample_ad_html):
        """Test parsing AD content."""
        base_info = {'name': 'Test GmbH', 'register_num': 'HRB 12345', 
                     'court': 'AG Berlin', 'state': 'Berlin', 'status': 'aktuell'}
        details = DetailsParser.parse_ad(sample_ad_html, base_info)
        
        assert details.name == "Test GmbH"
        assert details.legal_form == "Gesellschaft mit beschränkter Haftung"
    
    def test_parse_ad_capital(self, sample_ad_html):
        """Test parsing capital from AD."""
        details = DetailsParser.parse_ad(sample_ad_html)
        
        assert details.capital is not None
        assert "50.000" in details.capital
    
    def test_parse_ad_representatives(self, sample_ad_html):
        """Test parsing representatives from AD."""
        details = DetailsParser.parse_ad(sample_ad_html)
        
        gf = next((r for r in details.representatives if r.role == "Geschäftsführer"), None)
        assert gf is not None
        assert "Schmidt" in gf.name


class TestDetailsParserUT:
    """Unit tests for DetailsParser UT (Unternehmensträger) parsing."""
    
    @pytest.fixture
    def sample_ut_html(self):
        """Sample HTML from company owners view (UT)."""
        return '''
        <html>
        <body>
        <div>
            <h1>Unternehmensträger</h1>
            <p>Gesellschafter: Holding AG, Anteil: 100%</p>
            <p>Geschäftsführer: Maria Müller</p>
        </div>
        </body>
        </html>
        '''
    
    def test_parse_ut_owners(self, sample_ut_html):
        """Test parsing owners from UT."""
        base_info = {'name': 'Test GmbH', 'register_num': 'HRB 12345',
                     'court': 'AG Berlin', 'state': 'Berlin', 'status': 'aktuell'}
        details = DetailsParser.parse_ut(sample_ut_html, base_info)
        
        assert len(details.owners) >= 1
    
    def test_parse_ut_representatives(self, sample_ut_html):
        """Test parsing representatives from UT."""
        details = DetailsParser.parse_ut(sample_ut_html)
        
        gf = next((r for r in details.representatives if r.role == "Geschäftsführer"), None)
        assert gf is not None
        assert "Müller" in gf.name


class TestPublicAPIGetDetails:
    """Unit tests for the public get_details() function."""
    
    def test_get_details_function_exists(self):
        """Test that get_details function is importable."""
        assert callable(get_details)


# =============================================================================
# Integration Tests - Live API
# =============================================================================

@pytest.mark.integration
@pytest.mark.slow
class TestLiveAPI:
    """Integration tests that hit the live Handelsregister API.
    
    These tests are marked with @pytest.mark.integration and @pytest.mark.slow.
    Run with: pytest -m integration
    Skip with: pytest -m "not integration"
    """

    @pytest.mark.parametrize("company,expected_state", [
        ("Hafen Hamburg", "Hamburg"),
        ("Bayerische Motoren Werke", "Bayern"),
        ("Daimler Truck", "Baden-Württemberg"),
        ("Volkswagen", "Niedersachsen"),
        ("RWE", "Nordrhein-Westfalen"),
        ("Fraport", "Hessen"),
        ("Saarstahl", "Saarland"),
        ("Mainz", "Rheinland-Pfalz"),
        ("Nordex", "Mecklenburg-Vorpommern"),
        ("Jenoptik", "Thüringen"),
        ("Vattenfall", "Berlin"),
        ("Bremen", "Bremen"),
        ("Sachsen", "Sachsen"),
        ("Magdeburg", "Sachsen-Anhalt"),
        ("Kiel", "Schleswig-Holstein"),
        ("Potsdam", "Brandenburg"),
    ])
    def test_search_by_state_company(self, company, expected_state):
        """Test searching for companies in different German states."""
        args = argparse.Namespace(
            debug=False,
            force=True,
            schlagwoerter=company,
            schlagwortOptionen='all',
            json=False
        )
        hr = HandelsRegister(args)
        hr.open_startpage()
        companies = hr.search_company()
        
        assert companies is not None
        assert len(companies) > 0

    def test_haus_anker_b_suffix(self):
        """Test that Berlin companies get the B suffix."""
        args = argparse.Namespace(
            debug=False,
            force=True,
            schlagwoerter='Haus-Anker Verwaltungs GmbH',
            schlagwortOptionen='exact',
            json=False
        )
        hr = HandelsRegister(args)
        hr.open_startpage()
        companies = hr.search_company()
        
        assert companies is not None
        
        target = next((c for c in companies if '138434' in (c.get('register_num') or '')), None)
        
        assert target is not None, "Haus-Anker Verwaltungs GmbH with expected number not found"
        assert target['register_num'] == 'HRB 138434 B'

    def test_search_function_simple(self):
        """Test the simple search() function API."""
        results = search("GASAG AG", keyword_option="exact", force_refresh=True)
        
        assert results is not None
        assert len(results) > 0
        assert any("GASAG" in r.get('name', '') for r in results)

    def test_search_function_with_states(self):
        """Test search() with state filtering."""
        results = search(
            "Bank",
            states=["BE"],
            register_type="HRB",
            force_refresh=True,
        )
        
        assert results is not None
        # Results should be from Berlin
        for r in results:
            if r.get('state'):
                assert r['state'] == 'Berlin'

    def test_search_with_options_method(self):
        """Test HandelsRegister.search_with_options() method."""
        opts = SearchOptions(
            keywords="Deutsche Bahn",
            keyword_option="all",
        )
        
        hr = HandelsRegister(debug=False)
        hr.open_startpage()
        results = hr.search_with_options(opts, force_refresh=True)
        
        assert results is not None
        assert len(results) > 0


