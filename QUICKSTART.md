# Quick Start Guide

## Setup (One-time)

Run the setup script:

```bash
cd /home/adsy42/Coding/pathway-properties
./setup.sh
```

Or manually:

### Backend Setup

```bash
cd backend

# Create virtual environment (use python3, not python)
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### Frontend Setup

```bash
# From project root (not from backend directory!)
cd frontend

# Install dependencies
npm install
```

## Running the Application

### Terminal 1: Backend

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Frontend

```bash
cd frontend
npm run dev
```

You should see:
```
  ▲ Next.js 14.1.0
  - Local:        http://localhost:3000
```

### Open in Browser

Visit **http://localhost:3000**

## Troubleshooting

### "python: command not found"
- Use `python3` instead of `python`
- Or install: `sudo apt install python-is-python3`

### "venv/bin/activate: No such file or directory"
- Make sure you ran `python3 -m venv venv` first
- Check you're in the `backend` directory

### "npm: command not found"
- Install Node.js: `sudo apt install nodejs npm`
- Or use nvm: `curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash`

### "cd frontend: No such file or directory"
- Make sure you're in the project root (`pathway-properties/`), not inside `backend/`
- The frontend folder is a sibling of backend, not a child

### Port already in use
- Backend: Change port in uvicorn command: `--port 8001`
- Frontend: Change port: `npm run dev -- -p 3001`







