from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
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

ROLE_PROFILES = {
    "web developer": {
        "aliases": ["frontend developer", "front end developer", "ui developer", "web designer"],
        "skills": ["html", "css", "javascript", "react"],
        "keywords": ["responsive", "frontend", "ui", "website", "api"],
    },
    "data analyst": {
        "aliases": ["business analyst", "reporting analyst", "analytics analyst"],
        "skills": ["python", "sql", "excel", "statistics"],
        "keywords": ["dashboard", "analysis", "reporting", "visualization", "insights"],
    },
    "software engineer": {
        "aliases": ["software developer", "application developer", "backend developer", "full stack developer"],
        "skills": ["java", "python", "dsa", "oops", "git"],
        "keywords": ["api", "backend", "testing", "scalable", "debugging"],
    },
}

TERM_DISPLAY_MAP = {
    "api": "API",
    "apis": "APIs",
    "aws": "AWS",
    "css": "CSS",
    "dsa": "DSA",
    "excel": "Excel",
    "flask": "Flask",
    "git": "Git",
    "html": "HTML",
    "javascript": "JavaScript",
    "oops": "OOPS",
    "python": "Python",
    "react": "React",
    "sql": "SQL",
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


def normalize_text_list(values):
    if not isinstance(values, list):
        return []

    normalized_values = []
    for value in values:
        cleaned = clean_text(value).lower()
        if cleaned:
            normalized_values.append(cleaned)
    return normalized_values


def tokenize_text(value):
    return re.findall(r"[a-zA-Z][a-zA-Z+#.\-]*", clean_text(value).lower())


def count_words(value):
    return len(tokenize_text(value))


def has_measurable_impact(value):
    return bool(re.search(r"\d|%|\bpercent\b|\bimprov\w*\b|\bincreas\w*\b|\breduc\w*\b", clean_text(value).lower()))


def format_term(value):
    cleaned = clean_text(value).lower()
    if not cleaned:
        return ""
    return TERM_DISPLAY_MAP.get(cleaned, cleaned.title())


def resolve_role_profile(role):
    cleaned_role = clean_text(role).lower()
    if not cleaned_role:
        return "", None

    best_role_name = ""
    best_profile = None
    best_score = 0
    role_tokens = set(tokenize_text(cleaned_role))

    for role_name, profile in ROLE_PROFILES.items():
        aliases = [role_name, *profile.get("aliases", [])]
        for alias in aliases:
            alias_text = alias.lower()
            alias_tokens = set(tokenize_text(alias_text))

            if cleaned_role == alias_text:
                return role_name, profile

            score = 0
            if alias_text in cleaned_role or cleaned_role in alias_text:
                score = max(score, 80)

            overlap = len(role_tokens & alias_tokens)
            if overlap:
                score = max(score, overlap * 20)

            if score > best_score:
                best_score = score
                best_role_name = role_name
                best_profile = profile

    if best_score >= 20:
        return best_role_name, best_profile

    return "", None


def calculate_ats_score(payload):
    role = clean_text(payload.get("role", ""))
    summary = clean_text(payload.get("summary", ""))
    skills = normalize_text_list(payload.get("skills", []))
    sections = normalize_text_list(payload.get("sections", []))
    project_descriptions = normalize_text_list(payload.get("project_descriptions", []))
    work_descriptions = normalize_text_list(payload.get("work_descriptions", []))
    achievement_texts = normalize_text_list(payload.get("achievement_texts", []))

    education_count = int(payload.get("education_count", 0) or 0)
    project_count = int(payload.get("project_count", 0) or 0)
    work_count = int(payload.get("work_experience_count", 0) or 0)
    certification_count = int(payload.get("certification_count", 0) or 0)
    achievement_count = int(payload.get("achievement_count", 0) or 0)

    unique_skills = sorted(set(skills))
    unique_sections = set(sections)
    matched_role_name, matched_role_profile = resolve_role_profile(role)
    expected_skills = matched_role_profile.get("skills", []) if matched_role_profile else []
    matched_skills = [skill for skill in expected_skills if skill in unique_skills]
    missing_skills = [skill for skill in expected_skills if skill not in unique_skills]

    analysis_text_parts = [summary, *project_descriptions, *work_descriptions, *achievement_texts]
    analysis_text = " ".join(part for part in analysis_text_parts if part)
    analysis_tokens = set(tokenize_text(analysis_text))
    role_tokens = set(tokenize_text(role))

    section_score = 0
    section_notes = []
    if role:
        section_score += 4
        section_notes.append("role title")
    if summary:
        section_score += 4
        section_notes.append("summary")
    if unique_skills:
        section_score += 4
        section_notes.append("skills")
    if education_count or "education" in unique_sections:
        section_score += 4
        section_notes.append("education")
    if project_count or work_count:
        section_score += 4
        section_notes.append("projects/work experience")

    skill_score = round((len(matched_skills) / len(expected_skills)) * 40) if expected_skills else 22

    keyword_pool = set(expected_skills)
    keyword_pool.update(role_tokens)
    if matched_role_profile:
        keyword_pool.update(matched_role_profile.get("keywords", []))

    keyword_matches = len(keyword_pool & (analysis_tokens | set(unique_skills) | unique_sections))
    keyword_score = round((keyword_matches / len(keyword_pool)) * 20) if keyword_pool else 10

    summary_word_count = count_words(summary)
    detail_word_counts = [count_words(text) for text in [*project_descriptions, *work_descriptions] if text]
    richest_detail = max(detail_word_counts, default=0)
    measurable_impact = has_measurable_impact(analysis_text)

    completeness_score = 0
    if summary_word_count >= 20:
        completeness_score += 5
    elif summary:
        completeness_score += 3

    if len(unique_skills) >= 6:
        completeness_score += 5
    elif len(unique_skills) >= 4:
        completeness_score += 3
    elif len(unique_skills) >= 2:
        completeness_score += 2

    if richest_detail >= 18:
        completeness_score += 5
    elif richest_detail >= 10:
        completeness_score += 3

    if measurable_impact:
        completeness_score += 5

    if certification_count or achievement_count:
        completeness_score = min(completeness_score + 2, 20)

    score = min(section_score + skill_score + keyword_score + completeness_score, 100)

    breakdown = [
        {
            "label": "Section Presence",
            "score": section_score,
            "max_score": 20,
            "detail": f"Found {', '.join(section_notes) if section_notes else 'very few core sections'}."
        },
        {
            "label": "Skill Match",
            "score": skill_score,
            "max_score": 40,
            "detail": (
                f"Matched {len(matched_skills)} of {len(expected_skills)} role-based skills for {matched_role_name.title()}."
                if expected_skills
                else "Used a general analysis because the role did not map cleanly to a target profile."
            ),
        },
        {
            "label": "Keywords",
            "score": keyword_score,
            "max_score": 20,
            "detail": "Checked whether role keywords appear across summary, projects, work, and skills.",
        },
        {
            "label": "Completeness",
            "score": completeness_score,
            "max_score": 20,
            "detail": "Reviewed summary depth, skill breadth, detail level, and measurable impact.",
        },
    ]

    analysis_notes = []
    if matched_role_name:
        analysis_notes.append(f"Target role matched to {matched_role_name.title()}.")
    elif role:
        analysis_notes.append("Role could not be matched strongly, so this score uses a more general ATS analysis.")

    if matched_skills:
        analysis_notes.append(f"Role-aligned skills found: {', '.join(format_term(skill) for skill in matched_skills[:5])}.")

    if not missing_skills:
        analysis_notes.append("No major role-based skill gaps were detected.")

    if summary_word_count and summary_word_count < 20:
        analysis_notes.append("Your summary is present but still quite short for keyword coverage.")

    if richest_detail < 10:
        analysis_notes.append("Project and work descriptions need more depth to help ATS and recruiters understand impact.")

    if not measurable_impact:
        analysis_notes.append("No measurable outcomes were found in the summary, projects, work, or achievements.")

    suggestions = []
    if not role:
        suggestions.append("Add a clear target role in the Role / Job Title field.")
    elif not matched_role_name:
        suggestions.append("Use a more specific job title so ATS can match your resume to a target role more accurately.")

    if missing_skills:
        suggestions.append(f"Add role-specific skills such as {', '.join(format_term(skill) for skill in missing_skills[:3])}.")

    if summary_word_count < 20:
        suggestions.append("Expand the summary with target keywords, strengths, and the type of role you want.")

    if richest_detail < 10:
        suggestions.append("Rewrite project or work descriptions with stronger action verbs, tools used, and clear outcomes.")

    if not measurable_impact:
        suggestions.append("Add numbers where possible, such as percentages, team size, users, performance gains, or project scale.")

    if not (project_count or work_count):
        suggestions.append("Include at least one project or work experience entry to improve ATS confidence.")

    if "education" not in unique_sections and not education_count:
        suggestions.append("Include an education section for better completeness.")

    if not suggestions:
        suggestions.append("Your resume is strong overall. Tailor keywords and project bullets for each application.")

    return {
        "score": score,
        "matched_role": matched_role_name.title() if matched_role_name else "",
        "missing_skills": [format_term(skill) for skill in missing_skills],
        "suggestions": suggestions[:5],
        "breakdown": breakdown,
        "analysis_notes": analysis_notes[:5],
    }


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
@page {
    size: A4;
    margin: 0;
}

html, body {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #ffffff;
    overflow: hidden;
}
body.pdf-export-page {
    margin: 0 !important;
    padding: 0 !important;
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
    width: 100%;
    height: 100%;
    margin: 0 !important;
    padding: 0 !important;
    background: #ffffff;
    overflow: hidden;
    position: relative;
}
.pdf-stage {
    width: 100%;
    height: 100%;
    overflow: hidden;
}
.pdf-shell .resume-sheet {
    box-sizing: border-box;
    width: 100%;
    min-height: 100%;
    max-width: none;
    margin: 0 !important;
    border-radius: 0 !important;
    box-shadow: none !important;
}
.pdf-export-page .resume-sheet {
    padding: 20px 22px 22px !important;
}
.pdf-export-page .resume-header {
    padding-bottom: 12px !important;
}
.pdf-export-page .resume-header h1 {
    font-size: 2rem !important;
}
.pdf-export-page .resume-role {
    margin-top: 4px !important;
    font-size: 0.88rem !important;
}
.pdf-export-page .resume-meta {
    margin-top: 8px !important;
    gap: 6px 10px !important;
}
.pdf-export-page .resume-meta__item {
    font-size: 0.72rem !important;
}
.pdf-export-page .resume-section {
    padding-top: 8px !important;
}
.pdf-export-page .resume-section + .resume-section {
    margin-top: 8px !important;
}
.pdf-export-page .resume-section h2 {
    padding-bottom: 6px !important;
    font-size: 0.98rem !important;
}
.pdf-export-page .resume-section p {
    margin-top: 7px !important;
    line-height: 1.45 !important;
    font-size: 0.84rem !important;
}
.pdf-export-page .resume-list {
    gap: 8px !important;
    margin-top: 8px !important;
}
.pdf-export-page .resume-item {
    gap: 3px !important;
}
.pdf-export-page .resume-item h3 {
    font-size: 0.88rem !important;
    line-height: 1.3 !important;
}
.pdf-export-page .resume-item__subtitle,
.pdf-export-page .resume-item__meta,
.pdf-export-page .resume-item__date,
.pdf-export-page .resume-item__aside-meta,
.pdf-export-page .skills-group,
.pdf-export-page .contact-list__item,
.pdf-export-page .resume-bullets li {
    font-size: 0.76rem !important;
    line-height: 1.35 !important;
}
.pdf-export-page .resume-item__headline {
    gap: 10px !important;
}
.pdf-export-page .resume-bullets {
    gap: 4px !important;
    margin: 8px 0 0 !important;
    padding-left: 18px !important;
}
.pdf-export-page .skills-group-list {
    display: grid !important;
    gap: 6px !important;
}
.pdf-export-page .skills-group {
    margin: 0 !important;
}
#pdf-link-metadata {
    display: none !important;
}

@media print {
    html,
    body,
    body.pdf-export-page {
        margin: 0 !important;
        padding: 0 !important;
        width: 100% !important;
        height: 100% !important;
        overflow: hidden !important;
        background: #ffffff !important;
    }

    .pdf-shell {
        width: 100% !important;
        height: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }

    .pdf-stage {
        width: 100% !important;
        height: 100% !important;
        overflow: hidden !important;
    }

    .pdf-shell .resume-sheet {
        width: 100% !important;
        max-width: 100% !important;
        margin: 0 !important;
    }
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


@app.route('/ats_score', methods=['POST'])
def ats_score():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid request payload"}), 400

    result = calculate_ats_score(payload)
    return jsonify(result)

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('resume_data', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)
