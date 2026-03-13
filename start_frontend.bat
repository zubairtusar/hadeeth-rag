@echo off
echo Starting Hadeeth RAG Frontend...

cd frontend

if not exist node_modules (
    echo Installing npm packages...
    npm install --legacy-peer-deps
)

echo.
echo Frontend starting at http://localhost:5173
echo.

npm run dev
