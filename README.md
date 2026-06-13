# 🚀 DevMind AI Agent

AI-powered multi-step repository intelligence system built for the **Microsoft Agents League Hackathon 2026**.

---

## 🧠 Overview

DevMind AI Agent is a **reasoning-based developer intelligence system** that analyzes entire GitHub repositories and generates a structured **Project Health Report**.

It uses a multi-stage AI pipeline:

- ⚡ Fast per-file analysis (Groq / Llama-3.3-70B)
- 🔍 Cross-file reasoning and pattern detection
- 🧠 Microsoft Foundry IQ final synthesis (Azure AI Inference / GitHub Models)

The system transforms raw code into **actionable engineering intelligence**.

---

## 🏗️ Architecture

### 4-Step AI Pipeline

**Step 1: Repository Ingestion**
- GitHub API fetches repository files
- Filters supported programming languages
- Limits file size for efficiency

**Step 2: Per-File Analysis (Groq)**
- Bug detection
- Security vulnerability analysis
- Code quality evaluation

**Step 3: Cross-File Reasoning**
- Detects systemic issues across files
- Finds inconsistent patterns
- Identifies architecture-level problems

**Step 4: Microsoft Foundry IQ Synthesis**
- Uses GPT-4o via Azure AI Inference / GitHub Models
- Produces grounded, structured final report
- Reduces hallucinations with multi-step reasoning

---

## ⚙️ Features

### Code Intelligence APIs

- `GET /` → Health check
- `POST /review` → AI code review
- `POST /bughunt` → Debugging assistant
- `POST /devdocs` → Auto documentation generator
- `POST /complexity` → Complexity analysis
- `POST /commit` → Smart commit message generator

### AI Agent Endpoint

- `POST /agent/analyze-repo`

Analyzes a full GitHub repository and returns:

- File-by-file AI analysis
- Cross-file system insights
- Security vulnerability report
- Architecture evaluation
- Overall health score (0–100)
- Final executive report

---

## 🧠 Microsoft IQ Integration

This project integrates **Microsoft Foundry IQ** via:

- Azure AI Inference endpoint (GPT-4o)
- GitHub Models API
- Grounded final reasoning layer

### Benefits:
- Reduced hallucination
- Structured outputs
- Evidence-based analysis
- Enterprise-grade reasoning

---

## 🏆 Hackathon Alignment

Built for:

🎯 **Microsoft Agents League Hackathon 2026**

### Tracks:
- 🧠 Reasoning Agents (Primary)
- 💼 Enterprise AI Agents (Extension-ready)



## 🚀 Run Locally

### 1. Install dependencies
```bash
pip install -r requirements.txt

uvicorn main:app --reload

http://127.0.0.1:8000/docs

GROQ_API_KEY=your_groq_key
GITHUB_TOKEN=your_github_token

