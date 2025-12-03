# SWE Blackjack

## Prereqs

- Python 3.12+ from python.org (check "Add Python to PATH" during install)
- PostgreSQL with pgAdmin from postgresql.org
- Each developer uses a local Postgres database and password
- Git installed and the project cloned locally

## Notes

- Do not move the `.venv` folder. If it ends up in the wrong place, delete it and recreate it.
- Database settings are hard coded in the Python files. Update the password in:
  - `app/api.py`
  - `app/blackjack.py`
  - `app/admin_launcher.py`
  - `app/create_admin.py`
- All of these expect a database named `blackjack_db` and user `postgres` on `localhost:5432` by default.

## First time setup (Windows)

### 1) Create virtual environment and install packages

```powershell
cd <your path>\SWE-group-project
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 2) Create database and tables in pgAdmin

Open pgAdmin and connect to your local server.

Create a new database named `blackjack_db`.

With `blackjack_db` selected:

- Tools -> Query Tool  
- Open `app/schema.sql`, copy or load the file  
- Run the script to create all tables, views, and default settings  


## Run

### Backend API
```powershell
cd <your path>\SWE-group-project
.\.venv\Scripts\Activate.ps1
cd app
python api.py
```
**Note about password**
- Replace password with your local Postgres password.
- If your password has special characters, percent encode them.

## Frontend
```powershell
cd <your path>\SWE-group-project\frontendtest
py -m http.server 5173
```
Open the browser to:
http://localhost:5173

## Shutdown
- Frontend terminal: Ctrl+C, then close.
- Backend terminal: Ctrl+C, then deactivate, then close.
- pgAdmin: disconnect and close.