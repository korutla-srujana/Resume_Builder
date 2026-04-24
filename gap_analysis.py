import re


ROLE_SKILLS = {
    "Frontend Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "TypeScript",
        "React",
        "Next.js",
        "Redux",
        "Tailwind CSS",
        "Bootstrap",
        "REST API",
        "Responsive Design",
        "Git",
        "Webpack",
        "Vite",
        "Accessibility",
    ],
    "Backend Developer": [
        "Python",
        "Java",
        "Node.js",
        "Spring Boot",
        "Django",
        "Flask",
        "Express.js",
        "REST API",
        "GraphQL",
        "SQL",
        "PostgreSQL",
        "MongoDB",
        "Authentication",
        "Microservices",
        "Docker",
        "Git",
    ],
    "Full Stack Developer": [
        "HTML",
        "CSS",
        "JavaScript",
        "TypeScript",
        "React",
        "Node.js",
        "Express.js",
        "REST API",
        "SQL",
        "MongoDB",
        "Git",
        "Docker",
        "Deployment",
        "System Design",
        "Testing",
    ],
    "Software Engineer": [
        "Python",
        "Java",
        "Data Structures",
        "Algorithms",
        "OOP",
        "Git",
        "REST API",
        "SQL",
        "System Design",
        "Testing",
        "Debugging",
        "CI/CD",
        "Docker",
        "Problem Solving",
    ],
    "Data Analyst": [
        "Python",
        "Pandas",
        "NumPy",
        "SQL",
        "Excel",
        "Power BI",
        "Tableau",
        "Data Cleaning",
        "Data Visualization",
        "Statistics",
        "Dashboarding",
        "Business Insights",
        "A/B Testing",
    ],
    "Data Scientist": [
        "Python",
        "Machine Learning",
        "Deep Learning",
        "TensorFlow",
        "PyTorch",
        "Pandas",
        "NumPy",
        "SQL",
        "Data Visualization",
        "Statistics",
        "Feature Engineering",
        "NLP",
        "Model Evaluation",
        "Experimentation",
    ],
    "Machine Learning Engineer": [
        "Python",
        "Machine Learning",
        "Deep Learning",
        "TensorFlow",
        "PyTorch",
        "MLOps",
        "Docker",
        "Kubernetes",
        "AWS",
        "Feature Engineering",
        "Model Deployment",
        "CI/CD",
        "Data Pipelines",
        "Monitoring",
    ],
    "DevOps Engineer": [
        "Docker",
        "Kubernetes",
        "Jenkins",
        "GitHub Actions",
        "CI/CD",
        "Linux",
        "AWS",
        "Terraform",
        "Monitoring",
        "Shell Scripting",
        "Ansible",
        "Networking",
        "Security",
        "Logging",
    ],
    "Cloud Engineer": [
        "AWS",
        "Azure",
        "GCP",
        "Docker",
        "Kubernetes",
        "CI/CD",
        "Terraform",
        "Linux",
        "Networking",
        "Security",
        "IAM",
        "Serverless",
        "Monitoring",
        "Infrastructure as Code",
    ],
    "Cybersecurity Analyst": [
        "Network Security",
        "Cryptography",
        "Penetration Testing",
        "SIEM",
        "Firewalls",
        "Ethical Hacking",
        "Incident Response",
        "Vulnerability Assessment",
        "IAM",
        "Security Monitoring",
        "Threat Intelligence",
        "Risk Assessment",
        "Linux",
    ],
    "Mobile App Developer": [
        "Java",
        "Kotlin",
        "Swift",
        "Flutter",
        "React Native",
        "REST API",
        "UI Design",
        "App Deployment",
        "Firebase",
        "Android",
        "iOS",
        "Git",
        "Testing",
    ],
    "UI/UX Designer": [
        "Figma",
        "Wireframing",
        "Prototyping",
        "User Research",
        "Design Systems",
        "Accessibility",
        "Usability Testing",
        "Information Architecture",
        "Interaction Design",
        "Visual Design",
        "Responsive Design",
        "Design Thinking",
        "Journey Mapping",
    ],
    "QA Engineer": [
        "Manual Testing",
        "Automation Testing",
        "Selenium",
        "Cypress",
        "API Testing",
        "Postman",
        "Regression Testing",
        "Test Cases",
        "Bug Tracking",
        "CI/CD",
        "Performance Testing",
        "JMeter",
        "Git",
        "SQL",
    ],
    "Product Manager": [
        "Roadmapping",
        "User Stories",
        "Agile",
        "Scrum",
        "Stakeholder Management",
        "Market Research",
        "Product Strategy",
        "Analytics",
        "A/B Testing",
        "Prioritization",
        "Go-to-Market",
        "Communication",
        "Backlog Management",
    ],
    "Business Analyst": [
        "Requirements Gathering",
        "Stakeholder Management",
        "SQL",
        "Excel",
        "Power BI",
        "Process Mapping",
        "Documentation",
        "Data Analysis",
        "User Stories",
        "Agile",
        "UAT",
        "Communication",
        "Reporting",
    ],
    "AI Engineer": [
        "Python",
        "Machine Learning",
        "Deep Learning",
        "LLMs",
        "Prompt Engineering",
        "RAG",
        "Vector Databases",
        "PyTorch",
        "TensorFlow",
        "Model Deployment",
        "API Integration",
        "MLOps",
        "Docker",
        "Cloud Services",
    ],
}

SKILL_ALIASES = {
    "A/B Testing": ["ab testing", "a b testing"],
    "API Integration": ["api integrations", "integrating apis"],
    "App Deployment": ["app publishing", "mobile deployment"],
    "Automation Testing": ["test automation"],
    "Business Insights": ["business intelligence", "insights"],
    "CI/CD": ["cicd", "continuous integration", "continuous delivery", "continuous deployment"],
    "Cloud Services": ["cloud", "cloud platforms"],
    "Computer Vision": ["cv"],
    "Data Cleaning": ["data wrangling"],
    "Data Structures": ["dsa"],
    "Data Visualization": ["visualization", "visualisation"],
    "Deep Learning": ["dl"],
    "Express.js": ["express", "expressjs"],
    "Feature Engineering": ["feature selection"],
    "Firebase": ["firebase services"],
    "GitHub Actions": ["github action"],
    "GraphQL": ["graph ql"],
    "HTML": ["html5"],
    "IAM": ["identity and access management"],
    "Infrastructure as Code": ["iac"],
    "JavaScript": ["js"],
    "Kubernetes": ["k8s"],
    "Large Language Models": ["llm", "llms"],
    "LLMs": ["llm", "large language model", "large language models"],
    "Machine Learning": ["ml"],
    "MLOps": ["ml ops"],
    "MongoDB": ["mongo"],
    "Natural Language Processing": ["nlp"],
    "Next.js": ["nextjs", "next js"],
    "Node.js": ["node", "nodejs", "node js"],
    "OOP": ["oops", "object oriented programming"],
    "PostgreSQL": ["postgres", "postgresql"],
    "Power BI": ["powerbi"],
    "Problem Solving": ["problem-solving"],
    "PyTorch": ["pytorch"],
    "RAG": ["retrieval augmented generation"],
    "React Native": ["reactnative"],
    "REST API": ["rest apis", "restful api", "restful apis"],
    "Responsive Design": ["responsive ui"],
    "SIEM": ["security information and event management"],
    "Shell Scripting": ["bash", "shell"],
    "SQL": ["mysql", "sql databases"],
    "Tailwind CSS": ["tailwind", "tailwindcss"],
    "TensorFlow": ["tensorflow"],
    "TypeScript": ["ts"],
    "UI Design": ["user interface design"],
    "UAT": ["user acceptance testing"],
    "UI/UX Designer": ["ui ux"],
    "Usability Testing": ["usability studies"],
    "Vector Databases": ["vector database"],
    "Vulnerability Assessment": ["vapt"],
    "Wireframing": ["wireframes"],
}

CATEGORY_SKILLS = {
    "frontend": {"HTML", "CSS", "JavaScript", "TypeScript", "React", "Next.js", "Redux", "Tailwind CSS", "Bootstrap", "Responsive Design", "Accessibility", "Vite", "Webpack"},
    "backend": {"Python", "Java", "Node.js", "Spring Boot", "Django", "Flask", "Express.js", "REST API", "GraphQL", "SQL", "PostgreSQL", "MongoDB", "Authentication", "Microservices", "System Design", "API Testing", "API Integration"},
    "cloud": {"AWS", "Azure", "GCP", "Docker", "Kubernetes", "CI/CD", "Terraform", "Linux", "IAM", "Serverless", "Monitoring", "Infrastructure as Code", "Cloud Services"},
    "data": {"Python", "Pandas", "NumPy", "SQL", "Excel", "Power BI", "Tableau", "Data Cleaning", "Data Visualization", "Statistics", "Dashboarding", "Business Insights", "A/B Testing", "Machine Learning", "Feature Engineering"},
    "security": {"Network Security", "Cryptography", "Penetration Testing", "SIEM", "Firewalls", "Ethical Hacking", "Incident Response", "Vulnerability Assessment", "Threat Intelligence", "Risk Assessment", "Security Monitoring", "Security"},
    "mobile": {"Java", "Kotlin", "Swift", "Flutter", "React Native", "Firebase", "Android", "iOS", "App Deployment", "UI Design"},
    "testing": {"Manual Testing", "Automation Testing", "Selenium", "Cypress", "API Testing", "Postman", "Regression Testing", "Performance Testing", "JMeter", "Test Cases", "Bug Tracking", "Testing"},
    "design": {"Figma", "Wireframing", "Prototyping", "User Research", "Design Systems", "Accessibility", "Usability Testing", "Information Architecture", "Interaction Design", "Visual Design", "Design Thinking", "Journey Mapping"},
    "ai": {"Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "LLMs", "Prompt Engineering", "RAG", "Vector Databases", "MLOps", "Model Deployment", "NLP"},
}


def clean_text(value):
    if isinstance(value, str):
        return value.strip()
    return ""


def normalize_phrase(value):
    lowered = clean_text(value).lower()
    normalized = re.sub(r"[^a-z0-9+#]+", " ", lowered)
    return re.sub(r"\s+", " ", normalized).strip()


def get_target_roles():
    return list(ROLE_SKILLS.keys())


def build_resume_text(payload):
    parts = []
    summary_fields = [
        payload.get("role", ""),
        payload.get("summary", ""),
        payload.get("resume_text", ""),
    ]
    parts.extend(summary_fields)
    parts.extend(payload.get("skills", []) if isinstance(payload.get("skills"), list) else [])
    parts.extend(payload.get("project_descriptions", []) if isinstance(payload.get("project_descriptions"), list) else [])
    parts.extend(payload.get("work_descriptions", []) if isinstance(payload.get("work_descriptions"), list) else [])
    parts.extend(payload.get("achievement_texts", []) if isinstance(payload.get("achievement_texts"), list) else [])
    parts.extend(payload.get("certification_titles", []) if isinstance(payload.get("certification_titles"), list) else [])
    parts.extend(payload.get("custom_section_content", []) if isinstance(payload.get("custom_section_content"), list) else [])
    return " ".join(clean_text(part) for part in parts if clean_text(part))


def get_all_known_skills():
    all_skills = set()
    for skills in ROLE_SKILLS.values():
        all_skills.update(skills)
    return sorted(all_skills)


def extract_resume_skills(resume_text):
    normalized_text = f" {normalize_phrase(resume_text)} "
    detected_skills = set()

    for skill in get_all_known_skills():
        aliases = [skill, *SKILL_ALIASES.get(skill, [])]
        normalized_aliases = {normalize_phrase(alias) for alias in aliases if normalize_phrase(alias)}
        if any(f" {alias} " in normalized_text for alias in normalized_aliases):
            detected_skills.add(skill)

    return detected_skills


def build_recommendations(role, missing_skills, matched_skills):
    missing_set = set(missing_skills)
    recommendations = []

    def missing_from(category_name):
        return sorted(missing_set & CATEGORY_SKILLS[category_name])

    frontend_missing = missing_from("frontend")
    backend_missing = missing_from("backend")
    cloud_missing = missing_from("cloud")
    data_missing = missing_from("data")
    security_missing = missing_from("security")
    mobile_missing = missing_from("mobile")
    testing_missing = missing_from("testing")
    design_missing = missing_from("design")
    ai_missing = missing_from("ai")

    if len(frontend_missing) >= 3:
        recommendations.append("Strengthen frontend depth by building 2 responsive UI projects with modern state management and accessibility improvements.")
    if len(backend_missing) >= 3:
        recommendations.append("Add backend experience through API development, authentication flows, and database-backed CRUD projects.")
    if len(cloud_missing) >= 3:
        recommendations.append("Cover cloud and DevOps basics by deploying one project with Docker, CI/CD, and an AWS or Azure workflow.")
    if len(data_missing) >= 3:
        recommendations.append("Practice analytics with one dashboard project that includes SQL, data cleaning, and clear business insights.")
    if len(security_missing) >= 3:
        recommendations.append("Build cybersecurity fundamentals with labs on threat detection, incident response, and vulnerability assessment.")
    if len(mobile_missing) >= 3:
        recommendations.append("Create a mobile app with API integration, polished UI flows, and a publish-ready deployment pipeline.")
    if len(testing_missing) >= 3:
        recommendations.append("Improve quality coverage by adding automated test suites, API validation, and regression test documentation.")
    if len(design_missing) >= 3:
        recommendations.append("Improve product design skills with user research, wireframes, and a reusable design system case study.")
    if len(ai_missing) >= 3:
        recommendations.append("Build an AI portfolio piece that includes prompt design, model integration, and deployment-ready evaluation.")

    if {"REST API", "GraphQL", "API Testing", "API Integration"} & missing_set:
        recommendations.append("Add hands-on API work so recruiters can see real integration or service design experience.")
    if {"Git", "GitHub Actions", "CI/CD"} & missing_set:
        recommendations.append("Show stronger engineering workflow habits with Git, pull-request collaboration, and an automated delivery pipeline.")
    if {"AWS", "Azure", "GCP"} & missing_set:
        recommendations.append("Learn one major cloud platform and document a deployment project with monitoring and cost-aware architecture.")

    if not recommendations:
        if missing_skills:
            top_missing = ", ".join(missing_skills[:3])
            recommendations.append(f"Prioritize the top missing skills for {role}: {top_missing}.")
        else:
            recommendations.append(f"Your resume already covers the core skill areas for {role}; focus on stronger project outcomes and measurable impact.")

    if matched_skills:
        recommendations.append(f"Keep highlighting your matched strengths: {', '.join(matched_skills[:3])}.")

    return recommendations[:5]


def analyze_gap(payload):
    target_role = clean_text(payload.get("target_role", ""))
    if not target_role:
        raise ValueError("Please select a target role for gap analysis")

    if target_role not in ROLE_SKILLS:
        raise ValueError("Selected role is not available for gap analysis")

    resume_text = build_resume_text(payload)
    resume_skills = extract_resume_skills(resume_text)
    required_skills = ROLE_SKILLS[target_role]
    matched_skills = [skill for skill in required_skills if skill in resume_skills]
    missing_skills = [skill for skill in required_skills if skill not in resume_skills]
    gap_percentage = round(len(missing_skills) / len(required_skills), 2) if required_skills else 0.0

    return {
        "role": target_role,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "gap_percentage": gap_percentage,
        "recommendations": build_recommendations(target_role, missing_skills, matched_skills),
    }
