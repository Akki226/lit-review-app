# Backend

## Virtual environment

From this directory (`backend`):

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Run

From `backend`, use this venv’s Python so dependencies (including **biopython**) are available:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uvicorn app.main:app --reload
```

Or without activating: `.venv/bin/uvicorn app.main:app --reload`

If you see `ModuleNotFoundError: No module named 'Bio'`, install deps into the venv you use to run the server: `pip install -r requirements.txt`.

`GET /health` → `{"status": "ok"}` at `http://127.0.0.1:8000/health`.

## Tests

```bash
pip install -r requirements-dev.txt
pytest
```

Integration with OpenAI and PubMed is mocked; the shared sample topic is **macrophage heterogeneity in tuberculosis**.
