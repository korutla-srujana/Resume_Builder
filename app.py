from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, send_file, jsonify
import base64
import json
import os
from pathlib import Path
import re
import sqlite3
import uuid
from werkzeug.security import check_password_hash, generate_password_hash
from gap_analysis import analyze_gap, get_target_roles
from scoring_logic import calculate_ats_score as calculate_ats_score_result
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
        "target_role": clean_text(data.get("target_role", "")),
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


def get_db_connection():
    return sqlite3.connect('database.db')


def get_current_user_id():
    user_id = session.get('user_id')
    if user_id:
        return user_id
    return 0


def login_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if not session.get('user_id'):
            return redirect(url_for('login', next=request.path))
        return view_func(*args, **kwargs)

    return wrapped_view


def is_password_valid(stored_password, submitted_password):
    if not stored_password:
        return False

    if stored_password.startswith(("pbkdf2:", "scrypt:")):
        return check_password_hash(stored_password, submitted_password)

    # Backward compatibility for accounts created before password hashing.
    return stored_password == submitted_password


def safe_next_url(next_url):
    if next_url and next_url.startswith("/") and not next_url.startswith("//"):
        return next_url
    return url_for('dashboard')


def build_resume_form_data():
    raw_data = {
        "name": request.form.get('name', ''),
        "role": request.form.get('role', ''),
        "target_role": request.form.get('target_role', ''),
        "email": request.form.get('email', ''),
        "phone": request.form.get('phone', ''),
        "linkedin": request.form.get('linkedin', ''),
        "github": request.form.get('github', ''),
        "profile_image_data": store_profile_image(request.form.get('profile_image_data', '')),
        "summary": request.form.get('summary', ''),
        "template": request.form.get('template', 'classic'),
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
    return normalize_resume_data(raw_data)


def build_flat_resume_columns(data):
    skill_values = []
    for key in SKILL_FIELDS:
        label = SKILL_FIELDS[key]
        value = clean_text(data.get("skills", {}).get(key, ""))
        if value:
            skill_values.append(f"{label}: {value}")

    experience_values = []
    for item in data.get("work_experience", []):
        role = clean_text(item.get("role", ""))
        company = clean_text(item.get("company", ""))
        description = clean_text(item.get("description", ""))
        headline = " - ".join(part for part in [role, company] if part)
        combined = ": ".join(part for part in [headline, description] if part)
        if combined:
            experience_values.append(combined)

    education_values = []
    for item in data.get("education", []):
        degree = clean_text(item.get("degree", ""))
        specialization = clean_text(item.get("specialization", ""))
        institution = clean_text(item.get("institution", ""))
        combined = " - ".join(part for part in [degree or specialization, institution] if part)
        if combined:
            education_values.append(combined)

    project_values = []
    for item in data.get("projects", []):
        title = clean_text(item.get("title", ""))
        description = clean_text(item.get("description", ""))
        combined = ": ".join(part for part in [title, description] if part)
        if combined:
            project_values.append(combined)

    return {
        "name": clean_text(data.get("name", "")) or "Untitled Resume",
        "email": clean_text(data.get("email", "")),
        "phone": clean_text(data.get("phone", "")),
        "skills": "\n".join(skill_values),
        "experience": "\n".join(experience_values),
        "education": "\n".join(education_values),
        "projects": "\n".join(project_values),
    }


def save_resume_record(data):
    flat_data = build_flat_resume_columns(data)
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO resumes (
            user_id, name, email, phone, skills, experience, education, projects, resume_data, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """,
        (
            get_current_user_id(),
            flat_data["name"],
            flat_data["email"],
            flat_data["phone"],
            flat_data["skills"],
            flat_data["experience"],
            flat_data["education"],
            flat_data["projects"],
            json.dumps(data),
        ),
    )
    resume_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return resume_id


def build_resume_data_from_row(resume_row):
    if not resume_row:
        return normalize_resume_data({})

    resume_data_json = clean_text(resume_row[8]) if len(resume_row) > 8 else ""
    if resume_data_json:
        try:
            return normalize_resume_data(json.loads(resume_data_json))
        except json.JSONDecodeError:
            pass

    skills_text = clean_text(resume_row[4]) if len(resume_row) > 4 else ""
    return normalize_resume_data({
        "name": clean_text(resume_row[1]) if len(resume_row) > 1 else "",
        "email": clean_text(resume_row[2]) if len(resume_row) > 2 else "",
        "phone": clean_text(resume_row[3]) if len(resume_row) > 3 else "",
        "skills": {"languages": skills_text},
        "work_experience": [{"description": clean_text(resume_row[5])}] if len(resume_row) > 5 and clean_text(resume_row[5]) else [],
        "education": [{"institution": clean_text(resume_row[6])}] if len(resume_row) > 6 and clean_text(resume_row[6]) else [],
        "projects": [{"title": clean_text(resume_row[7])}] if len(resume_row) > 7 and clean_text(resume_row[7]) else [],
    })


def ensure_resume_columns(cursor):
    cursor.execute("PRAGMA table_info(resumes)")
    existing_columns = {column[1] for column in cursor.fetchall()}
    required_columns = {
        "user_id": "INTEGER",
        "name": "TEXT",
        "email": "TEXT",
        "phone": "TEXT",
        "skills": "TEXT",
        "experience": "TEXT",
        "education": "TEXT",
        "projects": "TEXT",
        "resume_data": "TEXT",
        "created_at": "TEXT",
        "updated_at": "TEXT",
    }

    for column_name, definition in required_columns.items():
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE resumes ADD COLUMN {column_name} {definition}")

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
    c.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            name TEXT,
            email TEXT,
            phone TEXT,
            skills TEXT,
            experience TEXT,
            education TEXT,
            projects TEXT,
            resume_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    ensure_resume_columns(c)
    conn.commit()
    conn.close()

init_db()

# -------- HOME ROUTE --------
@app.route('/')
@login_required
def home():
    session.pop('resume_data', None)
    session.pop('editing_resume_id', None)
    return render_template(
        'resume/form.html',
        resume=None,
        resume_data=normalize_resume_data({}),
        editing_resume_id=None,
        skill_fields=SKILL_FIELDS,
        gap_roles=get_target_roles(),
    )

# -------- SIGNUP --------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = clean_text(request.form.get('username', ''))
        password = request.form.get('password', '')

        if not username or not password:
            return render_template('auth/signup.html', error="Username and password are required")

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        try:
            c.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
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
    if session.get('user_id'):
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = clean_text(request.form.get('username', ''))
        password = request.form.get('password', '')
        next_page = safe_next_url(request.form.get('next') or request.args.get('next'))

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute(
            "SELECT id, username, password FROM users WHERE username=?",
            (username,)
        )
        user = c.fetchone()

        if user and is_password_valid(user[2], password):
            if user[2] == password:
                c.execute(
                    "UPDATE users SET password=? WHERE id=?",
                    (generate_password_hash(password), user[0])
                )
                conn.commit()

            conn.close()
            session.clear()
            session['user'] = user[1]
            session['user_id'] = user[0]
            return redirect(next_page)
        else:
            conn.close()
            return render_template('auth/login.html', error="Invalid credentials", next=request.args.get('next', ''))

    return render_template('auth/login.html', next=request.args.get('next', ''))

# -------- RESUME FORM --------
@app.route('/resume', methods=['GET', 'POST'])
@login_required
def resume_form():
    if request.method == 'GET':
        return redirect(url_for('home'))

    if request.method == 'POST':
        submission_mode = request.form.get('submission_mode', 'preview')
        data = build_resume_form_data()

        # store temporarily in session
        session['resume_data'] = data

        if submission_mode == 'download':
            generate_pdf(build_pdf_html(data))
            return send_file("resume.pdf", as_attachment=True)

        return redirect(url_for('preview'))


@app.route('/save_resume', methods=['POST'])
@login_required
def save_resume():
    data = build_resume_form_data()
    save_resume_record(data)
    session['resume_data'] = data
    session.pop('editing_resume_id', None)
    return redirect(url_for('dashboard'))


@app.route('/dashboard')
@login_required
def dashboard():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, created_at FROM resumes WHERE user_id=? ORDER BY id DESC",
        (get_current_user_id(),),
    )
    resumes = cursor.fetchall()
    conn.close()

    return render_template('dashboard.html', resumes=resumes)


@app.route('/edit_resume/<int:id>')
@login_required
def edit_resume(id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, email, phone, skills, experience, education, projects, resume_data
        FROM resumes
        WHERE id=? AND user_id=?
        """,
        (id, get_current_user_id()),
    )
    resume = cursor.fetchone()
    conn.close()

    if not resume:
        return redirect(url_for('dashboard'))

    resume_data = build_resume_data_from_row(resume)
    session['resume_data'] = resume_data
    session.pop('editing_resume_id', None)

    return render_template(
        'resume/form.html',
        resume=resume,
        resume_data=resume_data,
        editing_resume_id=None,
        skill_fields=SKILL_FIELDS,
        gap_roles=get_target_roles(),
    )

# -------- PREVIEW PAGE --------
@app.route('/preview')
@login_required
def preview():
    if 'resume_data' not in session:
        return redirect(url_for('home'))

    data = normalize_resume_data(session['resume_data'])
    session['resume_data'] = data
    return render_template('resume/preview.html', resume_data=data)

# -------- PDF DOWNLOAD --------
@app.route('/download')
@login_required
def download_pdf():
    if 'resume_data' not in session:
        return redirect(url_for('home'))

    data = normalize_resume_data(session['resume_data'])
    session['resume_data'] = data
    generate_pdf(build_pdf_html(data))

    return send_file("resume.pdf", as_attachment=True)


@app.route('/ats_score', methods=['POST'])
def ats_score():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid request payload"}), 400

    result = calculate_ats_score_result(payload)
    return jsonify(result)


@app.route('/gap_analysis', methods=['POST'])
def gap_analysis():
    payload = request.get_json(silent=True) or {}
    if not isinstance(payload, dict):
        return jsonify({"error": "Invalid request payload"}), 400

    try:
        result = analyze_gap(payload)
    except ValueError as error:
        return jsonify({"error": str(error)}), 400

    return jsonify(result)

# -------- LOGOUT --------
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
