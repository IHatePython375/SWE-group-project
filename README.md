# SWE Blackjack – Sprint 1 demo


## Prereqs
- Python 3.12+ from python.org (check “Add Python to PATH” during install)
- PostgreSQL with pgAdmin from postgresql.org
- Each person uses a local DB and their own password

## Note
- Do not move the `.venv` folder to avoid breaking anything. If it is in the wrong place, delete and recreate it.

## First time setup (Windows)

### 1) Install backend packages
```powershell
cd <your path>\SWE-group-project\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2) Create database and tables in pgAdmin

- Create a database.
- Tools -> Query Tool -> open `backend/schema.sql`, paste contents, Execute.
- Tools -> Query Tool -> open `backend/seed.sql`, paste contents, Execute.

## Run

### Backend API
```powershell
cd <your path>\SWE-group-project\backend
.\.venv\Scripts\Activate.ps1
$env:DATABASE_URL="postgresql://postgres:YOUR_PASSWORD@localhost:5432/swe_blackjack"
python app.py
```
**Note about YOUR_PASSWORD**
- Replace `YOUR_PASSWORD` with your local Postgres password.
- If your password has special characters, percent encode them.

## Frontend
```powershell
cd <your path>\SWE-group-project\frontend
py -m http.server 5173
```

## Shutdown
- Frontend terminal: Ctrl+C, then close.
- Backend terminal: Ctrl+C, then deactivate, then close.
- pgAdmin: disconnect and close.