@echo off
echo Starting Hadeeth RAG Backend...

echo Installing dependencies with Poetry...
poetry install

echo.
echo Backend starting at http://localhost:8000
echo API docs at http://localhost:8000/docs
echo.

poetry run uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
