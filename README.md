# Shared Grocery List

A web app for shared grocery list management with AI-powered natural language input. Built for the SE Toolkit Hackathon.

## Demo

![Shared Grocery List Screenshot](docs/screenshot.png)

## Context

### End Users
Roommates, couples, and families who share grocery shopping responsibilities.

### Problem
It's unclear what items have run out at home — someone forgot to buy milk, someone bought bread twice. No shared visibility leads to waste and frustration.

### Solution
A simple shared grocery list accessible from any device. Add items manually or via natural language ("add milk and eggs"), mark items as bought, and everyone sees the same real-time list.

## Features

### Implemented (Version 1)
- ✅ Add/remove grocery items
- ✅ Mark items as "bought"
- ✅ Auto-refresh every 5 seconds for shared sync
- ✅ Natural language input via AI agent (nanobot)
- ✅ Mobile-responsive UI
- ✅ Dockerized deployment

### Planned (Version 2)
- ⬜ Multiple lists (home/work)
- ⬜ Item categories with filtering
- ⬜ Purchase history
- ⬜ User authentication

## Usage

### Manual Item Addition
1. Type the item name in the input field
2. Optionally set quantity
3. Click "Add"

### AI Natural Language Addition
1. Click "🤖 AI Add" button
2. Type natural language like: `"add milk, 3 eggs, and bread"`
3. Click "Add via AI" — the agent parses and adds all items

## Deployment

### Requirements
- Ubuntu 24.04 (or any Linux with Docker)
- Docker and Docker Compose installed

### Step-by-Step

1. **Clone the repository:**
   ```bash
   git clone https://github.com/<your-username>/se-toolkit-hackathon.git
   cd se-toolkit-hackathon
   ```

2. **Build and start all services:**
   ```bash
   docker compose up -d --build
   ```

3. **Access the app:**
   - Frontend: `http://<vm-ip>:3000`
   - Backend API: `http://<vm-ip>:8000`
   - API Docs: `http://<vm-ip>:8000/docs`

### Services
| Service | Port | Description |
|---------|------|-------------|
| Frontend (React + Nginx) | 3000 | Web UI |
| Backend (FastAPI) | 8000 | REST API + Agent |
| Database (PostgreSQL) | 5432 | Persistent storage |

### Local Development

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

**Frontend:**
```bash
cd client-web-react
npm install
REACT_APP_API_URL=http://localhost:8000 npm start
```

## Architecture

```
Client (React) → Backend (FastAPI) → PostgreSQL
                        ↑
                  Agent (nanobot)
```

- **Backend:** FastAPI with SQLAlchemy ORM, PostgreSQL database
- **Frontend:** React + TypeScript, mobile-responsive
- **Agent:** Rule-based NLP parser that extracts items and quantities from natural language
