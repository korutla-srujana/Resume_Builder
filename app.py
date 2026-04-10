from flask import Flask, render_template, request, redirect, url_for, session, send_file
import base64
import json
import os
from pathlib import Path
import re
import sqlite3
import uuid
from utils.pdf_generator import generate_pdf

app = Flask(__name__)
app.secret_key = "your_secret_key"
PROFILE_IMAGE_DIR = os.path.join("static", "uploads", "profile_images")

SKILL_FIELDS = {
    "languages": "Languages",
    "web_technologies": "Web Technologies",
    "frameworks": "Frameworks",
    "databases": "Databases",
    "tools_platforms": "Tools & Platforms",
    "core_concepts": "Core Concepts",
    "testing": "Testing",
    "cloud_devops": "Cloud & DevOps",
}

CONTACT_ICON_MAP = {
    "email": "email",
    "phone": "phone",
    "linkedin": "linkedin",
    "github": "github",
}


def clean_text(value):
    if isinstance(value, str):
        return value.strip()
    return ""


def parse_json_field(name, fallback):
    raw_value = request.form.get(name, "").strip()
    if not raw_value:
        return fallback

    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return fallback


def normalize_entries(entries, fields):
    normalized_entries = []
    if not isinstance(entries, list):
        return normalized_entries

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        normalized_entry = {field: clean_text(entry.get(field, "")) for field in fields}
        if any(normalized_entry.values()):
            normalized_entries.append(normalized_entry)

    return normalized_entries


def normalize_skills(skills):
    if isinstance(skills, str):
        skills = {"languages": skills}
    if not isinstance(skills, dict):
        skills = {}

    return {field: clean_text(skills.get(field, "")) for field in SKILL_FIELDS}


def split_skill_items(value):
    return [item.strip() for item in re.split(r"[\n,]+", value) if item.strip()]


def normalize_url(value):
    cleaned = clean_text(value)
    if not cleaned:
        return ""

    if cleaned.startswith(("http://", "https://", "mailto:", "tel:")):
        return cleaned

    return f"https://{cleaned}"


def normalize_phone_link(value):
    cleaned = clean_text(value)
    if not cleaned:
        return ""

    digits = re.sub(r"[^\d+]", "", cleaned)
    return f"tel:{digits}" if digits else ""


def build_contact_items(data):
    contact_items = []
    contact_fields = [
        ("email", "email", lambda value: f"mailto:{value}"),
        ("phone", "phone", normalize_phone_link),
        ("linkedin", "linkedin", normalize_url),
        ("github", "github", normalize_url),
    ]

    for key, label, href_builder in contact_fields:
        value = clean_text(data.get(key, ""))
        if value:
            contact_items.append({
                "key": key,
                "label": label,
                "value": value,
                "href": href_builder(value),
            })

    return contact_items


def build_profile_image_render_src(image_value):
    cleaned = clean_text(image_value)
    if not cleaned:
        return ""

    if cleaned.startswith("data:image"):
        return cleaned

    if cleaned.startswith("/static/"):
        return (Path(app.root_path) / cleaned.lstrip("/")).resolve().as_uri()

    return cleaned


def build_pdf_html(data):
    css_path = Path(app.root_path) / "static" / "css" / "style.css"
    inline_css = css_path.read_text(encoding="utf-8") + """
html, body {
    margin: 0;
    padding: 0;
    width: 794px;
    min-height: 1123px;
    background: #ffffff;
    overflow: hidden;
}
body.pdf-export-page {
    background: white !important;
}
html,
body.pdf-export-page,
body.pdf-export-page * {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}
.pdf-shell {
    box-sizing: border-box;
    width: 794px;
    min-height: 1123px;
    padding: 18px;
    background: #ffffff;
}
.pdf-shell .resume-sheet {
    box-sizing: border-box;
    width: 758px;
    min-height: 1087px;
    margin: 0 !important;
}
#pdf-link-metadata {
    display: none !important;
}
"""
    return render_template('resume/pdf.html', resume_data=data, inline_css=inline_css, pdf_mode=True)


def store_profile_image(image_value):
    image_text = clean_text(image_value)
    if not image_text:
        return ""

    if image_text.startswith("/static/"):
        return image_text

    match = re.match(r"^data:image/([a-zA-Z0-9+]+);base64,(.+)$", image_text)
    if not match:
        return ""

    extension = match.group(1).lower().replace("jpeg", "jpg").replace("+xml", "")
    encoded = match.group(2)

    try:
        image_bytes = base64.b64decode(encoded)
    except Exception:
        return ""

    os.makedirs(PROFILE_IMAGE_DIR, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.{extension}"
    file_path = os.path.join(PROFILE_IMAGE_DIR, filename)

    with open(file_path, "wb") as image_file:
        image_file.write(image_bytes)

    return f"/static/uploads/profile_images/{filename}"


def build_skill_groups(skills):
    skill_groups = []
    for key, label in SKILL_FIELDS.items():
        items = split_skill_items(skills.get(key, ""))
        if items:
            skill_groups.append({
                "key": key,
                "label": label,
                "items": items,
            })
    return skill_groups


def normalize_resume_data(data):
    if not isinstance(data, dict):
        data = {}

    normalized_data = {
        "name": clean_text(data.get("name", "")),
        "role": clean_text(data.get("role", "")),
        "email": clean_text(data.get("email", "")),
        "phone": clean_text(data.get("phone", "")),
        "linkedin": clean_text(data.get("linkedin", "")),
        "github": clean_text(data.get("github", "")),
        "profile_image_data": clean_text(data.get("profile_image_data", "")),
        "profile_image_render_src": build_profile_image_render_src(data.get("profile_image_data", "")),
        "summary": clean_text(data.get("summary", data.get("career_objective", ""))),
        "template": clean_text(data.get("template", "")) or "classic",
        "skills": normalize_skills(data.get("skills", {})),
        "education": normalize_entries(
            data.get("education", []),
            ["institution", "degree", "specialization", "start_year", "end_year", "score"],
        ),
        "projects": normalize_entries(
            data.get("projects", []),
            ["title", "url", "description", "technologies"],
        ),
        "work_experience": normalize_entries(
            data.get("work_experience", []),
            ["company", "role", "start_date", "end_date", "description"],
        ),
        "certifications": normalize_entries(
            data.get("certifications", []),
            ["title", "issuer", "url", "year"],
        ),
        "achievements": normalize_entries(
            data.get("achievements", []),
            ["text"],
        ),
        "custom_sections": normalize_entries(
            data.get("custom_sections", []),
            ["title", "content"],
        ),
    }

    if not normalized_data["education"] and isinstance(data.get("education"), str):
        institution = clean_text(data.get("education", ""))
        if institution:
            normalized_data["education"] = [{
                "institution": institution,
                "degree": "",
                "specialization": "",
                "start_year": "",
                "end_year": "",
                "score": "",
            }]

    if not normalized_data["projects"] and isinstance(data.get("projects"), str):
        project_text = clean_text(data.get("projects", ""))
        if project_text:
            normalized_data["projects"] = [{
                "title": project_text,
                "url": "",
                "description": "",
                "technologies": "",
            }]

    if not normalized_data["work_experience"] and isinstance(data.get("work_experience"), str):
        work_text = clean_text(data.get("work_experience", ""))
        if work_text:
            normalized_data["work_experience"] = [{
                "company": "",
                "role": "",
                "start_date": "",
                "end_date": "",
                "description": work_text,
            }]

    if not normalized_data["certifications"] and isinstance(data.get("certifications"), str):
        certification_text = clean_text(data.get("certifications", ""))
        if certification_text:
            normalized_data["certifications"] = [{
                "title": certification_text,
                "issuer": "",
                "url": "",
                "year": "",
            }]

    if not normalized_data["achievements"] and isinstance(data.get("achievements"), str):
        achievement_lines = [
            line.strip()
            for line in data.get("achievements", "").splitlines()
            if line.strip()
        ]
        normalized_data["achievements"] = [{"text": line} for line in achievement_lines]

    normalized_data["skill_groups"] = build_skill_groups(normalized_data["skills"])
    normalized_data["contact_items"] = build_contact_items(normalized_data)
    return normalized_data

# -------- DATABASE SETUP --------
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------- HOME ROUTE --------
@app.route('/')
def home():
    return redirect(url_for('login'))

# -------- SIGNUP --------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password)
            )
            conn.commit()
            conn.close()
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('auth/signup.html', error="Username already exists")

    return render_template('auth/signup.html')

# -------- LOGIN --------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = username
            return redirect(url_for('resume_form'))
        else:
            return render_template('auth/login.html', error="Invalid credentials")

    return render_template('auth/login.html')

# -------- RESUME FORM --------
@app.route('/resume', methods=['GET', 'POST'])
def resume_form():
    if 'user' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        submission_mode = request.form.get('submission_mode', 'preview')
        raw_data = {
            "name": request.form['name'],
            "role": request.form.get('role', ''),
            "email": request.form['email'],
            "phone": request.form['phone'],
            "linkedin": request.form['linkedin'],
            "github": request.form['github'],
            "profile_image_data": store_profile_image(request.form.get('profile_image_data', '')),
            "summary": request.form['summary'],
            "template": request.form['template'],
            "skills": {
                field: request.form.get(field, "")
                for field in SKILL_FIELDS
            },
            "education": parse_json_field("education_json", []),
            "projects": parse_json_field("projects_json", []),
            "work_experience": parse_json_field("work_experience_json", []),
            "certifications": parse_json_field("certifications_json", []),
            "achievements": parse_json_field("achievements_json", []),
            "custom_sections": parse_json_field("custom_sections_json", []),
        }

        data = normalize_resume_data(raw_data)

        # store temporarily in session
        session['resume_data'] = data

        if submission_mode == 'download':
            generate_pdf(build_pdf_html(data))
            return send_file("resume.pdf", as_attachment=True)

        return redirect(url_for('preview'))

    resume_data = normalize_resume_data(session.get('resume_data', {}))
    return render_template('resume/form.html', resume_data=resume_data, skill_fields=SKILL_FIELDS)

# -------- PREVIEW PAGE --------
@app.route('/preview')
def preview():
    if 'resume_data' not in session:
        return redirect(url_for('resume_form'))

    data = normalize_resume_data(session['resume_data'])
    session['resume_data'] = data
    return render_template('resume/preview.html', resume_data=data)

# -------- PDF DOWNLOAD --------
@app.route('/download')
def download_pdf():
    if 'resume_data' not in session:
        return redirect(url_for('resume_form'))

    data = normalize_resume_data(session['resume_data'])
    session['resume_data'] = data
    generate_pdf(build_pdf_html(data))

    return send_file("resume.pdf", as_attachment=True)

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('resume_data', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
