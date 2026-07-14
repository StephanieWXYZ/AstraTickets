# AstraTickets

AstraTickets is a full-stack customer-support ticketing system that combines
traditional support workflows with local AI-assisted knowledge retrieval.

The project will include:

- a FastAPI and SQLAlchemy backend;
- a React and TypeScript frontend;
- JWT-based authentication;
- customer, agent, and administrator roles;
- ticket creation, updates, replies, assignment, and status workflows;
- a local RAG pipeline using SentenceTransformers and ChromaDB; and
- a reproducible retrieval-latency benchmark.

Implementation and setup instructions will be added as development progresses.

## Backend development

Create a virtual environment and install the API with its development tools:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e "backend[dev]"
```

Start the development server:

```bash
cd backend
../.venv/bin/python -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, with interactive
documentation at `http://127.0.0.1:8000/docs`.

Run the backend tests from the `backend` directory:

```bash
../.venv/bin/python -m pytest
```
