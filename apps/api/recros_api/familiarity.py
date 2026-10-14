"""Search real local catalog titles and collect a person's familiar-work anchors.

These selections are development input, never automatic cross-domain ground truth.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import secrets
import sqlite3
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from . import db

ROOT = Path(__file__).resolve().parents[3]
CATALOG_DB = ROOT / 'apps/api/data/familiar-catalog.db'
router = APIRouter(prefix='/api/familiar')


def connect_catalog():
    if not CATALOG_DB.exists():
        raise HTTPException(503, 'Build the local title index with scripts/build_familiar_catalog.py')
    conn = sqlite3.connect(f'{CATALOG_DB.as_uri()}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def init_familiarity():
    with db.get_conn() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS familiar_profiles (token TEXT PRIMARY KEY, payload TEXT NOT NULL)')


@router.get('/search')
def search(q: str = Query(min_length=2,max_length=120), domain: Literal['all','movie','book','music'] = 'all'):
    terms = re.findall(r'\w+', q, flags=re.UNICODE)
    if not terms:
        return {'items':[]}
    match = ' AND '.join('"'+t+'"*' for t in terms)
    with connect_catalog() as conn:
        rows = conn.execute('SELECT w.id,w.domain,w.title,w.creators,w.year,w.description,w.genres '
                            'FROM search JOIN works w ON search.rowid=w.rowid WHERE search MATCH ? '
                            "AND (?='all' OR w.domain=?) ORDER BY bm25(search),w.title,w.year DESC LIMIT 20",
                            (match,domain,domain)).fetchall()
    return {'items':[dict(r) for r in rows]}


class KnownWork(BaseModel):
    id: str | None = None
    title: str = Field(min_length=1,max_length=200)
    domain: Literal['movie','book','music']
    familiarity: Literal['consumed','familiar']
    liking: int = Field(ge=1,le=5)
    reason: str = Field(default='',max_length=800)


class FamiliarProfile(BaseModel):
    works: list[KnownWork] = Field(min_length=1,max_length=20)


@router.post('/profiles')
def save_profile(payload: FamiliarProfile):
    works, seen = [], set()
    with connect_catalog() as conn:
        for work in payload.works:
            data = work.model_dump()
            key = work.id or (work.domain,work.title.casefold())
            if key in seen:
                raise HTTPException(422, 'Choose each work only once')
            seen.add(key)
            if work.id:
                row = conn.execute('SELECT id,title,domain,creators,year,description,genres FROM works WHERE id=?',(work.id,)).fetchone()
                if row is None or row['domain'] != work.domain:
                    raise HTTPException(422, 'Catalog work does not match the selected domain')
                # Preserve authoritative catalog identity, rather than trusting browser titles.
                data.update(dict(row))
                data['evidence_status'] = 'catalog_description_available' if row['description'] else 'no_narrative_description'
            else:
                data['evidence_status'] = 'unresolved_title_needs_source'
            works.append(data)
    token = secrets.token_urlsafe(32)
    data = {'schema':'recros-familiar-anchors-v1','works':works,
            'interpretation':'Self-reported development anchors from one participant; not held-out preference-transfer outcomes.'}
    with db.get_conn() as conn:
        conn.execute('INSERT INTO familiar_profiles VALUES (?,?)',(token,json.dumps(data)))
    return {'token':token,'saved':len(works),'message':'Saved locally. These works need a separately prepared, sourced recommendation trial.'}


@router.get('/profiles/{token}')
def get_profile(token: str):
    with db.get_conn() as conn:
        row = conn.execute('SELECT payload FROM familiar_profiles WHERE token=?',(token,)).fetchone()
    if row is None:
        raise HTTPException(404,'Profile not found')
    return json.loads(row['payload'])
