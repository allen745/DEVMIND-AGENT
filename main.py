from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import requests
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="DevMind AI")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


class CodeInput(BaseModel):
    code: str
    language: str = "python"


@app.get("/")
def home():
    return {"message": "DevMind AI is Live! 🚀"}


@app.post("/review")
def review_code(input: CodeInput):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"Review this {input.language} code. Find bugs, security issues and give a score out of 100:\n\n{input.code}"
        }]
    )
    return {"review": response.choices[0].message.content}


class BugInput(BaseModel):
    error: str
    code: str = ""
    language: str = "python"


@app.post("/bughunt")
def hunt_bug(input: BugInput):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"I got this error in my {input.language} code:\n\nError: {input.error}\n\nCode: {input.code}\n\nExplain why this bug occurred and provide the fixed code."
        }]
    )
    return {"solution": response.choices[0].message.content}


class DocInput(BaseModel):
    code: str
    doc_type: str = "readme"
    language: str = "python"


@app.post("/devdocs")
def generate_docs(input: DocInput):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"Generate a {input.doc_type} for this {input.language} code:\n\n{input.code}"
        }]
    )
    return {"documentation": response.choices[0].message.content}


class ComplexityInput(BaseModel):
    code: str
    language: str = "python"


@app.post("/complexity")
def analyze_complexity(input: ComplexityInput):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Analyze the time and space complexity of this {input.language} code:

{input.code}

Provide:
1. Time Complexity (Big O notation)
2. Space Complexity (Big O notation)
3. Why this complexity?
4. How to optimize it?
5. Optimized version of the code"""
        }]
    )
    return {"complexity": response.choices[0].message.content}


class CommitInput(BaseModel):
    code: str
    language: str = "python"


@app.post("/commit")
def generate_commit(input: CommitInput):
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Analyze this {input.language} code and generate:
1. A concise git commit message (conventional commits format)
2. A detailed description
3. Type of change (feat/fix/refactor/docs/test)

Code:
{input.code}

Format:
Type: 
Commit: 
Description:"""
        }]
    )
    return {"commit": response.choices[0].message.content}


# ─── HACKATHON: REPO ANALYSIS AGENT ─────────────────────────────────────────

class RepoInput(BaseModel):
    repo_url: str
    github_token: str = ""


def get_repo_files(owner: str, repo: str, token: str = ""):
    """Fetch all code files from a GitHub repository"""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    # Get repo tree
    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return []

    tree = response.json().get("tree", [])

    # Filter only code files
    allowed_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.html', '.css']
    code_files = [
        f for f in tree
        if f['type'] == 'blob' and any(f['path'].endswith(ext) for ext in allowed_extensions)
           and f.get('size', 0) < 50000  # skip files larger than 50KB
    ]

    # Fetch content of each file (max 10 files to avoid timeout)
    files_content = []
    for file in code_files[:10]:
        file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file['path']}"
        file_response = requests.get(file_url, headers=headers)
        if file_response.status_code == 200:
            import base64
            content_data = file_response.json()
            if content_data.get('encoding') == 'base64':
                try:
                    content = base64.b64decode(content_data['content']).decode('utf-8', errors='ignore')
                    files_content.append({
                        "path": file['path'],
                        "content": content[:3000]  # limit to 3000 chars per file
                    })
                except:
                    pass

    return files_content


def analyze_file(file_path: str, content: str) -> str:
    """Step 2: Analyze individual file"""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Analyze this file: {file_path}

Code:
{content}

Provide a brief analysis:
1. Purpose of this file
2. Bugs or errors found
3. Security issues
4. Code quality issues
5. Severity: Critical/High/Medium/Low

Keep it concise — max 200 words."""
        }],
        max_tokens=400
    )
    return response.choices[0].message.content


def generate_final_report(repo_name: str, file_analyses: list) -> str:
    """Step 4: Generate unified project health report"""
    analyses_text = "\n\n".join([
        f"File: {a['path']}\n{a['analysis']}"
        for a in file_analyses
    ])

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""You are DevMind AI Agent — an expert code intelligence system.

You have analyzed the repository: {repo_name}

Here are the individual file analyses:

{analyses_text}

Now generate a comprehensive Project Health Report:

1. OVERALL HEALTH SCORE (0-100)
2. EXECUTIVE SUMMARY (3-4 sentences)
3. CRITICAL ISSUES (must fix immediately)
4. HIGH PRIORITY ISSUES (fix soon)
5. CODE QUALITY OBSERVATIONS
6. SECURITY VULNERABILITIES
7. TOP 5 RECOMMENDED ACTIONS
8. ARCHITECTURE OVERVIEW

Format it clearly with sections and bullet points."""
        }],
        max_tokens=1500
    )
    return response.choices[0].message.content


@app.post("/agent/analyze-repo")
def analyze_repo(input: RepoInput):
    """
    DevMind AI Agent — Multi-step Repository Analysis

    Step 1: Parse repo URL and fetch all files
    Step 2: Analyze each file individually
    Step 3: Cross-reference issues across files
    Step 4: Generate unified project health report
    """
    try:
        # Step 1: Parse GitHub URL
        repo_url = input.repo_url.strip()
        if "github.com/" not in repo_url:
            return {"error": "Invalid GitHub URL. Use format: https://github.com/owner/repo"}

        parts = repo_url.split("github.com/")[-1].strip("/").split("/")
        if len(parts) < 2:
            return {"error": "Invalid GitHub URL format"}

        owner = parts[0]
        repo = parts[1]
        repo_name = f"{owner}/{repo}"

        # Step 2: Fetch all code files
        files = get_repo_files(owner, repo, input.github_token)

        if not files:
            return {"error": "No code files found or repository is private. Make sure the repo is public."}

        # Step 3: Analyze each file (multi-step reasoning)
        file_analyses = []
        for file in files:
            analysis = analyze_file(file['path'], file['content'])
            file_analyses.append({
                "path": file['path'],
                "analysis": analysis
            })

        # Step 4: Generate unified report using Foundry IQ reasoning
        final_report = generate_final_report(repo_name, file_analyses)

        return {
            "repo": repo_name,
            "files_analyzed": len(files),
            "file_analyses": file_analyses,
            "project_health_report": final_report,
            "powered_by": "DevMind AI Agent — Microsoft Agents League Hackathon 2026"
        }

    except Exception as e:
        return {"error": f"Agent error: {str(e)}"}