from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


ROOT = Path(__file__).resolve().parents[3]


class MCPProtocolTest(unittest.IsolatedAsyncioTestCase):
    async def test_tool_discovery_and_favorite_recommendation(self) -> None:
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "recros_mcp.server"],
            cwd=ROOT,
            env={
                **os.environ,
                "PYTHONPATH": f"{ROOT / 'apps' / 'api'}:{ROOT / 'apps' / 'mcp'}",
                "RECROS_DB": str(ROOT / "apps" / "api" / "data" / "recros.db"),
                "RECROS_RANKER_BUNDLE": str(ROOT / "ml" / "artifacts" / "bundle_latest"),
            },
        )
        async with stdio_client(params) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                tools = await session.list_tools()
                names = sorted(tool.name for tool in tools.tools)
                self.assertEqual(
                    names,
                    ["get_item_details", "recommend_from_favorite", "recommend_from_favorites", "search_catalog"],
                )
                result = await session.call_tool(
                    "recommend_from_favorite", {"favorite": "Interstellar", "domain": "movie", "count": 5}
                )
                self.assertFalse(result.is_error)
                payload = json.loads(result.content[0].text)
                self.assertEqual(payload["favorite"]["title"], "Interstellar")
                self.assertEqual(len(payload["recommendations"]), 5)

                books_only = await session.call_tool(
                    "recommend_from_favorite",
                    {
                        "favorite": "Interstellar",
                        "domain": "movie",
                        "count": 5,
                        "recommendation_domains": ["book"],
                    },
                )
                self.assertFalse(books_only.is_error)
                book_payload = json.loads(books_only.content[0].text)
                self.assertTrue(book_payload["recommendations"])
                self.assertTrue(all(item["domain"] == "book" for item in book_payload["recommendations"]))

                movies_books = await session.call_tool(
                    "recommend_from_favorite",
                    {
                        "favorite": "Interstellar",
                        "domain": "movie",
                        "count": 5,
                        "recommendation_domains": ["movie", "book"],
                    },
                )
                self.assertFalse(movies_books.is_error)
                mixed_payload = json.loads(movies_books.content[0].text)
                self.assertTrue(mixed_payload["recommendations"])
                self.assertTrue(all(item["domain"] in {"movie", "book"} for item in mixed_payload["recommendations"]))

                matrix = [
                    ("book",),
                    ("movie",),
                    ("music",),
                    ("book", "movie"),
                    ("book", "music"),
                    ("movie", "music"),
                    None,
                ]
                for requested in matrix:
                    arguments = {"favorite": "Interstellar", "domain": "movie", "count": 5}
                    if requested is not None:
                        arguments["recommendation_domains"] = list(requested)
                    response = await session.call_tool("recommend_from_favorite", arguments)
                    self.assertFalse(response.is_error)
                    response_payload = json.loads(response.content[0].text)
                    returned = {item["domain"] for item in response_payload["recommendations"]}
                    expected = set(requested or ("book", "movie", "music"))
                    self.assertEqual(len(response_payload["recommendations"]), 5)
                    self.assertEqual(returned, expected)


if __name__ == "__main__":
    unittest.main()
