from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any

import re

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .db import (
    authenticate_password,
    authenticate_token,
    create_user,
    email_exists,
    get_conn,
    init_db,
    revoke_token,
    user_exists,
)
from .recommender import get_profile, recommend_with_trace, record_event, update_profile
from .ranker import ranker_status
from .schemas import Credentials, Feedback, ProfileUpdate
from .bridges import CONCEPTS, bridge_candidates
from .decision_routes import router as decision_router, init_trials
from .familiarity import router as familiarity_router, init_familiarity
from .personal_case import router as personal_case_router
from .transfer_routes import router as transfer_router
from .source_review import router as source_review_router
from .catalog_routes import router as catalog_discovery_router, init_discovery
from .hierarchy_routes import router as hierarchy_router


ROOT = Path(__file__).resolve().parents[3]
WEB_DIR = Path(os.getenv("RECROS_WEB_DIR", ROOT / "apps" / "web"))

app = FastAPI(title="Recros", version="0.1.0")
app.include_router(decision_router)
app.include_router(familiarity_router)
app.include_router(personal_case_router)
app.include_router(transfer_router)
app.include_router(source_review_router)
app.include_router(catalog_discovery_router)
app.include_router(hierarchy_router)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
bearer = HTTPBearer(auto_error=False)


@app.on_event("startup")
def startup() -> None:
    init_db()
    init_trials()
    init_familiarity()
    init_discovery()


def require_user(user_id: int, current_user_id: int) -> None:
    if not user_exists(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    if user_id != current_user_id:
        raise HTTPException(status_code=403, detail="User token does not match requested user")


def current_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)) -> int:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail="Bearer token required")
    user_id = authenticate_token(credentials.credentials)
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user_id


@app.get("/api/health")
def health() -> dict[str, Any]:
    with get_conn() as conn:
        items = conn.execute("SELECT COUNT(*) FROM items").fetchone()[0]
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    status = ranker_status()
    return {"status": "ok", "items": str(items), "users": str(users), "ranker": status}


@app.get('/lab')
def lab():
    return FileResponse(WEB_DIR / 'lab.html')


@app.get('/decision')
def decision_lab():
    return FileResponse(WEB_DIR / 'decision.html')


@app.get('/familiar')
def familiar_works():
    return FileResponse(WEB_DIR / 'familiar.html')


@app.get('/personal-case/{token}')
def personal_case_page(token: str):
    return FileResponse(WEB_DIR / 'personal-case.html')


@app.get('/explore')
def evidence_discovery_page():
    return FileResponse(WEB_DIR / 'explore.html')


@app.get('/evidence')
def bounded_evidence_lab():
    return FileResponse(WEB_DIR / 'evidence.html')


@app.get('/hierarchy')
def hierarchy_research_page():
    return FileResponse(WEB_DIR / 'hierarchy.html')


@app.get('/source-review/{token}')
def source_review_page(token:str):
    return FileResponse(WEB_DIR / 'source-review.html')


@app.get('/api/lab/catalog')
def lab_catalog():
    path = ROOT / 'demo' / 'catalog.real.deepseek.annotated.json'
    if not path.exists():
        raise HTTPException(503, 'Cached language-model annotations have not been generated')
    return json.loads(path.read_text())


@app.get('/api/lab/bridges')
def lab_bridges(seed: str, target: str = 'book', remove: str | None = None):
    if target not in {'movie', 'book', 'music'} or (remove and remove not in CONCEPTS):
        raise HTTPException(422, 'Unknown target domain or concept')
    catalog = lab_catalog()
    try:
        items = bridge_candidates(catalog['items'], seed, target, remove)
    except ValueError as exc:
        raise HTTPException(404, str(exc)) from exc
    return {'items': items, 'synthetic': catalog['synthetic'],
            'model': catalog['annotation_run']['requested_model'],
            'mode': 'cached model annotations; deterministic online scoring'}


@app.post("/api/users")
def users_create() -> dict[str, int | str]:
    user_id, token = create_user()
    return {"user_id": user_id, "token": token}


def _validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise HTTPException(status_code=422, detail="Valid email required")
    return normalized


@app.post("/api/auth/register")
def auth_register(payload: Credentials) -> dict[str, int | str]:
    email = _validate_email(payload.email)
    if email_exists(email):
        raise HTTPException(status_code=409, detail="Email already registered")
    user_id, token = create_user(email, payload.password)
    return {"user_id": user_id, "token": token}


@app.post("/api/auth/login")
def auth_login(payload: Credentials) -> dict[str, int | str]:
    email = _validate_email(payload.email)
    result = authenticate_password(email, payload.password)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    user_id, token = result
    return {"user_id": user_id, "token": token}


@app.get("/api/auth/me")
def auth_me(user_id: int = Depends(current_user)) -> dict[str, int]:
    return {"user_id": user_id}


@app.post("/api/auth/logout")
def auth_logout(user_id: int = Depends(current_user)) -> dict[str, bool]:
    revoke_token(user_id)
    return {"ok": True}


@app.get("/api/users/{user_id}/profile")
def profile_get(user_id: int, current_user_id: int = Depends(current_user)) -> dict:
    require_user(user_id, current_user_id)
    return get_profile(user_id)


@app.put("/api/users/{user_id}/profile")
def profile_put(user_id: int, payload: ProfileUpdate, current_user_id: int = Depends(current_user)) -> dict:
    require_user(user_id, current_user_id)
    return update_profile(user_id, payload.model_dump())


@app.get("/api/users/{user_id}/recommendations")
def recommendations(user_id: int, limit: int = Query(12, ge=1, le=40), domain: str = "all", current_user_id: int = Depends(current_user)) -> dict:
    require_user(user_id, current_user_id)
    return {**recommend_with_trace(user_id, limit, domain), "profile": get_profile(user_id)}


@app.get("/api/users/{user_id}/compare")
def compare(user_id: int, limit: int = Query(12, ge=1, le=40), domain: str = "all", current_user_id: int = Depends(current_user)) -> dict:
    require_user(user_id, current_user_id)
    return {policy: recommend_with_trace(user_id, limit, domain, policy)
            for policy in ('relevance', 'discovery')}


@app.post("/api/users/{user_id}/feedback")
def feedback(user_id: int, payload: Feedback, current_user_id: int = Depends(current_user)) -> dict[str, bool]:
    require_user(user_id, current_user_id)
    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM items WHERE id = ?", (payload.item_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Item not found")
    record_event(user_id, payload.item_id, payload.action)
    return {"ok": True}


@app.get("/api/catalog")
def catalog(
    domain: str = "all",
    q: str = "",
    limit: int = Query(24, ge=1, le=100),
) -> dict:
    clauses = []
    params: list[str | int] = []
    if domain in {"movie", "music", "book"}:
        clauses.append("domain = ?")
        params.append(domain)
    if q.strip():
        clauses.append("(title LIKE ? OR creators LIKE ? OR genres LIKE ? OR tags LIKE ?)")
        needle = f"%{q.strip()}%"
        params.extend([needle] * 4)
    where = " AND ".join(clauses) if clauses else "1=1"
    with get_conn() as conn:
        rows = conn.execute(
            f"SELECT * FROM items WHERE {where} ORDER BY popularity DESC LIMIT ?", (*params, limit)
        ).fetchall()
    from .recommender import _item

    return {"items": [_item(row) for row in rows]}


@app.get("/api/items/{item_id}")
def item_get(item_id: str) -> dict:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM items WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Item not found")
    from .recommender import _item

    return _item(row)


if WEB_DIR.exists():
    app.mount("/assets", StaticFiles(directory=WEB_DIR), name="assets")


@app.get("/")
def home():
    index = WEB_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Web app not found")
    return FileResponse(index)
