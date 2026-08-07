"""Tool to search for items in a STAC catalog."""

from typing import Any

from mcp.types import TextContent

from stac_mcp.tools.client import STACClient

BBOX_MIN_COORDS = 4


def handle_search_items(
    client: STACClient,
    arguments: dict[str, Any],
) -> list[TextContent] | dict[str, Any]:
    collections = arguments.get("collections")
    bbox = arguments.get("bbox")
    dt = arguments.get("datetime")
    query = arguments.get("query")
    limit = arguments.get("limit", 10)
    fields = arguments.get("fields")
    intersects = arguments.get("intersects")
    ids = arguments.get("ids")
    sortby = arguments.get("sortby")
    sign_assets = arguments.get("sign_assets", False)
    items, pagination_links = client.search_items(
        collections=collections,
        bbox=bbox,
        datetime=dt,
        query=query,
        fields=fields,
        intersects=intersects,
        ids=ids,
        sortby=sortby,
        limit=limit,
        sign_assets=sign_assets,
    )
    returned = len(items)
    has_more = returned >= limit
    meta = {
        "catalog_url": client.catalog_url,
        "parameters": {
            "collections": collections,
            "bbox": bbox,
            "datetime": dt,
            "limit": limit,
            "fields": fields,
            "intersects": intersects,
            "ids": ids,
            "sortby": sortby,
        },
        "returned": returned,
        "has_more": has_more,
        "links": pagination_links,
    }
    if arguments.get("output_format") == "json":
        return {"type": "item_list", "count": returned, "items": items, "meta": meta}
    result_text = f"Found {returned} items"
    if has_more:
        result_text += f" (limit {limit}, more may exist)"
    result_text += ":\n\n"
    asset_keys = set()
    for item in items:
        item_id = item.get("id", "unknown")
        collection_id = item.get("collection", "unknown")
        result_text += f"**{item_id}** (Collection: `{collection_id}`)\n"
        dt_value = item.get("datetime")
        if dt_value:
            result_text += f"  Date: {dt_value}\n"
        bbox = item.get("bbox")
        if isinstance(bbox, list | tuple) and len(bbox) >= BBOX_MIN_COORDS:
            result_text += (
                "  BBox: "
                f"[{bbox[0]:.2f}, {bbox[1]:.2f}, {bbox[2]:.2f}, {bbox[3]:.2f}]\n"
            )
        assets = item.get("assets") or {}
        asset_keys.update(assets.keys())
        asset_count = len(assets) if hasattr(assets, "__len__") else 0
        result_text += f"  Assets: {asset_count}\n\n"
        result_text += "\n"
    if asset_keys:
        result_text += "Assets found across items:\n"
        for key in sorted(asset_keys):
            result_text += f" - {key}\n"
    if pagination_links:
        result_text += "\n**Pagination Links:**\n"
        for link in pagination_links:
            rel = link.get("rel", "unknown")
            href = link.get("href", "")
            result_text += f"  - {rel}: {href}\n"
    return [TextContent(type="text", text=result_text)]
