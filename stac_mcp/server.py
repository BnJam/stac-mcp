from __future__ import annotations

import logging
from typing import Any

from fastmcp.server.server import FastMCP

from stac_mcp.prompts import register_prompts
from stac_mcp.tools import execution
from stac_mcp.tools.params import preprocess_parameters

app = FastMCP()

_LOGGER = logging.getLogger(__name__)

# Prompts are registered separately to keep the server module small and
# avoid import cycles. See `stac_mcp.prompts.register_prompts` for details.
register_prompts(app)


@app.tool
async def get_root(
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Return the STAC root document for a catalog."""
    return await execution.execute_tool(
        "get_root", arguments={}, catalog_url=catalog_url, headers=None
    )


@app.tool
async def get_conformance(
    check: list[str] | str | None = None,
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Return server conformance classes.

    Args:
        check: Optional list of conformance URIs to check support for.
               If provided, returns a boolean for each URI indicating support.
        catalog_url: Optional catalog URL override.
    """
    arguments = preprocess_parameters({"check": check})
    return await execution.execute_tool(
        "get_conformance", arguments=arguments, catalog_url=catalog_url, headers=None
    )


@app.tool
async def get_capabilities(
    output_format: str | None = "text",
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Return a summary of STAC API capabilities.

    Maps conformance classes to human-readable capability names, making it
    easier for agents to discover what features a catalog supports (e.g.,
    query, sort, fields, aggregations).

    Args:
        output_format: Output format ("text" or "json").
        catalog_url: Optional catalog URL override.
    """
    arguments = preprocess_parameters({"output_format": output_format})
    return await execution.execute_tool(
        "get_capabilities", arguments=arguments, catalog_url=catalog_url, headers=None
    )


@app.tool
async def search_collections(
    limit: int | None = 10, catalog_url: str | None = None
) -> list[dict[str, Any]]:
    """Return a page of STAC collections."""
    return await execution.execute_tool(
        "search_collections",
        arguments={"limit": limit},
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_collection(
    collection_id: str, catalog_url: str | None = None
) -> list[dict[str, Any]]:
    """Fetch a single STAC Collection by id."""
    return await execution.execute_tool(
        "get_collection",
        arguments={"collection_id": collection_id},
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_item(
    collection_id: str,
    item_id: str,
    output_format: str | None = "text",
    sign_assets: bool | None = False,
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Get a specific STAC Item by collection and item ID.

    Args:
        collection_id: The collection ID.
        item_id: The item ID.
        output_format: Output format ("text" or "json").
        sign_assets: If True and catalog is Planetary Computer, sign asset URLs
                     for direct access. Requires planetary-computer package.
        catalog_url: Optional catalog URL override.
    """
    return await execution.execute_tool(
        "get_item",
        arguments={
            "collection_id": collection_id,
            "item_id": item_id,
            "output_format": output_format,
            "sign_assets": sign_assets,
        },
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def search_items(
    collections: list[str] | str | None = None,
    bbox: list[float] | str | None = None,
    datetime: str | None = None,
    limit: int | None = 10,
    query: dict[str, Any] | str | None = None,
    fields: list[str] | str | None = None,
    intersects: dict[str, Any] | str | None = None,
    ids: list[str] | str | None = None,
    sortby: list[str] | str | None = None,
    output_format: str | None = "text",
    sign_assets: bool | None = False,
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Search for STAC items.

    Args:
        collections: One or more collection IDs to search.
        bbox: Bounding box [west, south, east, north] or GeoJSON geometry.
        datetime: Datetime filter (e.g., "2020-01-01/2020-12-31").
        limit: Maximum number of items to return.
        query: Query filter for properties.
        fields: List of fields to include/exclude (e.g., ["id", "properties.datetime"]).
                Prefix with "-" to exclude (e.g., ["-properties.eo:cloud_cover"]).
        intersects: GeoJSON geometry for spatial intersection query.
        ids: List of specific item IDs to retrieve.
        sortby: Sort order (e.g., ["-properties.datetime"] for descending,
                ["+properties.datetime"] for ascending).
        output_format: Output format ("text" or "json").
        sign_assets: If True and catalog is Planetary Computer, sign asset URLs
                     for direct access. Requires planetary-computer package.
        catalog_url: Optional catalog URL override.
    """
    arguments = preprocess_parameters(
        {
            "collections": collections,
            "bbox": bbox,
            "datetime": datetime,
            "limit": limit,
            "query": query,
            "fields": fields,
            "intersects": intersects,
            "ids": ids,
            "sortby": sortby,
            "output_format": output_format,
            "sign_assets": sign_assets,
        }
    )
    return await execution.execute_tool(
        "search_items",
        arguments=arguments,
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def estimate_data_size(
    collections: list[str] | str,
    bbox: list[float] | str | None = None,
    datetime: str | None = None,
    query: dict[str, Any] | str | None = None,
    aoi_geojson: dict[str, Any] | str | None = None,
    limit: int | None = 10,
    force_metadata_only: bool | None = False,
    output_format: str | None = "text",
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Estimate the data size for a STAC query."""
    arguments = preprocess_parameters(
        {
            "collections": collections,
            "bbox": bbox,
            "datetime": datetime,
            "query": query,
            "aoi_geojson": aoi_geojson,
            "limit": limit,
            "force_metadata_only": force_metadata_only,
            "output_format": output_format,
        }
    )
    return await execution.execute_tool(
        "estimate_data_size",
        arguments=arguments,
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_queryables(
    collection_id: list[str],
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Get the queryable properties for a specific STAC collection by its ID."""
    return await execution.execute_tool(
        "get_queryables",
        {"collection_id": collection_id},
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_aggregations(
    collections: list[str],
    bbox: list[float] | None = None,
    datetime: str | None = None,
    query: dict[str, Any] | None = None,
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Get aggregations for STAC items."""
    return await execution.execute_tool(
        "get_aggregations",
        arguments={
            "collections": collections,
            "bbox": bbox,
            "datetime": datetime,
            "query": query,
        },
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_sensor_registry_info() -> list[dict[str, Any]]:
    """Get information about the STAC sensor registry."""
    return await execution.execute_tool(
        "sensor_registry_info",
        arguments={},
        catalog_url=None,
        headers=None,
    )
