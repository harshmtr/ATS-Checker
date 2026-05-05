import os
import re
import json
import time
from google import genai
from typing import Dict, List, Any

class ATSAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.client = None
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
        
        # Keywords for fallback logic
        self.common_skills = [
            "python", "javascript", "java", "react", "node", "flask", "django", 
            "sql", "nosql", "aws", "docker", "kubernetes", "git", "ci/cd", 
            "machine learning", "data analysis", "project management", "agile",
            "html", "css", "typescript", "angular", "vue", "c++", "c#", "php",
            "ruby", "swift", "kotlin", "go", "rust", "terraform", "ansible",
            "linux", "windows", "macos", "azure", "gcp", "mongodb", "postgresql",
            "mysql", "redis", "elasticsearch", "graphql", "rest api", "unit testing",
            "scrum", "kanban", "devops", "cloud computing", "cybersecurity",
            "artificial intelligence", "deep learning", "nlp", "computer vision",
            "full stack", "backend", "frontend", "ui/ux", "mobile development",
            "software engineer", "developer", "architect", "lead", "senior",
            "communication", "leadership", "problem solving", "teamwork"
        ]

    def analyze(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Main analysis entry point with retry and fallback."""
        print(f"Starting analysis for resume ({len(resume_text)} chars) and job desc ({len(job_description)} chars)")
        
        # 1. Try Gemini API (with retries)
        if self.client:
            for attempt in range(2):
                try:
                    return self._call_gemini(resume_text, job_description)
                except Exception as e:
                    print(f"Gemini API attempt {attempt+1} failed: {e}")
                    if hasattr(e, 'response'):
                        print(f"API Response: {e.response}")
                    time.sleep(1)
        
        # 2. Fallback to manual logic
        print("Falling back to manual ATS analysis")
        return self._manual_fallback(resume_text, job_description)

    def _call_gemini(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Direct call to Gemini API using the new google-genai SDK."""
        prompt = f"""
        Act as an expert ATS (Applicant Tracking System) optimizer. 
        Analyze the provided resume against the job description.
        Return ONLY a raw JSON object with this exact structure:
        {{
            "score": <number 0-100>,
            "matched_skills": [<list of strings>],
            "missing_keywords": [<list of strings>],
            "suggestions": [<list of strings>]
        }}

        Resume: {resume_text[:6000]}
        
        Job Description: {job_description[:4000]}
        """
        
        response = self.client.models.generate_content(
            model='models/gemini-1.5-flash',
            contents=prompt
        )
        
        text = response.text.strip()
        
        # Clean potential markdown wrapping
        if text.startswith("```"):
            text = re.sub(r'^```(?:json)?\n?|\n?```$', '', text, flags=re.MULTILINE).strip()
            
        print("Raw Gemini Response:", text)
        return json.loads(text)

    def _manual_fallback(self, resume_text: str, job_description: str) -> Dict[str, Any]:
        """Sophisticated keyword matching fallback."""
        def clean(t): return set(re.findall(r"\b\w{3,}\b", t.lower()))
        
        res_words = clean(resume_text)
        job_words = clean(job_description)
        
        # Filter for "meaningful" keywords
        matched = sorted(list(res_words & job_words))
        missing = sorted(list(job_words - res_words))
        
        # Refine missing: only keep common technical keywords or words > 4 chars
        missing = [w for w in missing if len(w) > 4 or w in self.common_skills]
        
        # Calculate score: matched / (significant job words)
        score = int((len(matched) / (len(job_words) + 1)) * 100)
        score = min(max(score, 10), 85) # Realistic fallback range
        
        return {
            "score": score,
            "matched_skills": matched[:15],
            "missing_keywords": missing[:15],
            "suggestions": [
                "The AI service is currently busy. Showing local keyword matching results.",
                "Ensure your contact information is clearly visible.",
                "Quantify your achievements with numbers and percentages.",
                "Include more industry-specific keywords found in the job description."
            ]
        }
