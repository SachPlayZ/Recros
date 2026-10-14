"""Restore the upstream Kaggle sources without requiring credentials for public data.

Install kagglehub first. Existing nonempty files are retained and audited. Download
errors (including a login/consent requirement) propagate; no alternate data is substituted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [
    ('rounakbanik/the-movies-dataset', 'movies_metadata.csv', 'movie_dataset/movies_metadata.csv', {'id', 'title', 'overview', 'genres'}),
    ('rounakbanik/the-movies-dataset', 'keywords.csv', 'movie_dataset/keywords.csv', {'id', 'keywords'}),
    ('rounakbanik/the-movies-dataset', 'links.csv', 'movie_dataset/links.csv', {'movieId', 'tmdbId'}),
    ('grouplens/movielens-20m-dataset', 'rating.csv', 'movie_dataset/rating.csv', {'userId', 'movieId', 'rating', 'timestamp'}),
    ('vatsalmavani/spotify-dataset/versions/1', 'data/data.csv', 'music_dataset/data_music.csv', {'id', 'name', 'artists', 'valence', 'energy'}),
    ('dylanjcastillo/7k-books-with-metadata/versions/3', 'books.csv', 'book_dataset/book_data.csv', {'isbn13', 'title', 'description', 'average_rating'}),
]


def audit(path: Path, required: set[str]) -> dict:
    with path.open(newline='', encoding='utf-8') as handle:
        reader = csv.reader(handle)
        columns = next(reader)
        if not required.issubset(columns):
            raise ValueError(f'{path.name}: missing columns {required - set(columns)}')
        rows = sum(1 for _ in reader)
    with path.open('rb') as handle:
        digest = hashlib.file_digest(handle, 'sha256').hexdigest()
    return {'path': str(path.relative_to(ROOT)), 'bytes': path.stat().st_size,
            'rows': rows, 'columns': columns, 'sha256': digest}


def main(audit_only: bool = False):
    raw = ROOT / 'ml/data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault('KAGGLEHUB_CACHE', str(raw / 'kaggle-cache'))
    files = []
    for slug, source_name, destination, required in SOURCES:
        target = ROOT / destination
        if not target.is_file() or target.stat().st_size == 0:
            if audit_only:
                raise FileNotFoundError(target)
            import kagglehub

            with TemporaryDirectory(prefix='recros-dataset-', dir=raw) as temp:
                output = Path(temp) / 'download'
                downloaded = Path(kagglehub.dataset_download(slug, path=source_name, output_dir=str(output)))
                # Check schema before promoting the download to its configured path.
                with downloaded.open(newline='', encoding='utf-8') as handle:
                    columns = next(csv.reader(handle))
                if not required.issubset(columns):
                    raise ValueError(f'Unexpected schema from {slug}/{source_name}')
                target.parent.mkdir(parents=True, exist_ok=True)
                downloaded.replace(target)
        record = audit(target, required)
        record.update(source_handle=slug, source_file=source_name,
                      source_url='https://www.kaggle.com/datasets/' + '/'.join(slug.split('/')[:2]))
        files.append(record)
        print(f"{destination}: {record['rows']:,} rows; schema and SHA-256 recorded", flush=True)
    report = {'audited_utc': datetime.now(timezone.utc).isoformat(),
              'upstream_dataset_script_commit': '6fcda21ff19723dbc802f6855d1bcb82136268af',
              'note': 'Re-downloaded public sources, not recovered original trained artifacts. '
                      'Hashes identify the local files; movie sources follow their latest public version.',
              'files': files}
    output = ROOT / 'docs/milestone2/DATA_AUDIT.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--audit-only', action='store_true', help='Check local files without downloading')
    main(parser.parse_args().audit_only)
