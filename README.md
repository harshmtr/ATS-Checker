# 🚀 AI-Powered ATS Resume Checker & Career Suite

![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Version](https://img.shields.io/badge/Version-1.0.0-blue)
![License](https://img.shields.io/badge/License-MIT-orange)

A sophisticated, full-stack application designed to help job seekers optimize their resumes for Applicant Tracking Systems (ATS). This suite combines AI-driven analysis with professional document generation.

## ✨ Key Features

- **🔍 Smart ATS Analysis**: Leverages Google Gemini AI to analyze resumes against job descriptions, providing a compatibility score and actionable feedback.
- **📄 Professional Resume Builder**: Create stunning, ATS-friendly resumes using modern templates.
- **✉️ AI Cover Letter Generator**: Generate tailored cover letters based on your resume and target role.
- **🛠 LaTeX Integration**: High-quality PDF generation using premium LaTeX templates for that professional edge.
- **📊 Real-time Scoring**: Instant feedback on formatting, keyword density, and overall impact.
- **📱 Responsive Design**: A sleek, modern glassmorphism UI that works on all devices.

## 🛠 Technology Stack

### Backend
- **Framework**: Flask (Python)
- **AI Engine**: Google GenAI (Gemini 2.0 Flash)
- **Database**: SQLite (SQLAlchemy)
- **Document Processing**: PyPDF2, PDFMiner
- **Templates**: Jinja2 & LaTeX

### Frontend
- **Languages**: HTML5, Vanilla CSS, JavaScript
- **Design System**: Custom Glassmorphism UI
- **Icons**: FontAwesome / Lucide

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- MikTeX or TeX Live (for LaTeX PDF generation)

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/harshmtr/ATS-Checker.git
   cd ATS-Checker
   ```

2. **Set up the virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```

3. **Install dependencies**:
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the `backend` directory:
   ```env
   GEMINI_API_KEY=your_api_key_here
   SECRET_KEY=your_flask_secret_key
   ```

5. **Run the application**:
   ```bash
   python backend/app.py
   ```

## 📂 Project Structure

```text
├── backend/
│   ├── analyzer.py          # AI analysis logic
│   ├── app.py               # Flask server & routes
│   ├── latex_templates/    # Premium LaTeX layouts
│   └── uploads/             # Temporary file storage
├── frontend/
│   ├── static/              # CSS, JS, and Images
│   └── templates/           # HTML views
└── README.md
```

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests to improve the ATS logic or UI.

## 📄 License

This project is licensed under the MIT License.

---
*Built with ❤️ for job seekers everywhere.*
