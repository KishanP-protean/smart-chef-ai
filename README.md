# 🧠👨‍🍳 Smart Chef AI — Multi-Agent Recipe Generator

[![Google ADK](https://img.shields.io/badge/Google-ADK-4285F4?logo=google&logoColor=white)](https://google.github.io/adk-docs/)
[![Gemini AI](https://img.shields.io/badge/Gemini-AI-8E75B2?logo=google&logoColor=white)](https://ai.google.dev/)
[![Cloud Run](https://img.shields.io/badge/Cloud-Run-4285F4?logo=googlecloud&logoColor=white)](https://cloud.google.com/run)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)

> **Gen AI Academy APAC Edition — Hackathon Project**
>
> A multi-agent AI recipe generator powered by Google ADK and Gemini.
> Upload ingredients or documents — **Agent 1** analyzes content for food relevance,
> **Agent 2** generates a complete recipe. Non-food files are rejected automatically.

---

## ✨ Features

- 🧠 **Multi-Agent Architecture** — Two specialized agents working in sequence via ADK's `SequentialAgent`
- 🔍 **Agent 1: Content Analyzer** — Validates if uploaded content is food/cooking related
- 👨‍🍳 **Agent 2: Recipe Chef** — Generates detailed recipes from identified ingredients
- 🚫 **Smart Rejection** — Non-food documents (code, reports, contracts) are rejected gracefully
- 📄 **Document Upload** — Supports PDF, Word, TXT, and image files
- 📝 **Text Input** — Type ingredients directly with dietary/cuisine/meal filters
- 🌙 **Premium Dark UI** — Glassmorphism design with agent pipeline visualization
- 🚀 **One-Click Deploy** — Deploy to Cloud Run with `bash deploy.sh`

---

## 🏗️ Multi-Agent Architecture

```
┌──────────────────────────────────────────────────────┐
│                   Cloud Run Service                   │
│                  (smart-chef-ai)                      │
│                                                       │
│  User Input (text / document)                         │
│        │                                              │
│        ▼                                              │
│  ┌─────────────────────────────────┐                  │
│  │  Root Agent (smart_chef_ai)     │                  │
│  │  Orchestrates the pipeline      │                  │
│  └──────────────┬──────────────────┘                  │
│                 │                                     │
│                 ▼  SequentialAgent                     │
│  ┌──────────────────────────────────────────┐         │
│  │                                          │         │
│  │  ┌──────────────────────────────┐        │         │
│  │  │ Agent 1: Content Analyzer 🔍 │        │         │
│  │  │ • Reads file content          │        │         │
│  │  │ • Checks if food-related      │        │         │
│  │  │ • Extracts ingredients         │        │         │
│  │  │ • Rejects non-food content     │        │         │
│  │  └──────────────┬───────────────┘        │         │
│  │                 │                         │         │
│  │         ┌───────┴───────┐                │          │
│  │         │               │                │          │
│  │    ✅ Food          ❌ Not Food          │          │
│  │         │               │                │          │
│  │         ▼               ▼                │          │
│  │  ┌──────────────┐  Rejection             │         │
│  │  │ Agent 2:      │  Message               │         │
│  │  │ Recipe Chef 👨‍🍳│                        │         │
│  │  │ • Generates    │                        │         │
│  │  │   full recipe  │                        │         │
│  │  └───────────────┘                        │         │
│  └──────────────────────────────────────────┘         │
│                                                       │
│              Gemini 2.5 Flash (Vertex AI)             │
└──────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- [Google Cloud Account](https://cloud.google.com/) with billing enabled
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed and authenticated
- Python 3.11+

### One-Click Deploy to Cloud Run

```bash
git clone https://github.com/KishanP-protean/smart-chef-ai.git
cd smart-chef-ai

# Deploy (interactive — prompts for project ID and region)
bash deploy.sh
```

### Run Locally

```bash
git clone https://github.com/KishanP-protean/smart-chef-ai.git
cd smart-chef-ai

python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your Google Cloud project details

uvicorn main:app --reload --port 8080
```

Open `http://localhost:8080` in your browser.

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `GET` | `/health` | Health check (shows agent architecture) |
| `POST` | `/api/generate` | Generate recipe from text input |
| `POST` | `/api/upload` | Upload document → analyze → generate/reject |

### Example: Text Input

```bash
curl -X POST https://YOUR-URL/api/generate \
  -F "ingredients=chicken, rice, garlic, soy sauce" \
  -F "cuisine_preference=japanese"
```

### Example: File Upload (food document → recipe)

```bash
curl -X POST https://YOUR-URL/api/upload \
  -F "file=@grocery_list.pdf"
```

### Example: File Upload (non-food document → rejection)

```bash
curl -X POST https://YOUR-URL/api/upload \
  -F "file=@business_report.pdf"
# → Agent 1 rejects: "This file does not contain food-related content."
```

---

## 📁 Project Structure

```
smart-chef-ai/
├── recipe_agent/           # ADK Agent Package
│   ├── __init__.py
│   └── agent.py            # Multi-agent: Analyzer → Chef (SequentialAgent)
├── static/
│   ├── index.html          # Web UI with pipeline visualization
│   ├── style.css           # Glassmorphism dark theme
│   └── script.js           # Pipeline animation + rejection handling
├── main.py                 # FastAPI server + file processing
├── requirements.txt
├── Dockerfile
├── deploy.sh               # One-click Cloud Run deployment
├── Procfile
├── .env.example
├── .dockerignore
├── .gitignore
└── README.md
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Agent Framework | Google ADK `SequentialAgent` |
| LLM | Gemini 2.5 Flash (Vertex AI) |
| Backend | FastAPI + Uvicorn |
| Frontend | HTML5, CSS3, Vanilla JS |
| Document Processing | PyPDF2, python-docx, Pillow |
| Deployment | Google Cloud Run |

---

## 🧹 Cleanup

```bash
gcloud run services delete smart-chef-ai --region us-central1
```

---

<p align="center">
  Built with ❤️ using Google ADK • Gemini AI • Cloud Run<br>
  <strong>Cloud Run Service:</strong> <code>smart-chef-ai</code>
</p>
