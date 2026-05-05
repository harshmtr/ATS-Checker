import os
import re
import json
import requests
import time
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
from PyPDF2 import PdfReader
import docx
from google import genai

# Load environment variables
load_dotenv(override=True)

# Configure paths
basedir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.join(os.path.dirname(basedir), 'frontend')

app = Flask(__name__,
            template_folder=os.path.join(frontend_dir, 'templates'),
            static_folder=os.path.join(frontend_dir, 'static'))
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback-secret-key")

# ── Helper Functions ─────────────────────────────────────────────────────────

def extract_pdf(file):
    reader = PdfReader(file)
    return "".join(page.extract_text() or "" for page in reader.pages)

def extract_docx(file):
    doc = docx.Document(file)
    return "\n".join(para.text for para in doc.paragraphs)

def escape_latex(text):
    if not text: return ""
    replacements = {'&': '\\&', '%': '\\%', '$': '\\$', '#': '\\#', '_': '\\_', '{': '\\{', '}': '\\}'}
    return "".join(replacements.get(c, c) for c in str(text))

def fill_template(content, data):
    for key, val in data.items():
        content = content.replace(f"<<{key.upper()}>>", escape_latex(val))
    return content

# ── Page Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def home(): return render_template("index.html")

@app.route('/editor')
def editor(): return render_template("editor.html")

@app.route("/resume-builder")
def resume_builder(): return render_template("resume_builder.html")

@app.route("/latex-resume-builder")
def latex_resume_builder(): return render_template("latex_resume_builder.html")

@app.route("/create")
def create(): return render_template("create.html")

@app.route("/tools")
def tools(): return render_template("tools.html")

@app.route("/resume")
def resume(): return render_template("resume.html")

@app.route("/cv", methods=["GET", "POST"])
def cv(): return render_template("cv.html")

@app.route("/latex-cv")
def latex_cv(): return render_template("latex_cv.html")

@app.route("/cover-letter", methods=["GET", "POST"])
def cover_letter(): return render_template("cover-letter.html")

@app.route("/latex-cover-letter")
def latex_cover_letter(): return render_template("latex_cover_letter.html")

@app.route("/register")
def register(): return render_template("register.html")

@app.route("/about")
def about(): return render_template("about.html")

@app.route("/account")
def account(): return render_template("account.html")

# ── API Proxies and Template Discovery ──────────────────────────────────────

@app.route("/api/templates/<ttype>", methods=["GET"])
def get_templates(ttype):
    template_dir = os.path.join(os.path.dirname(basedir), "template .p")
    if not os.path.exists(template_dir): return jsonify([])
    templates = [d for d in os.listdir(template_dir) if os.path.isdir(os.path.join(template_dir, d))]
    return jsonify(templates)

@app.route("/api/compile", methods=["POST"])
def proxy_compile():
    data = request.get_json()
    latex_code = data.get("latex", "")
    url = "https://api.formatex.io/api/v1/compile"
    api_key = os.environ.get("LATEX_API_KEY", "")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json={"latex": latex_code, "engine": "pdflatex"})
        if resp.status_code == 200: return Response(resp.content, mimetype='application/pdf')
        return resp.text, 500
    except Exception as e: return str(e), 500

@app.route("/analyze", methods=["POST"])
def analyze():
    # 1. Get Data (Support both JSON and Form)
    resume_text = ""
    job_desc = ""

    if request.is_json:
        data = request.get_json()
        resume_text = data.get("resume_text", "")
        job_desc = data.get("job_description", "")
    else:
        if 'resume' in request.files and 'job_description' in request.form:
            file = request.files['resume']
            job_desc = request.form['job_description']
            if file.filename.lower().endswith('.pdf'):
                resume_text = extract_pdf(file)
            elif file.filename.lower().endswith('.docx'):
                resume_text = extract_docx(file)
        
    if not resume_text or not job_desc:
        error_msg = "Missing resume text or job description."
        if request.is_json: return jsonify({"error": error_msg}), 400
        flash(error_msg, 'error')
        return redirect(url_for('home', _anchor='analyzer'))

    # 2. Call Gemini API with Fallback
    try:
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"""Return ONLY valid JSON:
{{
"score": number,
"matched_keywords": [],
"missing_keywords": [],
"suggestions": ""
}}

Resume: {resume_text[:4000]}
Job: {job_desc[:2000]}
"""
        )

        text = response.text.strip()
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n?|\n?```$', '', text, flags=re.MULTILINE).strip()
            
        result = json.loads(text)
        
        if request.is_json: return jsonify(result)
        return render_template("analyze.html", result=result, matched_keywords=result.get("matched_keywords", []), missed_keywords=result.get("missing_keywords", []), suggestions=result.get("suggestions", ""))

    except Exception as e:
        print("Gemini Error:", e)

        # 🔁 FALLBACK LOGIC
        # Extract meaningful words (filter out common short words)
        def get_words(t): return set(re.findall(r"\b\w{3,}\b", t.lower()))
        resume_words = get_words(resume_text)
        job_words = get_words(job_desc)

        matched = list(resume_words & job_words)
        missing = list(job_words - resume_words)
        
        # Calculate a fair score
        score = int(len(matched) / (len(job_words) + 1) * 100)
        score = min(score, 95) # Cap fallback score to be realistic

        fallback_result = {
            "score": score,
            "matched_keywords": matched[:10],
            "missing_keywords": missing[:10],
            "suggestions": "The AI is currently at its limit. Showing high-speed local keyword analysis. Please try again in 60 seconds for full AI insights."
        }

        if request.is_json: return jsonify(fallback_result)
        return render_template("analyze.html", result=fallback_result, matched_keywords=fallback_result["matched_keywords"], missed_keywords=fallback_result["missing_keywords"], suggestions=fallback_result["suggestions"])

# ── Resume/CV Building Routes ────────────────────────────────────────────────

@app.route("/generate-resume", methods=["POST"])
def generate_resume():
    data = request.get_json()
    template_name = data.get("template", "fancy rover")
    template_root = os.path.join(os.path.dirname(basedir), "template .p", template_name)
    tex_files = [f for f in os.listdir(template_root) if f.endswith(".tex")]
    if not tex_files: return jsonify({"error": "No .tex file found"}), 404
    with open(os.path.join(template_root, tex_files[0]), "r", encoding="utf-8") as f:
        template_content = f.read()
    latex_code = fill_template(template_content, data)
    
    url = "https://api.formatex.io/api/v1/compile"
    api_key = os.environ.get("LATEX_API_KEY", "")
    headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
    try:
        resp = requests.post(url, headers=headers, json={"latex": latex_code, "engine": "pdflatex"})
        if resp.status_code == 200: return Response(resp.content, mimetype='application/pdf')
        return jsonify({"error": "LaTeX failed"}), 500
    except: return jsonify({"error": "LaTeX connection error"}), 500

if __name__ == "__main__":
    app.run(debug=True)
