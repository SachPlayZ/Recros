from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from typing import Any

from .db import get_conn
from .ranker import get_ranker


WORD_RE = re.compile(r"[a-z0-9']+")


def _json(value: str | None, fallback: Any) -> Any:
    try:
        return json.loads(value or "")
    except json.JSONDecodeError:
        return fallback


def _words(value: str) -> set[str]:
    return set(WORD_RE.findall((value or "").lower()))


def _list_words(values: list[str]) -> set[str]:
    return _words(" ".join(values))


def _item(row: Any, reason: str | None = None, score: float | None = None) -> dict[str, Any]:
    result = {
        "id": row["id"],
        "domain": row["domain"],
        "title": row["title"],
        "description": row["description"],
        "creators": row["creators"],
        "genres": [x for x in row["genres"].split("|") if x],
        "tags": [x for x in row["tags"].split("|") if x],
        "year": int(row["year"]) if row["year"] else None,
        "rating": row["rating"],
        "image_url": row["image_url"],
        "metadata": _json(row["metadata"], {}),
    }
    if reason:
        result["reason"] = reason
    if score is not None:
        result["score"] = round(score, 4)
    return result


def get_profile(user_id: int) -> dict[str, Any]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
    if row is None:
        return {
            "user_id": user_id,
            "preferred_domains": [],
            "genres": [],
            "themes": [],
            "moods": [],
            "disliked_terms": [],
            "exploration": 0.5,
            "seed_item_ids": [],
        }
    return {
        "user_id": user_id,
        "preferred_domains": _json(row["preferred_domains"], []),
        "genres": _json(row["genres"], []),
        "themes": _json(row["themes"], []),
        "moods": _json(row["moods"], []),
        "disliked_terms": _json(row["disliked_terms"], []),
        "exploration": row["exploration"],
        "seed_item_ids": _json(row["seed_item_ids"], []),
    }


def update_profile(user_id: int, payload: dict[str, Any]) -> dict[str, Any]:
    fields = {
        "preferred_domains": payload.get("preferred_domains", []),
        "genres": payload.get("genres", []),
        "themes": payload.get("themes", []),
        "moods": payload.get("moods", []),
        "disliked_terms": payload.get("disliked_terms", []),
        "exploration": min(1.0, max(0.0, float(payload.get("exploration", 0.5)))),
        "seed_item_ids": payload.get("seed_item_ids", []),
    }
    with get_conn() as conn:
        conn.execute(
            """UPDATE profiles SET preferred_domains = ?, genres = ?, themes = ?, moods = ?,
               disliked_terms = ?, exploration = ?, seed_item_ids = ?, updated_at = datetime('now')
               WHERE user_id = ?""",
            (
                *(json.dumps(fields[k]) for k in ("preferred_domains", "genres", "themes", "moods", "disliked_terms")),
                fields["exploration"],
                json.dumps(fields["seed_item_ids"]),
                user_id,
            ),
        )
    return get_profile(user_id)


def record_event(user_id: int, item_id: str, action: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO events(user_id, item_id, action, created_at) VALUES (?, ?, ?, datetime('now'))",
            (user_id, item_id, action),
        )


def _feedback_context(user_id: int) -> tuple[set[str], set[str], set[str], Counter[str], Counter[str]]:
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT e.item_id, e.action, i.genres, i.tags, i.creators
               FROM events e JOIN items i ON i.id = e.item_id WHERE e.user_id = ?""",
            (user_id,),
        ).fetchall()
    hidden = {r["item_id"] for r in rows if r["action"] in {"dislike", "skip", "consume"}}
    liked = {r["item_id"] for r in rows if r["action"] in {"like", "save"}}
    liked_words: Counter[str] = Counter()
    liked_creators: Counter[str] = Counter()
    for row in rows:
        if row["item_id"] not in liked:
            continue
        liked_words.update(x for x in (row["genres"] + "|" + row["tags"]).split("|") if x)
        for creator in (row["creators"] or "").split(","):
            if creator.strip():
                liked_creators[creator.strip().lower()] += 1
    return hidden, liked, {r["item_id"] for r in rows}, liked_words, liked_creators


def _genre_profile(user_id: int, profile: dict[str, Any]) -> dict[str, float]:
    weights: Counter[str] = Counter({str(value).lower(): 1.0 for value in profile["genres"]})
    with get_conn() as conn:
        rows = conn.execute(
            """SELECT i.genres, e.action FROM events e JOIN items i ON i.id = e.item_id
               WHERE e.user_id = ? AND e.action IN ('like', 'save')""",
            (user_id,),
        ).fetchall()
    for row in rows:
        for genre in _genre_set(row["genres"]):
            weights[genre] += 1.0
    return dict(weights)


def _genre_set(value: str) -> set[str]:
    return {x.strip().lower() for x in (value or "").split("|") if x.strip()}


def _reason(row: Any, profile: dict[str, Any], genre_match: int, liked_words: Counter[str]) -> str:
    if genre_match:
        matched = [g for g in row["genres"].split("|") if g.lower() in {x.lower() for x in profile["genres"]}]
        return f"Matches your {matched[0].lower()} taste"
    if liked_words:
        item_words = {x.lower() for x in (row["genres"] + "|" + row["tags"]).split("|") if x}
        overlap = item_words & {x.lower() for x in liked_words}
        if overlap:
            return f"Because you liked {next(iter(overlap)).lower()} picks"
    if row["domain"] in profile["preferred_domains"]:
        return f"A strong {row['domain']} pick for your mix"
    if profile["exploration"] > 0.65:
        return "A fresh direction beyond your usual picks"
    return "Popular with people exploring this space"


def recommend(user_id: int, limit: int = 12, domain: str = "all") -> list[dict[str, Any]]:
    profile = get_profile(user_id)
    hidden, _liked, seen, liked_words, liked_creators = _feedback_context(user_id)
    profile_genres = {x.lower() for x in profile["genres"]}
    profile_words = _list_words(profile["themes"] + profile["moods"] + profile["disliked_terms"])
    disliked_words = _list_words(profile["disliked_terms"])
    requested_domains = {domain} if domain in {"movie", "music", "book"} else None

    with get_conn() as conn:
        clauses = []
        params: list[Any] = []
        if requested_domains:
            clauses.append("domain = ?")
            params.append(domain)
        if hidden:
            clauses.append("id NOT IN (%s)" % ",".join("?" for _ in hidden))
            params.extend(sorted(hidden))
        where = " AND ".join(clauses) if clauses else "1=1"
        rows = conn.execute(f"SELECT * FROM items WHERE {where}", params).fetchall()

    ranker = get_ranker()
    genre_profile = _genre_profile(user_id, profile)
    model_scores = ranker.score(rows, genre_profile) if ranker and rows else None
    scored: list[tuple[float, Any, str]] = []
    domain_weights = {d: (1.0 if d in profile["preferred_domains"] else 0.35) for d in ("movie", "music", "book")}
    for index, row in enumerate(rows):
        genres = {x.lower() for x in row["genres"].split("|") if x}
        text_words = _words(" ".join((row["title"], row["description"], row["creators"], row["tags"])))
        genre_match = len(genres & profile_genres)
        theme_match = len(text_words & profile_words)
        dislike_match = len(text_words & disliked_words)
        creator_match = sum(v for k, v in liked_creators.items() if k in row["creators"].lower())
        liked_tag_match = sum(liked_words.get(g, 0) for g in genres)
        popularity = min(math.log1p(max(float(row["popularity"] or 0), 0.0)) / 12.0, 1.0)
        quality = min(max(float(row["rating"] or 0.0) / 5.0, 0.0), 1.0)
        novelty = 1.0 - popularity
        heuristic_score = (
            genre_match * 2.8
            + theme_match * 0.18
            + liked_tag_match * 0.7
            + creator_match * 0.7
            + domain_weights[row["domain"]] * 0.55
            + quality * 0.8
            + popularity * (0.35 - profile["exploration"] * 0.25)
            + novelty * profile["exploration"] * 0.7
            - dislike_match * 1.8
            + (0.15 if row["id"] not in seen else 0.0)
        )
        model_score = model_scores[index] if model_scores is not None else 0.0
        score = model_score * 5.0 + heuristic_score * 0.3 if model_scores is not None else heuristic_score
        scored.append((score, row, _reason(row, profile, genre_match, liked_words)))

    scored.sort(key=lambda item: item[0], reverse=True)
    selected: list[dict[str, Any]] = []
    domain_counts: Counter[str] = Counter()
    max_per_domain = max(2, math.ceil(limit * 0.6))
    for score, row, reason in scored:
        if domain_counts[row["domain"]] >= max_per_domain:
            continue
        selected.append(_item(row, reason, score))
        domain_counts[row["domain"]] += 1
        if len(selected) >= limit:
            break
    return selected
