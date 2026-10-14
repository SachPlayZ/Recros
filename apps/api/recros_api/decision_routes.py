"""Local decision trials. Opaque session tokens grant access to one trial only."""
from __future__ import annotations

import json
import secrets
import time
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from . import db
from .deliberation import THEMES, act, browser_view, catalog, make_case, new_state, receipt
from .bridges import verified_facets

router = APIRouter(prefix='/api/decision')


def init_trials():
    with db.get_conn() as conn:
        conn.execute('CREATE TABLE IF NOT EXISTS decision_sessions '
                     '(token TEXT PRIMARY KEY, state TEXT NOT NULL)')


class Trial(BaseModel):
    seed_id: str
    target: Literal['movie', 'book', 'music']
    mode: Literal['demo', 'personal'] = 'demo'
    condition: Literal['both_unknown', 'preference_unknown', 'item_fact_unknown', 'both_known'] = 'both_unknown'
    budget: int = Field(default=2, ge=0, le=2)
    initial_preference: str | None = None
    source_familiarity: Literal['unknown', 'unfamiliar', 'familiar', 'consumed'] = 'unknown'
    source_liking: int | None = Field(default=None, ge=1, le=5)


class Step(BaseModel):
    kind: Literal['ask_user', 'inspect_evidence', 'recommend', 'abstain']
    expected_revision: int = Field(ge=0)
    answer: str | None = None
    item: Literal['A', 'B'] | None = None


class Rating(BaseModel):
    interest: int = Field(ge=1, le=5)
    familiarity: Literal['unfamiliar', 'familiar', 'consumed']


class Ratings(BaseModel):
    expected_revision: int = Field(ge=0)
    A: Rating
    B: Rating
    theme_fit: Literal['yes', 'partly', 'no']
    feedback: str = Field(default='', max_length=1500)


def read_state(conn, token):
    row = conn.execute('SELECT state FROM decision_sessions WHERE token = ?', (token,)).fetchone()
    if row is None:
        raise HTTPException(404, 'Trial not found')
    return json.loads(row['state'])


def checked_state(conn, token, revision):
    conn.execute('BEGIN IMMEDIATE')
    state = read_state(conn, token)
    if state['revision'] != revision:
        raise HTTPException(409, 'Trial changed. Reload its current state before continuing.')
    return state


def save(conn, token, state):
    conn.execute('UPDATE decision_sessions SET state = ? WHERE token = ?', (json.dumps(state), token))


@router.get('/catalog')
def trial_catalog():
    try:
        data = catalog()
    except (OSError, ValueError) as exc:
        raise HTTPException(503, 'The verified catalog is unavailable') from exc
    items = []
    for i in data['items']:
        first = next(f['concept'] for f in verified_facets(i) if f['concept'] in THEMES)
        items.append({**{k: i[k] for k in ('id', 'title', 'domain', 'description')},
                      'themes': [first, THEMES[(THEMES.index(first) + 1) % len(THEMES)]]})
    return {'items': items}


@router.post('/sessions')
def create_trial(payload: Trial):
    if payload.mode == 'personal' and (payload.condition != 'both_unknown' or payload.budget != 2):
        raise HTTPException(422, 'Personal trials use the two-action, both-unknown condition')
    try:
        case = make_case(payload.seed_id, payload.target, payload.condition,
                         order=secrets.randbelow(2), budget=payload.budget)
        state = new_state(case, payload.mode, payload.initial_preference)
    except (ValueError, OSError) as exc:
        raise HTTPException(400, str(exc)) from exc
    state['source_familiarity'] = payload.source_familiarity
    state['source_liking'] = payload.source_liking
    token = secrets.token_urlsafe(32)
    with db.get_conn() as conn:
        conn.execute('INSERT INTO decision_sessions VALUES (?, ?)', (token, json.dumps(state)))
    return {'token': token, **browser_view(state)}


@router.get('/sessions/{token}')
def get_trial(token: str):
    with db.get_conn() as conn:
        return browser_view(read_state(conn, token))


@router.post('/sessions/{token}/actions')
def take_action(token: str, payload: Step):
    with db.get_conn() as conn:
        state = checked_state(conn, token, payload.expected_revision)
        try:
            state = act(state, payload.kind, payload.answer, payload.item)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        save(conn, token, state)
    return browser_view(state)


@router.post('/sessions/{token}/ratings')
def rate_trial(token: str, payload: Ratings):
    with db.get_conn() as conn:
        state = checked_state(conn, token, payload.expected_revision)
        if state['status'] == 'active' or state['ratings'] is not None:
            raise HTTPException(409, 'Finish the trial first; ratings can be saved once')
        state['ratings'] = {a: getattr(payload, a).model_dump() for a in ('A', 'B')}
        state['feedback'] = {'theme_fit': payload.theme_fit, 'text': payload.feedback}
        state['revision'] += 1
        state['rated_at'] = time.time()
        save(conn, token, state)
    return browser_view(state)


@router.get('/sessions/{token}/export')
def export_trial(token: str):
    with db.get_conn() as conn:
        state = read_state(conn, token)
    if state['status'] == 'active':
        raise HTTPException(409, 'Finish the trial before exporting withheld item evidence')
    return {'schema': 'recros-personal-trial-v1', 'participant_count_claim': None,
            'interpretation': 'Self-reported interest in one local trial. Not blinded, '
                              'not consumption satisfaction or a population estimate.',
            'mode': state['mode'], 'method': state['method'],
            'source': state['case']['source']['title'], 'source_domain': state['case']['source']['domain'],
            'target_domain': state['case']['target'],
            'source_familiarity': state['source_familiarity'], 'source_liking': state['source_liking'],
            'condition': state['case']['condition'], 'budget': state['case']['budget'],
            'catalog_sha256': state['case']['catalog_sha256'], 'annotation_model': state['case']['model'],
            'candidate_order': receipt(state), 'preference': state['preference'],
            'history': state['history'], 'terminal': state['terminal'],
            'ratings': state['ratings'], 'feedback': state['feedback'],
            'created_at': state['created_at'], 'rated_at': state.get('rated_at')}
