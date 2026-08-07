"""Focused tests for STACClient wrapper to raise coverage of tool client logic.

These tests avoid real network calls by mocking the internal `client` attribute
and the private `_http_json` helper.
"""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from stac_mcp.tools.client import (
    CONFORMANCE_FIELDS,
    CONFORMANCE_QUERY,
    CONFORMANCE_QUERYABLES,
    CONFORMANCE_SORT,
    ConformanceError,
    STACClient,
)

NUM_ITEMS = 2
AGG_COUNT = 10


@pytest.fixture
def stac_client(request):
    """Yield a STACClient and clear its conformance cache on teardown."""
    client = STACClient("https://example.com/stac/v1")

    def teardown():
        # Clear cached property to ensure test isolation for conformance checks
        if hasattr(client, "_conformance"):
            delattr(client, "_conformance")

    request.addfinalizer(teardown)  # noqa: PT021
    return client


def _mk_collection(id_: str):
    c = SimpleNamespace()
    c.id = id_
    c.title = f"Title {id_}"
    c.description = f"Description {id_}"
    c.extent = SimpleNamespace(to_dict=lambda: {"spatial": id_})
    c.license = "CC-BY"
    c.providers = []
    c.summaries = SimpleNamespace(to_dict=lambda: {"a": 1})
    c.assets = {"asset1": SimpleNamespace(to_dict=lambda: {"href": "u"})}
    return c


def _mk_item(id_: str, collection_id: str):
    itm = SimpleNamespace()
    itm.id = id_
    itm.collection_id = collection_id
    itm.geometry = None
    itm.bbox = [0, 0, 1, 1]
    itm.datetime = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
    itm.properties = {"eo:cloud_cover": 10}
    itm.assets = {
        "B01": SimpleNamespace(to_dict=lambda: {"href": "u", "type": "image/tiff"}),
    }
    # Provide a to_dict so client code that calls item.to_dict() works in tests
    itm.to_dict = lambda: {
        "id": id_,
        "collection": collection_id,
        "geometry": None,
        "bbox": [0, 0, 1, 1],
        "datetime": itm.datetime.isoformat(),
        "properties": itm.properties,
        "assets": {k: v.to_dict() for k, v in itm.assets.items()},
    }
    return itm


def test_search_collections(stac_client, monkeypatch):
    mock_client = MagicMock()
    mock_client.get_collections.return_value = [
        _mk_collection("c1"),
        _mk_collection("c2"),
    ]
    monkeypatch.setattr(stac_client, "_client", mock_client)
    res = stac_client.search_collections(limit=1)
    assert len(res) == 1
    assert res[0]["id"] == "c1"


def test_get_collection(stac_client, monkeypatch):
    mock_client = MagicMock()
    mock_client.get_collection.return_value = _mk_collection("c9")
    monkeypatch.setattr(stac_client, "_client", mock_client)
    res = stac_client.get_collection("c9")
    assert res["id"] == "c9"
    assert "assets" in res


def test_search_items(stac_client, monkeypatch):
    search_mock = MagicMock()
    # Underlying pystac-client search may provide an object with items() or
    # items_as_dict(). Ensure our mock exposes items_as_dict() as used by code.
    search_mock.items.return_value = [
        _mk_item("i1", "c1"),
        _mk_item("i2", "c1"),
    ]
    search_mock.links = []
    mock_client = MagicMock()
    mock_client.search.return_value = search_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)
    res, links = stac_client.search_items(collections=["c1"], limit=5)
    assert len(res) == NUM_ITEMS
    assert isinstance(res, list)
    assert isinstance(links, list)
    assert isinstance(res[0], dict)
    assert res[0].get("id") == "i1"


def test_get_item(stac_client, monkeypatch):
    collection_mock = MagicMock()
    collection_mock.get_item.return_value = _mk_item("i100", "c9")
    mock_client = MagicMock()
    mock_client.get_collection.return_value = collection_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)
    res = stac_client.get_item("c9", "i100")
    assert res["id"] == "i100"
    assert res["collection"] == "c9"


def test_get_item_not_found(stac_client, monkeypatch):
    """Test that get_item returns None when the item is not found."""
    collection_mock = MagicMock()
    collection_mock.get_item.return_value = None
    mock_client = MagicMock()
    mock_client.get_collection.return_value = collection_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)
    item = stac_client.get_item(collection_id="test-collection", item_id="not-found")
    assert item is None


def test_get_item_collection_not_found(stac_client, monkeypatch):
    """Test that get_item returns None when the collection is not found."""
    mock_client = MagicMock()
    mock_client.get_collection.return_value = None
    monkeypatch.setattr(stac_client, "_client", mock_client)
    item = stac_client.get_item(collection_id="not-found", item_id="some-item")
    assert item is None


# ---------------- Conformance-aware method tests ---------------- #


def test_search_items_with_query_checks_conformance(stac_client, monkeypatch):
    # Mock underlying search and conformance check
    search_mock = MagicMock()
    search_mock.items.return_value = []
    mock_client = MagicMock()
    mock_client.search.return_value = search_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)
    # Set supported conformance
    monkeypatch.setattr(stac_client, "_conformance", CONFORMANCE_QUERY)

    # Should not raise
    stac_client.search_items(query={"proj:epsg": {"eq": 4326}})

    # Check that it fails without the right conformance
    monkeypatch.setattr(stac_client, "_conformance", ["core"])
    with pytest.raises(ConformanceError):
        stac_client.search_items(query={"proj:epsg": {"eq": 4326}})


def test_search_items_with_sortby_checks_conformance(stac_client, monkeypatch):
    # Mock underlying search and conformance check
    search_mock = MagicMock()
    search_mock.items.return_value = []
    mock_client = MagicMock()
    mock_client.search.return_value = search_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)
    # Set supported conformance
    monkeypatch.setattr(stac_client, "_conformance", CONFORMANCE_SORT)

    # Should not raise
    sort_spec = [("properties.datetime", "desc")]
    stac_client.search_items(sortby=sort_spec)
    mock_client.search.assert_called_with(
        collections=None,
        bbox=None,
        datetime=None,
        query=None,
        sortby=sort_spec,
        fields=None,
        intersects=None,
        ids=None,
        limit=10,
    )

    # Check that it fails without the right conformance
    monkeypatch.setattr(stac_client, "_conformance", ["core"])
    with pytest.raises(ConformanceError):
        stac_client.search_items(sortby=sort_spec)


def test_search_items_with_fields_checks_conformance(stac_client, monkeypatch):
    search_mock = MagicMock()
    search_mock.items.return_value = []
    mock_client = MagicMock()
    mock_client.search.return_value = search_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)
    monkeypatch.setattr(stac_client, "_conformance", CONFORMANCE_FIELDS)

    fields_spec = ["id", "properties.datetime"]
    stac_client.search_items(fields=fields_spec)
    mock_client.search.assert_called_with(
        collections=None,
        bbox=None,
        datetime=None,
        query=None,
        sortby=None,
        fields=fields_spec,
        intersects=None,
        ids=None,
        limit=10,
    )

    monkeypatch.setattr(stac_client, "_conformance", ["core"])
    with pytest.raises(ConformanceError):
        stac_client.search_items(fields=fields_spec)


def test_get_queryables_raises_if_unsupported(stac_client, monkeypatch):
    monkeypatch.setattr(stac_client, "_conformance", ["core"])
    with pytest.raises(ConformanceError):
        stac_client.get_queryables()


def test_get_aggregations_raises_if_unsupported(stac_client, monkeypatch):
    monkeypatch.setattr(stac_client, "_conformance", ["core"])
    with pytest.raises(ConformanceError):
        stac_client.get_aggregations()


def test_check_conformance_raises_error_if_missing(stac_client, monkeypatch):
    monkeypatch.setattr(stac_client, "_conformance", ["core"])
    with pytest.raises(ConformanceError, match="does not support"):
        stac_client._check_conformance(  # noqa: SLF001
            ["non-existent-capability"],
        )


def test_check_conformance_handles_older_uri_versions(stac_client, monkeypatch):
    """Verify that an older but compatible conformance URI is accepted."""
    # Server advertises an older RC version of the Queryables spec
    monkeypatch.setattr(
        stac_client,
        "_conformance",
        ["core", "https://api.stacspec.org/v1.0.0-rc.1/item-search#queryables"],
    )

    # Client should not raise an error because the older URI is in its list
    # of acceptable URIs for Queryables.
    try:
        stac_client._check_conformance(CONFORMANCE_QUERYABLES)  # noqa: SLF001
    except ConformanceError:
        pytest.fail(
            "Conformance check failed for a valid (older) URI",
        )


def test_search_items_with_intersects(stac_client, monkeypatch):
    """Test that intersects parameter is passed through correctly."""
    search_mock = MagicMock()
    search_mock.items.return_value = []
    mock_client = MagicMock()
    mock_client.search.return_value = search_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)

    intersects = {
        "type": "Point",
        "coordinates": [-122.4194, 37.7749],
    }
    stac_client.search_items(intersects=intersects)
    mock_client.search.assert_called_with(
        collections=None,
        bbox=None,
        datetime=None,
        query=None,
        sortby=None,
        fields=None,
        intersects=intersects,
        ids=None,
        limit=10,
    )


def test_search_items_with_ids(stac_client, monkeypatch):
    """Test that ids parameter is passed through correctly."""
    search_mock = MagicMock()
    search_mock.items.return_value = []
    mock_client = MagicMock()
    mock_client.search.return_value = search_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)

    ids = ["item1", "item2", "item3"]
    stac_client.search_items(ids=ids)
    mock_client.search.assert_called_with(
        collections=None,
        bbox=None,
        datetime=None,
        query=None,
        sortby=None,
        fields=None,
        intersects=None,
        ids=ids,
        limit=10,
    )


def test_search_items_combined_parameters(stac_client, monkeypatch):
    """Test that multiple new parameters can be used together."""
    search_mock = MagicMock()
    search_mock.items.return_value = []
    mock_client = MagicMock()
    mock_client.search.return_value = search_mock
    monkeypatch.setattr(stac_client, "_client", mock_client)
    monkeypatch.setattr(stac_client, "_conformance", CONFORMANCE_SORT)

    params = {
        "collections": ["sentinel-2-l2a"],
        "intersects": {"type": "Point", "coordinates": [-122.4194, 37.7749]},
        "ids": ["item1", "item2"],
        "sortby": ["-properties.datetime"],
        "limit": 5,
    }
    stac_client.search_items(**params)
    mock_client.search.assert_called_with(
        collections=["sentinel-2-l2a"],
        bbox=None,
        datetime=None,
        query=None,
        sortby=["-properties.datetime"],
        fields=None,
        intersects={"type": "Point", "coordinates": [-122.4194, 37.7749]},
        ids=["item1", "item2"],
        limit=5,
    )


def test_search_cache_key_includes_new_params(stac_client):
    """Test that cache key includes intersects, ids, and sortby."""
    key1 = stac_client._search_cache_key(  # noqa: SLF001
        collections=["col1"],
        bbox=None,
        datetime=None,
        query=None,
        limit=10,
        fields=None,
        intersects={"type": "Point", "coordinates": [0, 0]},
        ids=["item1"],
        sortby=["-datetime"],
    )
    key2 = stac_client._search_cache_key(  # noqa: SLF001
        collections=["col1"],
        bbox=None,
        datetime=None,
        query=None,
        limit=10,
        fields=None,
        intersects={"type": "Point", "coordinates": [1, 1]},
        ids=["item1"],
        sortby=["-datetime"],
    )
    key3 = stac_client._search_cache_key(  # noqa: SLF001
        collections=["col1"],
        bbox=None,
        datetime=None,
        query=None,
        limit=10,
        fields=None,
        intersects={"type": "Point", "coordinates": [0, 0]},
        ids=["item2"],
        sortby=["-datetime"],
    )

    # Different intersects should produce different keys
    assert key1 != key2
    # Different ids should produce different keys
    assert key1 != key3
