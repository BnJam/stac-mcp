"""Tests for get_capabilities tool handler."""

from unittest.mock import MagicMock

from stac_mcp.tools.get_capabilities import CAPABILITY_MAP, handle_get_capabilities


def test_handle_get_capabilities_json():
    client = MagicMock()
    client.conformance = [
        "https://api.stacspec.org/v1.0.0/item-search#query",
        "https://api.stacspec.org/v1.0.0/item-search#sort",
    ]
    result = handle_get_capabilities(client, {"output_format": "json"})
    assert result["type"] == "capabilities"
    assert result["capabilities"]["query"]["supported"] is True
    assert result["capabilities"]["sort"]["supported"] is True
    assert result["capabilities"]["fields"]["supported"] is False


def test_handle_get_capabilities_text():
    client = MagicMock()
    client.conformance = [
        "https://api.stacspec.org/v1.0.0/item-search#query",
    ]
    result = handle_get_capabilities(client, {})
    assert isinstance(result, list)
    text = result[0].text
    assert "STAC API Capabilities" in text
    assert "Supported (1)" in text
    assert "query" in text


def test_handle_get_capabilities_empty():
    client = MagicMock()
    client.conformance = []
    result = handle_get_capabilities(client, {"output_format": "json"})
    assert result["type"] == "capabilities"
    for cap in result["capabilities"].values():
        assert cap["supported"] is False


def test_capability_map_has_expected_keys():
    expected = {"query", "sort", "fields", "queryables", "aggregation", "filter"}
    assert set(CAPABILITY_MAP.keys()) == expected
