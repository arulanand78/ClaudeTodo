# ClaudeTodo

A lightweight task-management app for creating, completing, and deleting todos. Built with a React (Vite) frontend and a Python FastAPI backend.

## Project Structure

```
ClaudeTodo/
├── PRD.md              # Product requirements document
├── README.md
├── backend/            # FastAPI API
│   ├── main.py
│   └── requirements.txt
└── frontend/           # React + Vite SPA
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        └── App.jsx
```

## Backend (FastAPI)

Run from the `backend/` directory. It's recommended to create and activate a
virtual environment before installing dependencies, so packages stay isolated
to this project.

**Create the virtual environment** (once):

```bash
# macOS / Linux
python3 -m venv .venv

# Windows (Git Bash / Command Prompt / PowerShell)
python -m venv .venv
```

**Activate it** (each new shell):

```bash
# macOS / Linux
source .venv/bin/activate

# Windows — Git Bash
source .venv/Scripts/activate

# Windows — Command Prompt
.venv\Scripts\activate

# Windows — PowerShell
.venv\Scripts\Activate.ps1
```

**Install dependencies and run** (with the venv active):

```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

To leave the venv later, run `deactivate`. The `.venv/` folder is git-ignored.

The API serves `GET /health` -> `{ "status": "ok" }`, and interactive docs at `http://localhost:8000/docs`.

## Frontend (React + Vite)

Run from the `frontend/` directory:

```bash
npm install
npm run dev
```

The dev server runs on `http://localhost:5173` and proxies `/api` to the backend on port 8000.

## Status

This is the initial scaffold. See `PRD.md` for the full feature set planned for v1.