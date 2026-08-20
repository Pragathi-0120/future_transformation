# Mosaic - AI-Powered Task & Knowledge Management

Mosaic is an interview-ready MVP that connects an internal knowledge library to team work. Admins upload PDF/TXT files and assign tasks; users search the document knowledge semantically and complete their work.

## Stack

- Backend: Python, FastAPI, SQLAlchemy, MySQL, JWT
- Frontend: React and Vite
- AI: ChromaDB's local MiniLM embedding function
- File extraction: PyPDF

## Core flow

1. An Admin uploads a `.pdf` or `.txt` document.
2. Mosaic extracts text, splits it into overlapping chunks, creates embeddings, and stores vectors plus source metadata in ChromaDB.
3. A User asks a natural-language question.
4. Mosaic embeds the question and retrieves the most similar chunks with filename, excerpt, and relevance score.

This is retrieval-based semantic search: no LLM API is used as the search foundation.

## Database relationships

`roles 1 -> many users`; `users 1 -> many tasks` through both `assigned_to` and `created_by`; `users 1 -> many documents`; `users 1 -> many activity_logs`.

Chroma metadata includes the MySQL `document_id`, which connects every result back to its source document.

## Setup

1. Start MySQL and create the database:

```sql
CREATE DATABASE mosaic_db;
```

2. Update `backend/.env` if your MySQL username, password, or port differs.
3. Start the backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

4. Start the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

On the first document upload, Chroma downloads the local all-MiniLM-L6-v2
embedding model once to `backend/chroma_store/onnx_models/`. Subsequent uploads
and searches run against that project-local model and do not require an LLM API.

## Submission screenshots

After signing in as the Admin, capture the Today, Workboard, Library, Ask
Mosaic, and Pulse views. Add the resulting images under `screenshots/` before
submitting the repository.

## Demo accounts

- Admin: `admin@mosaic.local` / `Admin@123`
- User: `priya@mosaic.local` / `User@123`

## API overview

- `POST /auth/login`
- `GET /tasks?status=pending&assigned_to=1`
- `POST /tasks` (Admin)
- `PUT /tasks/{id}`
- `POST /documents` (Admin)
- `GET /documents`
- `POST /search`
- `GET /analytics` (Admin)

## Interview explanation

JWT contains the authenticated user's identity and role. FastAPI dependencies validate this before each protected endpoint, and Admin-only endpoints use a second role guard. MySQL stores normalized business data while ChromaDB stores semantic vectors with chunk metadata. Every important action is persisted in `activity_logs`, allowing the Admin Pulse view to show recent product activity.
