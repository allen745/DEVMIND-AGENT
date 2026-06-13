from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
import os
import base64  
import requests
from groq import Groq
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="DevMind AI",
    description="AI-powered developer tools — Microsoft Agents League Hackathon 2026",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
from fastapi.responses import FileResponse

@app.get("/")
def serve_frontend():
    return FileResponse("index.html")

# Groq client — fast per-file analysis (Steps 2 & 3)
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Microsoft Foundry IQ client — grounded final synthesis (Step 4)
# Accessed via GitHub Models / Azure AI Inference endpoint
foundry_client = ChatCompletionsClient(
    endpoint="https://models.inference.ai.azure.com",
    credential=AzureKeyCredential(os.getenv("GITHUB_TOKEN")),
)




class CodeInput(BaseModel):
    code: str
    language: str = "python"


@app.get("/")
def home():
    return {
        "message": "DevMind AI is Live! 🚀",
        "hackathon": "Microsoft Agents League 2026",
        "track": "Reasoning Agents",
        "microsoft_iq": "Foundry IQ — Azure AI Inference (GitHub Models / GPT-4o)"
    }


@app.post("/review")
def review_code(input: CodeInput):
    response = groq_client.chat.completions.create(
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
    response = groq_client.chat.completions.create(
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
    response = groq_client.chat.completions.create(
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
    response = groq_client.chat.completions.create(
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
    response = groq_client.chat.completions.create(
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




class RepoInput(BaseModel):
    repo_url: str
    github_token: str = ""


def get_repo_files(owner: str, repo: str, token: str = "") -> list:
    """Step 1: Fetch code files from a public GitHub repository via GitHub API."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"https://api.github.com/repos/{owner}/{repo}/git/trees/HEAD?recursive=1"
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        return []

    tree = response.json().get("tree", [])

    allowed_extensions = ['.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.cpp', '.c', '.html', '.css']
    code_files = [
        f for f in tree
        if f['type'] == 'blob'
        and any(f['path'].endswith(ext) for ext in allowed_extensions)
        and f.get('size', 0) < 50000
    ]

    files_content = []
    for file in code_files[:10]:
        file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file['path']}"
        file_response = requests.get(file_url, headers=headers)
        if file_response.status_code == 200:
            content_data = file_response.json()
            if content_data.get('encoding') == 'base64':
                try:
                    content = base64.b64decode(content_data['content']).decode('utf-8', errors='ignore')
                    files_content.append({
                        "path": file['path'],
                        "content": content[:3000]
                    })
                except Exception:
                    pass

    return files_content


def analyze_file(file_path: str, content: str) -> str:
    """Step 2: Analyze a single file for bugs, security issues, and code quality."""
    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""Analyze this file: {file_path}

Code:
{content}

Provide a concise analysis:
1. Purpose of this file
2. Bugs or errors found
3. Security issues
4. Code quality issues
5. Severity: Critical / High / Medium / Low

Max 200 words."""
        }],
        max_tokens=400
    )
    return response.choices[0].message.content


def cross_reference_issues(file_analyses: list) -> str:
    """Step 3: Cross-reference all file analyses to find systemic patterns.

    This is the ACTUAL Step 3 that was missing from the original — it finds
    issues that span multiple files, not just individual file problems.
    """
    all_analyses = "\n\n".join([
        f"FILE: {a['path']}\n{a['analysis']}"
        for a in file_analyses
    ])

    response = groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{
            "role": "user",
            "content": f"""You are a senior engineer performing cross-file codebase analysis.

Individual file analyses:
{all_analyses}

Identify only what spans multiple files:
1. RECURRING PATTERNS — Same issues appearing in multiple files (systemic)
2. CROSS-FILE DEPENDENCIES — Files that affect each other's behavior
3. INCONSISTENCIES — Different coding styles or naming across the codebase
4. SYSTEMIC SECURITY RISKS — Vulnerabilities that affect multiple files
5. ARCHITECTURE CONCERNS — High-level structural problems

Max 200 words. Focus on cross-file patterns only, not individual file issues."""
        }],
        max_tokens=500
    )
    return response.choices[0].message.content


def generate_final_report(repo_name: str, file_analyses: list, cross_ref: str) -> str:
    """Step 4: Generate unified Project Health Report via Microsoft Foundry IQ.

    This is the Microsoft Foundry IQ integration step.
    Uses Azure AI Inference endpoint (GitHub Models / GPT-4o) to deliver
    grounded, cited, structured final synthesis — reducing hallucination
    by grounding the model on concrete per-file evidence from Steps 2 & 3.
    """
    analyses_text = "\n\n".join([
        f"File: {a['path']}\n{a['analysis']}"
        for a in file_analyses
    ])

    response = foundry_client.complete(
        messages=[
            SystemMessage(
                content="""You are DevMind AI Agent — an elite code intelligence system powered by Microsoft Foundry IQ.
Your role: deliver grounded, structured, actionable project health reports.
Always cite specific file names when referencing issues. Avoid generic advice."""
            ),
            UserMessage(
                content=f"""Repository: {repo_name}

=== INDIVIDUAL FILE ANALYSES (Steps 2) ===
{analyses_text}

=== CROSS-FILE PATTERN ANALYSIS (Step 3) ===
{cross_ref}

Generate a comprehensive Project Health Report:

## OVERALL HEALTH SCORE: [0-100]/100

## EXECUTIVE SUMMARY
(3-4 sentences on the overall state of the codebase)

## CRITICAL ISSUES (fix immediately)
- Issue | File(s) affected | Why it is critical

## HIGH PRIORITY ISSUES
- Issue | File(s) affected

## SECURITY VULNERABILITIES
- Vulnerability | Severity | File(s) affected

## CODE QUALITY OBSERVATIONS
- Key observations with specific file references

## ARCHITECTURE OVERVIEW
- How the codebase is structured and key patterns observed

## TOP 5 RECOMMENDED ACTIONS
1.
2.
3.
4.
5.

Be specific, cite file names, avoid generic advice."""
            )
        ],
        model="gpt-4o",
        max_tokens=1500
    )
    return response.choices[0].message.content


@app.post("/agent/analyze-repo")
def analyze_repo(input: RepoInput):
    """
    DevMind AI Agent — Multi-step Repository Intelligence

    Step 1: Parse GitHub URL and fetch all code files (GitHub API)
    Step 2: Analyze each file individually (Groq / Llama-3.3-70b) — fast parallel reasoning
    Step 3: Cross-reference issues across all files (Groq / Llama-3.3-70b) — pattern detection
    Step 4: Generate unified Project Health Report (Microsoft Foundry IQ / GPT-4o) — grounded synthesis

    Track: Reasoning Agents — Microsoft Agents League Hackathon 2026
    Microsoft IQ Layer: Foundry IQ via Azure AI Inference (GitHub Models)
    """
    try:
        # Step 1: Parse GitHub URL
        repo_url = input.repo_url.strip()
        if "github.com/" not in repo_url:
            return {"error": "Invalid GitHub URL. Use format: https://github.com/owner/repo"}

        parts = repo_url.split("github.com/")[-1].strip("/").split("/")
        if len(parts) < 2:
            return {"error": "Invalid GitHub URL format"}

        owner, repo = parts[0], parts[1]
        repo_name = f"{owner}/{repo}"

        # Step 1: Fetch code files via GitHub API
        files = get_repo_files(owner, repo, input.github_token)
        if not files:
            return {"error": "No code files found. Make sure the repository is public and non-empty."}

        # Step 2: Analyze each file individually (fast Groq inference)
        file_analyses = []
        for file in files:
            analysis = analyze_file(file['path'], file['content'])
            file_analyses.append({
                "path": file['path'],
                "analysis": analysis
            })

        # Step 3: Cross-reference issues across all files
        cross_ref = cross_reference_issues(file_analyses)

        # Step 4: Synthesize final report via Microsoft Foundry IQ
        final_report = generate_final_report(repo_name, file_analyses, cross_ref)

        return {
            "repo": repo_name,
            "files_analyzed": len(files),
            "intelligence_layer": "Microsoft Foundry IQ — Azure AI Inference (GitHub Models / GPT-4o)",
            "pipeline": [
                "Step 1: GitHub API — fetched code files",
                "Step 2: Groq / Llama-3.3-70b — per-file analysis",
                "Step 3: Groq / Llama-3.3-70b — cross-file pattern detection",
                "Step 4: Microsoft Foundry IQ / GPT-4o — grounded synthesis"
            ],
            "file_analyses": file_analyses,
            "cross_reference_insights": cross_ref,
            "project_health_report": final_report,
            "powered_by": "DevMind AI Agent — Microsoft Agents League Hackathon 2026"
        }

    except Exception as e:
        return {"error": f"Agent error: {str(e)}"}
