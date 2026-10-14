"""Index the recovered local catalog for familiarity selection. No downloads/model calls."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / 'ml/data/processed/items.parquet'
    destination = ROOT / 'apps/api/data/familiar-catalog.db'
    destination.parent.mkdir(parents=True, exist_ok=True)
    frame = pd.read_parquet(source).fillna('')
    # The legacy normalizer appends a literal nan subtitle to some book titles.
    # Use the original CSV title, keyed by the same ISBN, for this search index.
    books = pd.read_csv(ROOT / 'book_dataset/book_data.csv', dtype={'isbn13':str}).fillna('')
    titles = dict(zip(books['isbn13'], books['title']))
    staging = destination.with_suffix('.building.db')
    if staging.exists():
        staging.unlink()  # This script's disposable, interrupted build only.
    with sqlite3.connect(staging) as conn:
        conn.execute('CREATE TABLE works (id TEXT PRIMARY KEY, domain TEXT NOT NULL, title TEXT NOT NULL, '
                     'creators TEXT, year TEXT, description TEXT, genres TEXT, metadata TEXT)')
        conn.execute('CREATE VIRTUAL TABLE search USING fts5(title, creators, content=works, content_rowid=rowid, tokenize="unicode61 remove_diacritics 2")')
        rows = []
        for r in frame.to_dict('records'):
            title = titles.get(str(r['source_id']), r['title']) if r['domain'] == 'book' else r['title']
            year = str(int(r['year'])) if r['year'] != '' else ''
            rows.append((r['item_key'],r['domain'],title,r['creators'],year,r['description'],r['genres_str'],r['extra_json']))
        conn.executemany('INSERT INTO works VALUES (?,?,?,?,?,?,?,?)', rows)
        conn.execute("INSERT INTO search(search) VALUES ('rebuild')")
        conn.execute('CREATE TABLE provenance (payload TEXT)')
        payload = {'source':'ml/data/processed/items.parquet',
                   'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
                   'counts':frame.groupby('domain').size().to_dict(),
                   'book_title_source':'book_dataset/book_data.csv',
                   'book_title_source_sha256':hashlib.sha256((ROOT/'book_dataset/book_data.csv').read_bytes()).hexdigest()}
        conn.execute('INSERT INTO provenance VALUES (?)',(json.dumps(payload),))
    staging.replace(destination)
    print(json.dumps({'path':str(destination),**payload},indent=2))


if __name__ == '__main__':
    main()
