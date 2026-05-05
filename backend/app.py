import os
import re
import json
import requests
import time
import logging
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, jsonify
from PyPDF2 import PdfReader
import docx
try:
    from .analyzer import ATSAnalyzer
except (ImportError, ValueError):
    from analyzer import ATSAnalyzer

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(override=True)

# Configure paths
basedir = os.path.abspath(os.path.dirname(__file__))
frontend_dir = os.path.join(os.path.dirname(basedir), 'frontend')

app = Flask(__name__,
            template_folder=os.path.join(frontend_dir, 'templates'),
            static_folder=os.path.join(frontend_dir, 'static'))
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "fallback-secret-key")

# Initialize Analyzer
analyzer = ATSAnalyzer()

# ── Helper Functions ─────────────────────────────────────────────────────────

def extract_pdf(file):
    try:
        reader = PdfReader(file)
        return "".join(page.extract_text() or "" for page in reader.pages)
    except Exception as e:
        logger.error(f"PDF extraction error: {e}")
        return ""

def extract_docx(file):
    try:
        doc = docx.Document(file)
        return "\n".join(para.text for para in doc.paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction error: {e}")
        return ""

def escape_latex(text):
    if not text: return ""
    replacements = {'&': '\\&', '%': '\\%', '$': '\\$', '#': '\\#', '_': '\\_', '{': '\\{', '}': '\\}'}
    return "".join(replacements.get(c, c) for c in str(text))

def fill_template(content, data):
    for key, val in data.items():
        content = content.replace(f"<<{key.upper()}>>", escape_latex(str(val)))
    return content

# ── Page Routes ──────────────────────────────────────────────────────────────

@app.route('/')
def home(): 
    return render_template("index.html")

@app.route('/editor')
def editor(): return render_template("editor.html")

@app.route("/resume-builder")
def resume_builder(): return render_template("resume_builder.html")

@app.route("/latex-resume-builder")
def latex_resume_builder(): return render_template("latex_resume_builder.html")

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

@app.route("/account")
def account(): return render_template("account.html")

@app.route("/about")
def about(): return render_template("about.html")

# ── API Proxies and Template Discovery ──────────────────────────────────────

@app.route("/api/templates/<ttype>", methods=["GET"])
def get_templates(ttype):
    # This assumes templates are in a directory named 'template .p' in the root
    template_dir = os.path.join(os.path.dirname(basedir), "template .p")
    if not os.path.exists(template_dir): 
        logger.warning(f"Template directory not found: {template_dir}")
        return jsonify([])
    templates = [d for d in os.listdir(template_dir) if os.path.isdir(os.path.join(template_dir, d))]
    return jsonify(templates)

@app.route("/generate-resume", methods=["POST"])
@app.route("/generate-cover-letter", methods=["POST"])
def generate_resume():
    try:
        data = request.get_json()
        template_name = data.get("template", "fancy rover")
        template_root = os.path.join(os.path.dirname(basedir), "template .p", template_name)
        
        if not os.path.exists(template_root):
            return jsonify({"error": f"Template '{template_name}' not found"}), 404
            
        tex_files = [f for f in os.listdir(template_root) if f.endswith(".tex")]
        if not tex_files: 
            return jsonify({"error": "No .tex file found in template directory"}), 404
            
        with open(os.path.join(template_root, tex_files[0]), "r", encoding="utf-8") as f:
            template_content = f.read()
            
        latex_code = fill_template(template_content, data)
        
        url = "https://api.formatex.io/api/v1/compile"
        api_key = os.environ.get("LATEX_API_KEY", "")
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        
        resp = requests.post(url, headers=headers, json={"latex": latex_code, "engine": "pdflatex"}, timeout=60)
        if resp.status_code == 200: 
            return Response(resp.content, mimetype='application/pdf')
        
        logger.error(f"LaTeX API failed: {resp.status_code} - {resp.text}")
        return jsonify({"error": "LaTeX compilation failed", "status": resp.status_code}), resp.status_code
    except Exception as e:
        logger.error(f"Generate resume error: {e}")
        return jsonify({"error": str(e)}), 500

# ── API Routes ──────────────────────────────────────────────────────────────

@app.route("/analyze", methods=["POST"])
def analyze():
    """Robust /analyze endpoint with guaranteed JSON response."""
    try:
        resume_text = ""
        job_desc = ""

        # 1. Extraction Logic
        if request.is_json:
            data = request.get_json()
            resume_text = data.get("resume_text", "")
            job_desc = data.get("job_description", "")
        else:
            job_desc = request.form.get('job_description', "")
            if 'resume' in request.files:
                file = request.files['resume']
                if file.filename.lower().endswith('.pdf'):
                    resume_text = extract_pdf(file)
                elif file.filename.lower().endswith('.docx'):
                    resume_text = extract_docx(file)
                else:
                    resume_text = file.read().decode('utf-8', errors='ignore')
            elif 'resume_text' in request.form:
                resume_text = request.form['resume_text']

        # 2. Validation
        if not resume_text or not job_desc:
            error_msg = "Missing resume content or job description."
            logger.warning(error_msg)
            if request.is_json or 'api' in request.path:
                return jsonify({"error": error_msg, "score": 0}), 400
            flash(error_msg, 'error')
            return redirect(url_for('home', _anchor='analyzer'))

        # 3. Analysis via Shared Logic
        result = analyzer.analyze(resume_text, job_desc)
        
        # 4. Response Logic
        if request.is_json:
            return jsonify(result)
        
        # Support for frontend template rendering
        return render_template("analyze.html", 
                             result=result, 
                             matched_keywords=result.get("matched_skills", []), 
                             missed_keywords=result.get("missing_keywords", []), 
                             suggestions=result.get("suggestions", ""))

    except Exception as e:
        logger.error(f"Unexpected error in /analyze: {e}", exc_info=True)
        fallback_err = {
            "score": 0,
            "matched_skills": [],
            "missing_keywords": [],
            "suggestions": ["An unexpected error occurred. Please try again later."]
        }
        if request.is_json:
            return jsonify(fallback_err), 500
        return render_template("analyze.html", result=fallback_err)

@app.route("/api/compile", methods=["POST"])
def proxy_compile():
    try:
        data = request.get_json()
        latex_code = data.get("latex", "")
        url = "https://api.formatex.io/api/v1/compile"
        api_key = os.environ.get("LATEX_API_KEY", "")
        headers = {"X-API-Key": api_key, "Content-Type": "application/json"}
        
        resp = requests.post(url, headers=headers, json={"latex": latex_code, "engine": "pdflatex"}, timeout=30)
        if resp.status_code == 200: 
            return Response(resp.content, mimetype='application/pdf')
        return jsonify({"error": "LaTeX compilation failed", "details": resp.text}), 500
    except Exception as e:
        logger.error(f"Compile proxy error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
