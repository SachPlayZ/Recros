"""Use the user's existing CLI login. Never read/copy credentials or buy credits."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile


DEFAULT_MODEL = 'deepseek/deepseek-v4-flash'


def parse_result(stdout: str) -> dict:
    results = []
    for line in stdout.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue  # CLI update banners are not protocol frames.
        if isinstance(value, dict) and value.get('type') == 'result':
            results.append(value)
    if not results or results[-1].get('subtype') != 'success':
        raise RuntimeError('Command Code did not return a successful final result')
    return results[-1]


def complete_json(prompt: str, model: str = DEFAULT_MODEL, timeout: int = 180) -> tuple[dict, dict]:
    executable = shutil.which('cmd') or shutil.which('command-code')
    if not executable:
        raise RuntimeError('Command Code CLI not installed; no download or fallback attempted')
    # Empty working directory avoids injecting this repo/history into each request.
    with tempfile.TemporaryDirectory(prefix='recros-model-') as directory:
        process = subprocess.run(
            [executable, '-p', '--model', model, '--max-turns', '1', '--skip-onboarding',
             '--permission-mode', 'plan', '--trust', '--output-format', 'json'],
            input=prompt, text=True, capture_output=True, cwd=directory, timeout=timeout, check=False)
    if process.returncode:
        raise RuntimeError(f'Command Code exited with status {process.returncode}; no automatic paid fallback')
    result = parse_result(process.stdout)
    raw = result['finalText'].strip()
    if raw.startswith('```') and raw.endswith('```'):
        raw = '\n'.join(raw.splitlines()[1:-1])
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError('Model output must be a JSON object')
    # Keep final outputs and usage only; do not publish reasoning or CLI session state.
    provenance = {'requested_model': model, 'provider': 'Command Code CLI',
                  'usage': result.get('usage', {}), 'duration_ms': result.get('durationMs'),
                  'session_id': result.get('sessionId')}
    return parsed, provenance
