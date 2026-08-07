"""Tests for Planetary Computer asset signing."""

from unittest.mock import MagicMock, patch

from stac_mcp.tools.client import STACClient


def test_is_planetary_computer_true():
    client = STACClient(
        catalog_url="https://planetarycomputer.microsoft.com/api/stac/v1"
    )
    assert client._is_planetary_computer() is True  # noqa: SLF001


def test_is_planetary_computer_false():
    client = STACClient(catalog_url="https://example.com/stac")
    assert client._is_planetary_computer() is False  # noqa: SLF001


def test_sign_item_non_pc_catalog():
    client = STACClient(catalog_url="https://example.com/stac")
    item = {"id": "item1", "assets": {"data": {"href": "http://example.com/data.tif"}}}
    result = client._sign_item(item)  # noqa: SLF001
    assert result == item


def test_sign_item_pc_catalog_without_package():
    client = STACClient(
        catalog_url="https://planetarycomputer.microsoft.com/api/stac/v1"
    )
    item = {"id": "item1", "assets": {"data": {"href": "http://example.com/data.tif"}}}
    with patch.dict("sys.modules", {"planetary_computer": None}):
        result = client._sign_item(item)  # noqa: SLF001
    assert result == item


def test_sign_item_pc_catalog_with_package():
    client = STACClient(
        catalog_url="https://planetarycomputer.microsoft.com/api/stac/v1"
    )
    item = {"id": "item1", "assets": {"data": {"href": "http://example.com/data.tif"}}}
    mock_pc = MagicMock()
    mock_pc.sign.return_value = "http://example.com/data.tif?signed=true"
    with patch.dict("sys.modules", {"planetary_computer": mock_pc}):
        result = client._sign_item(item)  # noqa: SLF001
    assert result["assets"]["data"]["href"] == "http://example.com/data.tif?signed=true"


def test_sign_items_skips_when_disabled():
    client = STACClient(
        catalog_url="https://planetarycomputer.microsoft.com/api/stac/v1"
    )
    items = [{"id": "item1", "assets": {}}]
    result = client._sign_items(items, sign_assets=False)  # noqa: SLF001
    assert result == items


def test_sign_items_skips_non_pc():
    client = STACClient(catalog_url="https://example.com/stac")
    items = [{"id": "item1", "assets": {}}]
    result = client._sign_items(items, sign_assets=True)  # noqa: SLF001
    assert result == items


def test_search_items_with_sign_assets():
    client = STACClient(
        catalog_url="https://planetarycomputer.microsoft.com/api/stac/v1"
    )
    client._client = MagicMock()  # noqa: SLF001
    client._conformance = []  # noqa: SLF001
    mock_search = MagicMock()
    mock_search.items.return_value = iter([])
    client._client.search.return_value = mock_search  # noqa: SLF001

    mock_pc = MagicMock()
    mock_pc.sign.return_value = "http://example.com/data.tif?signed=true"

    with patch.dict("sys.modules", {"planetary_computer": mock_pc}):
        result = client.search_items(collections=["test"], sign_assets=True, limit=1)
    assert isinstance(result, list)


def test_get_item_with_sign_assets():
    client = STACClient(
        catalog_url="https://planetarycomputer.microsoft.com/api/stac/v1"
    )
    mock_collection = MagicMock()
    mock_item = MagicMock()
    mock_item.id = "item1"
    mock_item.collection_id = "col1"
    mock_item.geometry = None
    mock_item.bbox = None
    mock_item.datetime = None
    mock_item.properties = {}
    mock_asset = MagicMock()
    mock_asset.to_dict.return_value = {"href": "http://example.com/data.tif"}
    mock_item.assets = {"data": mock_asset}
    mock_collection.get_item.return_value = mock_item
    client._client = MagicMock()  # noqa: SLF001
    client._client.get_collection.return_value = mock_collection  # noqa: SLF001

    mock_pc = MagicMock()
    mock_pc.sign.return_value = "http://example.com/data.tif?signed=true"

    with patch.dict("sys.modules", {"planetary_computer": mock_pc}):
        result = client.get_item("col1", "item1", sign_assets=True)
    assert result is not None
    assert result["assets"]["data"]["href"] == "http://example.com/data.tif?signed=true"
