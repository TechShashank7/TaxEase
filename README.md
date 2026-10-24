# TaxEase 🏛️⚡

> **Dynamic Conflict-Aware Vector Indexing (DCAVI) & AI Tax Optimization Platform**

TaxEase is an intelligent Indian Income Tax planning and optimization platform. It combines a deterministic rules engine with a state-of-the-art **DCAVI RAG (Retrieval-Augmented Generation)** pipeline grounded in the official Income Tax Act, preventing legal hallucinations and suppressing statutory conflicts.

---

## 🚀 Architecture & Tech Stack

- **Frontend**: React 18, TypeScript, Tailwind CSS, Lucide Icons, Vite
- **Backend**: FastAPI (Python 3.11+), Pydantic v2
- **Vector Database**: Qdrant (Hybrid / Dense Vector Search)
- **AI / LLM**: Google Gemini (`gemini-2.5-flash` for reasoning & chat, `gemini-embedding-2` for embeddings)
- **Database**: MongoDB (User profiles and analysis persistence)

---

## 📁 Repository Structure

```text
TaxEase/
├── backend/
│   ├── app/
│   │   ├── api/routers/        # Eligibility, AI Assistant, & DCAVI RAG endpoints
│   │   ├── core/config.py      # App configuration & CORS settings
│   │   ├── models/schemas.py   # Pydantic data models
│   │   └── services/           # Rules engine, Qdrant retrieval, Gemini assistant, DCAVI
│   ├── data/                   # Chunks and metadata (PDF ignored from git)
│   ├── scripts/                # Evaluation & ingestion utilities
│   ├── main.py                 # FastAPI application entry point
│   ├── requirements.txt        # Backend dependencies
│   └── .env.example            # Backend environment variables template
├── frontend/
│   ├── src/
│   │   ├── components/         # Citation badges, panels, layouts
│   │   ├── config/api.ts       # Centralized API base URL config
│   │   └── pages/              # Landing, TaxProfile, Dashboard, AIAssistant, RagSearch
│   ├── package.json            # Frontend dependencies & scripts
│   ├── vercel.json             # SPA routing rewrite for Vercel
│   └── .env.example            # Frontend environment variables template
└── docker-compose.yml          # Local Qdrant container definition
```

---

## 🛠️ Local Development Setup

### 1. Vector Database (Qdrant)
Run Qdrant via Docker:
```bash
docker-compose up -d
```
Access the Qdrant Web Dashboard at `http://localhost:6333/dashboard`.

### 2. Backend (FastAPI)
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and MONGODB_URL

uvicorn main:app --reload --port 8001
```
API docs available at `http://localhost:8001/docs`.

### 3. Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🌐 Production Deployment Guide

### Deploy Backend on [Render](https://render.com)
1. Create a **New Web Service** and connect this repository.
2. Configure settings:
   - **Root Directory**: `backend`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. Add Environment Variables in Render:
   - `GEMINI_API_KEY`: Your Google Gemini API key
   - `MONGODB_URL`: Your MongoDB Atlas connection string
   - `QDRANT_URL`: URL to your Qdrant Cloud cluster (or keep local fallback)
   - `QDRANT_API_KEY`: API key for Qdrant Cloud
   - `CORS_ORIGINS`: Your Vercel frontend URL (e.g. `https://your-taxease.vercel.app`)

### Deploy Frontend on [Vercel](https://vercel.com)
1. Import this repository in Vercel.
2. Set **Root Directory** to `frontend`.
3. Framework Preset: `Vite`.
4. Add Environment Variable:
   - `VITE_API_BASE_URL`: `https://your-taxease-backend.onrender.com` (your Render service URL).
5. Deploy! Vercel handles SPA client-side routing automatically via `frontend/vercel.json`.

---

## 📄 License
Academic & Educational Project.
