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
    CacheEntry,
    Company,
    HandelsRegister,
    HistoryEntry,
    ParseError,
    ResultParser,
    SearchCache,
    get_companies_in_searchresults,
    parse_result,
    SUFFIX_MAP,
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


