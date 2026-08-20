@echo off
set "ROOT=%~dp0"

start "Mosaic Backend" /D "%ROOT%backend" "%ROOT%backend\.venv\Scripts\python.exe" -m uvicorn app.main:app --reload
start "Mosaic Frontend" /D "%ROOT%frontend" cmd /c npm.cmd run dev

timeout /t 3 /nobreak > nul
start "" http://localhost:5173
