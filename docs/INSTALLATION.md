# Installation Guide (Windows)

## Prerequisites
- Windows 10/11
- Python 3.13+
- Node.js 22+ & npm
- Git
- MetaTrader 5 Desktop (Exness) for live/demo broker connection

## Automated Setup
```powershell
.\scripts\setup.ps1
```

## Manual Setup
1. **Python Backend**:
   ```powershell
   cd ai-service
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   copy .env.example .env
   ```
2. **Database**:
   ```powershell
   .\ai-service\.venv\Scripts\python.exe database\init_db.py
   ```
3. **Dashboard**:
   ```powershell
   cd dashboard
   npm install
   ```
