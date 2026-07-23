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
cp backend/.env.example backend/.env
```

Start the development server:

```bash
cd backend
../.venv/bin/python -m alembic upgrade head
../.venv/bin/python -m uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`, with interactive
documentation at `http://127.0.0.1:8000/docs`.

Current authentication endpoints are available under `/api/auth`:

- `POST /register` creates a customer account.
- `POST /login` returns a JWT access token.
- `GET /me` returns the authenticated user.

Public registration creates customer accounts only. Create a staff account from
the backend directory after applying the database migrations:

```bash
../.venv/bin/python -m app.cli create-staff \
  --email agent@example.com \
  --full-name "Support Agent" \
  --role agent
```

The command securely prompts for the password. Use `--role admin` to create an
administrator. Administrators can list active staff through `GET /api/users/staff`.

Current ticket endpoints are available under `/api/tickets`:

- `POST /api/tickets` creates a customer ticket.
- `GET /api/tickets` lists the tickets visible to the authenticated user.
- `GET /api/tickets/{ticket_id}` returns one visible ticket.
- `PATCH /api/tickets/{ticket_id}` updates permitted ticket fields.
- `PATCH /api/tickets/{ticket_id}/assignment` assigns or releases staff work.
- `DELETE /api/tickets/{ticket_id}` deletes a ticket when the role and state allow it.
- `GET /api/tickets/{ticket_id}/replies` lists the ticket conversation.
- `POST /api/tickets/{ticket_id}/replies` adds an authenticated reply.

## Local knowledge retrieval

AstraTickets stores knowledge-base chunks locally in ChromaDB and creates
semantic embeddings with `sentence-transformers/all-MiniLM-L6-v2`. The model is
downloaded on first use and then loaded from the local model cache.

- `POST /api/knowledge/documents` lets administrators ingest an English document.
- `POST /api/knowledge/search` lets staff retrieve relevant chunks with titles,
  source identifiers, source locations, similarity scores, and measured retrieval
  latency.

ChromaDB data is written to `backend/chroma_data` by default and is excluded
from version control. Configure another location with `CHROMA_PATH`.

Run the backend tests from the `backend` directory:

```bash
../.venv/bin/python -m pytest
```

## Frontend development

Install the frontend dependencies and start Vite:

```bash
cd frontend
npm install
npm run dev
```

The frontend is available at `http://127.0.0.1:5173`. During development,
Vite proxies `/api` requests to the FastAPI server on port `8000`.
