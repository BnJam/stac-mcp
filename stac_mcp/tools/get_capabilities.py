"""Tool to get STAC API capabilities summary."""

from typing import Any

from mcp.types import TextContent

from stac_mcp.tools.client import STACClient

CAPABILITY_MAP = {
    "query": {
        "uris": [
            "https://api.stacspec.org/v1.0.0/item-search#query",
            "https://api.stacspec.org/v1.0.0-beta.2/item-search#query",
        ],
        "description": "Advanced property filtering with CQL-like expressions",
    },
    "sort": {
        "uris": [
            "https://api.stacspec.org/v1.0.0/item-search#sort",
        ],
        "description": "Sort search results by properties",
    },
    "fields": {
        "uris": [
            "https://api.stacspec.org/v1.0.0/item-search#fields",
            "https://api.stacspec.org/v1.0.0-beta.2/item-search#fields",
        ],
        "description": "Select which properties to include in results",
    },
    "queryables": {
        "uris": [
            "https://api.stacspec.org/v1.0.0/item-search#queryables",
            "https://api.stacspec.org/v1.0.0-rc.1/item-search#queryables",
        ],
        "description": "Discover filterable properties",
    },
    "aggregation": {
        "uris": [
            "https://api.stacspec.org/v1.0.0/ogc-api-features-p3/conf/aggregation",
        ],
        "description": "Aggregate search results (counts, statistics)",
    },
    "filter": {
        "uris": [
            "https://api.stacspec.org/v1.0.0/item-search#filter",
            "https://api.stacspec.org/v1.0.0-beta.2/item-search#filter",
        ],
        "description": "CQL2 filtering support",
    },
}


def handle_get_capabilities(
    client: STACClient,
    arguments: dict[str, Any],
) -> list[TextContent] | dict[str, Any]:
    conformance = client.conformance
    capabilities = {}
    for name, info in CAPABILITY_MAP.items():
        supported = any(uri in conformance for uri in info["uris"])
        capabilities[name] = {
            "supported": supported,
            "description": info["description"],
        }
    if arguments.get("output_format") == "json":
        return {"type": "capabilities", "capabilities": capabilities}
    result_text = "**STAC API Capabilities**\n\n"
    supported_list = [
        (name, info) for name, info in capabilities.items() if info["supported"]
    ]
    unsupported_list = [
        (name, info) for name, info in capabilities.items() if not info["supported"]
    ]
    if supported_list:
        result_text += f"**Supported ({len(supported_list)}):**\n"
        for name, info in supported_list:
            result_text += f"- `{name}`: {info['description']}\n"
    if unsupported_list:
        result_text += f"\n**Not Supported ({len(unsupported_list)}):**\n"
        for name, info in unsupported_list:
            result_text += f"- `{name}`: {info['description']}\n"
    return [TextContent(type="text", text=result_text)]
