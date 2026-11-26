# Recros MCP

Tools exposed to Claude:

- `search_catalog`: find titles or creators.
- `get_item_details`: inspect one item.
- `recommend_from_favorite`: one favorite → cross-domain recommendations.
- `recommend_from_favorites`: blend up to five favorites.

Recommendation domain rules are enforced by the server:

- `recommendation_domains: ["book"]` → books only.
- `recommendation_domains: ["movie"]` → movies only.
- `recommendation_domains: ["book", "movie"]` → books and movies only.
- Omit `recommendation_domains` → movies, books, and music.

Recommendations use the exported hybrid bundle. The default embedding model is local and free; the MCP process only reads precomputed vectors from `ml/artifacts/bundle_latest`, so no embedding API key is required for the demo.

Install:

```bash
.venv-api/bin/pip install -r apps/mcp/requirements.txt
```

Claude Desktop config:

```json
{
  "mcpServers": {
    "recros": {
      "command": "/Users/sachplayz/Projects/Recros/.venv-api/bin/python",
      "args": ["-m", "recros_mcp.server"],
      "env": {
        "PYTHONPATH": "/Users/sachplayz/Projects/Recros/apps/api:/Users/sachplayz/Projects/Recros/apps/mcp",
        "RECROS_DB": "/Users/sachplayz/Projects/Recros/apps/api/data/recros.db",
        "RECROS_RANKER_BUNDLE": "/Users/sachplayz/Projects/Recros/ml/artifacts/bundle_latest"
      }
    }
  }
}
```

Restart Claude Desktop, then ask:

> I loved Interstellar. Use Recros to recommend five things across movies, books, and music, and explain each connection.
