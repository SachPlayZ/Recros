from __future__ import annotations

import difflib
import json
from typing import Any

from mcp.server.mcpserver import MCPServer

from recros_api.db import create_user, delete_user, get_conn, init_db
from recros_api.recommender import _item, recommend, update_profile


mcp = MCPServer("recros", description="Cross-domain movie, book, and music recommendations")
VALID_DOMAINS = {"movie", "book", "music"}


def _search_rows(query: str, domain: str | None, limit: int) -> list[Any]:
    query = query.strip().lower()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM items WHERE (? IS NULL OR domain = ?) ORDER BY popularity DESC",
            (domain, domain),
        ).fetchall()
    if not query:
        return rows[:limit]
    scored: list[tuple[float, Any]] = []
    for row in rows:
        title = row["title"].lower()
        creators = row["creators"].lower()
        score = difflib.SequenceMatcher(None, query, title).ratio()
        if query == title:
            score += 2.0
        if query in title:
            score += 1.0
        if query in creators:
            score += 0.7
        scored.append((score, row))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [row for score, row in scored[:limit] if score >= 0.5]


def _match_one(query: str, domain: str | None) -> Any:
    rows = _search_rows(query, domain, 5)
    if not rows:
        raise ValueError(f"No Recros catalog match for '{query}'")
    return rows[0]


def _recommend_for_profile(
    favorite_rows: list[Any],
    count: int,
    recommendation_domains: set[str] | None = None,
) -> list[dict[str, Any]]:
    user_id, _token = create_user()
    try:
        genres: list[str] = []
        for row in favorite_rows:
            genres.extend(x for x in row["genres"].split("|") if x)
        update_profile(
            user_id,
            {
                "preferred_domains": ["movie", "book", "music"],
                "genres": sorted(set(genres)),
                "themes": [],
                "moods": [],
                "disliked_terms": [],
                "exploration": 0.75,
                "seed_item_ids": [row["id"] for row in favorite_rows],
            },
        )
        with get_conn() as conn:
            conn.executemany(
                "INSERT INTO events(user_id, item_id, action, created_at) VALUES (?, ?, 'consume', datetime('now'))",
                [(user_id, row["id"]) for row in favorite_rows],
            )
        return recommend(
            user_id,
            limit=count,
            domain="all",
            allowed_domains=recommendation_domains,
        )
    finally:
        delete_user(user_id)


def _validate_domain(domain: str | None) -> str | None:
    if domain in (None, "", "all", "auto"):
        return None
    if domain not in VALID_DOMAINS:
        raise ValueError("domain must be movie, book, music, or omitted")
    return domain


def _validate_recommendation_domains(domains: list[str] | None) -> set[str] | None:
    """Validate output domains; omitted/empty means all three domains."""
    if not domains or any(str(value).strip().lower() in {"all", "auto"} for value in domains):
        return None
    normalized = {str(value).strip().lower() for value in domains}
    invalid = normalized - VALID_DOMAINS
    if invalid:
        raise ValueError("recommendation_domains must contain only movie, book, or music")
    return normalized


@mcp.tool()
def search_catalog(query: str = "", domain: str | None = None, limit: int = 10) -> str:
    """Search Recros movies, books, and music by title or creator."""
    domain = _validate_domain(domain)
    limit = max(1, min(int(limit), 20))
    init_db()
    rows = _search_rows(query, domain, limit)
    return json.dumps({"query": query, "items": [_item(row) for row in rows]}, indent=2)


@mcp.tool()
def get_item_details(item: str, domain: str | None = None) -> str:
    """Get details for one Recros item by exact ID or title."""
    domain = _validate_domain(domain)
    init_db()
    row = _match_one(item, domain)
    return json.dumps(_item(row), indent=2)


@mcp.tool()
def recommend_from_favorite(
    favorite: str,
    domain: str | None = None,
    count: int = 5,
    recommendation_domains: list[str] | None = None,
) -> str:
    """Recommend from one favorite. Filter output with recommendation_domains; omit it for movies, books, and music."""
    domain = _validate_domain(domain)
    recommendation_domains = _validate_recommendation_domains(recommendation_domains)
    count = max(1, min(int(count), 10))
    init_db()
    row = _match_one(favorite, domain)
    recommendations = _recommend_for_profile([row], count, recommendation_domains)
    return json.dumps(
        {"favorite": _item(row), "recommendations": recommendations, "count": len(recommendations)},
        indent=2,
    )


@mcp.tool()
def recommend_from_favorites(
    favorites: list[str],
    domains: list[str] | None = None,
    count: int = 5,
    recommendation_domains: list[str] | None = None,
) -> str:
    """Blend favorites. Filter output with recommendation_domains; omit it for movies, books, and music."""
    if not favorites or len(favorites) > 5:
        raise ValueError("provide between 1 and 5 favorites")
    domains = domains or [None] * len(favorites)
    if len(domains) != len(favorites):
        raise ValueError("domains must have one entry per favorite")
    recommendation_domains = _validate_recommendation_domains(recommendation_domains)
    count = max(1, min(int(count), 10))
    init_db()
    rows = [_match_one(favorite, _validate_domain(domain)) for favorite, domain in zip(favorites, domains)]
    recommendations = _recommend_for_profile(rows, count, recommendation_domains)
    return json.dumps(
        {
            "favorites": [_item(row) for row in rows],
            "recommendations": recommendations,
            "count": len(recommendations),
        },
        indent=2,
    )


if __name__ == "__main__":
    mcp.run(transport="stdio")
