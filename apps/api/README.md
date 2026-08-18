# Recros API

Content-first end-to-end MVP for the cross-domain recommendation product.

```bash
cd /Users/sachplayz/Projects/Recros
python3 -m venv .venv-api
.venv-api/bin/pip install -r apps/api/requirements.txt
PYTHONPATH=apps/api .venv-api/bin/python -m recros_api.seed --reset
PYTHONPATH=apps/api .venv-api/bin/uvicorn recros_api.main:app --reload
```

Open http://127.0.0.1:8000. The API stores the catalog, profiles, and feedback in `apps/api/data/recros.db`.

User-scoped routes require `Authorization: Bearer <token>`. Use `POST /api/users` for a local guest token, or `/api/auth/register` and `/api/auth/login` for email/password auth.
