#!/usr/bin/env bash
# Download the Kaggle datasets into the *_dataset/ folders the pipeline expects.
# Needs the Kaggle CLI (`pip install kaggle`) and an API token in ~/.kaggle/kaggle.json.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

command -v kaggle >/dev/null || { echo "kaggle CLI not found: pip install kaggle" >&2; exit 1; }

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# fetch <kaggle-slug> <file-in-dataset> <local-path> [whole]
# "whole" downloads the full archive (small datasets, nested paths); otherwise only that file.
fetch() {
  local slug="$1" name="$2" dest="$3" mode="${4:-}"
  if [[ -s "$dest" ]]; then
    echo "skip  $dest (exists)"
    return
  fi
  echo "fetch $slug/$name -> $dest"
  local work="$TMP_DIR/$(basename "$dest")"
  mkdir -p "$work" "$(dirname "$dest")"
  if [[ "$mode" == whole ]]; then
    kaggle datasets download -d "$slug" -p "$work" --unzip --quiet
  else
    kaggle datasets download -d "$slug" -f "$name" -p "$work" --quiet
    for z in "$work"/*.zip; do
      [[ -e "$z" ]] && unzip -oq "$z" -d "$work" && rm "$z"
    done
  fi
  local found
  found="$(find "$work" -type f -name "$name" | head -1)"
  [[ -n "$found" ]] || { echo "missing $name in $slug" >&2; exit 1; }
  mv "$found" "$dest"
}

fetch rounakbanik/the-movies-dataset       movies_metadata.csv movie_dataset/movies_metadata.csv
fetch rounakbanik/the-movies-dataset       keywords.csv        movie_dataset/keywords.csv
fetch rounakbanik/the-movies-dataset       links.csv           movie_dataset/links.csv
fetch grouplens/movielens-20m-dataset      rating.csv          movie_dataset/rating.csv
fetch vatsalmavani/spotify-dataset         data.csv            music_dataset/data_music.csv whole
fetch dylanjcastillo/7k-books-with-metadata books.csv          book_dataset/book_data.csv   whole

echo "done"
