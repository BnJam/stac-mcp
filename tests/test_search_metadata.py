"""Tests for search response metadata."""

from unittest.mock import MagicMock

from stac_mcp.tools.search_items import handle_search_items
from stac_mcp.tools.search_collections import handle_search_collections


def test_search_items_includes_meta():
    client = MagicMock()
    client.catalog_url = "https://example.com/stac"
    client.search_items.return_value = [
        {"id": "item1", "collection": "col1", "assets": {}},
        {"id": "item2", "collection": "col1", "assets": {}},
    ]
    result = handle_search_items(
        client, {"collections": ["col1"], "limit": 10, "output_format": "json"}
    )
    assert result["type"] == "item_list"
    assert result["count"] == 2
    assert "meta" in result
    meta = result["meta"]
    assert meta["catalog_url"] == "https://example.com/stac"
    assert meta["returned"] == 2
    assert meta["has_more"] is False
    assert meta["parameters"]["collections"] == ["col1"]
    assert meta["parameters"]["limit"] == 10


def test_search_items_has_more_when_at_limit():
    client = MagicMock()
    client.catalog_url = "https://example.com/stac"
    client.search_items.return_value = [{"id": f"item{i}"} for i in range(10)]
    result = handle_search_items(
        client, {"collections": ["col1"], "limit": 10, "output_format": "json"}
    )
    assert result["meta"]["has_more"] is True
    assert result["meta"]["returned"] == 10


def test_search_collections_includes_meta():
    client = MagicMock()
    client.catalog_url = "https://example.com/stac"
    client.search_collections.return_value = [
        {"id": "col1", "title": "Collection 1", "license": "MIT"},
    ]
    result = handle_search_collections(client, {"limit": 10, "output_format": "json"})
    assert result["type"] == "collection_list"
    assert result["count"] == 1
    assert "meta" in result
    meta = result["meta"]
    assert meta["catalog_url"] == "https://example.com/stac"
    assert meta["returned"] == 1
    assert meta["has_more"] is False


def test_search_items_text_output_includes_more_indicator():
    client = MagicMock()
    client.catalog_url = "https://example.com/stac"
    client.search_items.return_value = [{"id": f"item{i}"} for i in range(10)]
    result = handle_search_items(client, {"limit": 10})
    text = result[0].text
    assert "limit 10" in text
    assert "more may exist" in text
