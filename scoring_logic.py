import re


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

GENERAL_ANALYSIS_MESSAGE = "Role not specified \u2013 showing general analysis"


def clean_text(value):
    if isinstance(value, str):
        return value.strip()
    return ""


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
            "detail": f"Found {', '.join(section_notes) if section_notes else 'very few core sections'}.",
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
    else:
        analysis_notes.append(f"{GENERAL_ANALYSIS_MESSAGE}.")

    if matched_skills:
        analysis_notes.append(f"Role-aligned skills found: {', '.join(format_term(skill) for skill in matched_skills[:5])}.")

    if matched_role_name and not missing_skills:
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

    missing_skills_message = (
        "No major role-based skill gaps were detected."
        if matched_role_name
        else GENERAL_ANALYSIS_MESSAGE
    )

    return {
        "score": score,
        "matched_role": matched_role_name.title() if matched_role_name else "",
        "missing_skills": [format_term(skill) for skill in missing_skills],
        "missing_skills_message": missing_skills_message,
        "suggestions": suggestions[:5],
        "breakdown": breakdown,
        "analysis_notes": analysis_notes[:5],
    }
