from stac_mcp.tools.client import STACClient

DEFAULT_CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
CUSTOM_CATALOG_URL = "http://stac.example.internal/api/stac/v1"


def test_default_catalog_url_without_env_var(monkeypatch):
    monkeypatch.delenv("STAC_MCP_CATALOG_URL", raising=False)
    client = STACClient()
    assert client.catalog_url == DEFAULT_CATALOG_URL


def test_env_var_sets_default_catalog_url(monkeypatch):
    monkeypatch.setenv("STAC_MCP_CATALOG_URL", CUSTOM_CATALOG_URL)
    client = STACClient()
    assert client.catalog_url == CUSTOM_CATALOG_URL


def test_explicit_catalog_url_overrides_env_var(monkeypatch):
    monkeypatch.setenv("STAC_MCP_CATALOG_URL", CUSTOM_CATALOG_URL)
    explicit_url = "http://other.example.internal/stac"
    client = STACClient(explicit_url)
    assert client.catalog_url == explicit_url
