import re
import io
from typing import Dict, List, Any, Optional
import pypdf
import docx

# Comprehensive Tech & Professional Skills
KNOWN_SKILLS = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go", "Golang", 
    "Rust", "Ruby", "PHP", "Swift", "Kotlin", "Dart", "R", "SQL", "HTML", "CSS", "Bash", "Shell",
    # Frontend
    "React", "React.js", "Next.js", "Vue", "Vue.js", "Angular", "Svelte", "Redux", 
    "Tailwind CSS", "Bootstrap", "Material UI", "HTML5", "CSS3", "Webpack", "Vite",
    # Backend & Frameworks
    "FastAPI", "Flask", "Django", "Node.js", "Express", "Express.js", "NestJS", 
    "Spring", "Spring Boot", "ASP.NET", ".NET", "Ruby on Rails", "REST API", "RESTful API", 
    "GraphQL", "gRPC", "Microservices", "WebSockets",
    # Databases & Caching
    "PostgreSQL", "MySQL", "SQLite", "MongoDB", "Redis", "Elasticsearch", "DynamoDB", 
    "Cassandra", "Firebase", "Supabase", "SQL Server", "Oracle",
    # Cloud, DevOps & Tools
    "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", 
    "CI/CD", "GitHub Actions", "Jenkins", "Terraform", "Ansible", "Git", "GitHub", "GitLab", 
    "Linux", "Nginx", "Apache", "Kafka", "RabbitMQ", "Celery",
    # AI, ML & Data
    "Machine Learning", "Deep Learning", "Artificial Intelligence", "NLP", "LLM", 
    "PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy", "OpenCV", "Data Analysis", 
    "Data Science", "Tableau", "Power BI",
    # Testing & Practices
    "Unit Testing", "PyTest", "Jest", "Cypress", "Selenium", "Agile", "Scrum", 
    "TDD", "System Design", "Design Patterns", "Clean Architecture"
]

ACTION_VERBS = [
    "accelerated", "achieved", "administered", "analyzed", "architected", "automated", 
    "built", "collaborated", "configured", "created", "decreased", "delivered", "deployed", 
    "designed", "developed", "devised", "directed", "engineered", "enhanced", "established", 
    "executed", "expanded", "generated", "implemented", "improved", "increased", "initiated", 
    "integrated", "introduced", "launched", "lead", "led", "managed", "maximized", "mentored", 
    "migrated", "modernized", "optimized", "orchestrated", "overhauled", "pioneered", 
    "produced", "reduced", "refactored", "resolved", "revamped", "scaled", "simplified", 
    "spearheaded", "standardized", "streamlined", "strengthened", "transformed", "upgraded"
]

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from PDF, DOCX, or TXT file bytes."""
    filename_lower = filename.lower()
    text = ""
    
    if filename_lower.endswith(".pdf"):
        try:
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            text = f"[PDF extraction notice: {str(e)}]"
            
    elif filename_lower.endswith(".docx"):
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            for p in doc.paragraphs:
                if p.text:
                    text += p.text + "\n"
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text:
                            text += cell.text + " "
                    text += "\n"
        except Exception as e:
            text = f"[DOCX extraction notice: {str(e)}]"
            
    else:
        # Fallback to plain text
        try:
            text = file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            text = file_bytes.decode("latin-1", errors="ignore")

    return text.strip()

def extract_contact_info(text: str) -> Dict[str, Optional[str]]:
    """Extract email, phone, links, and candidate name."""
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text)
    email = email_match.group(0) if email_match else None

    phone_match = re.search(r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{10,13}', text)
    phone = phone_match.group(0) if phone_match else None

    # Detect Candidate Name from top lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    candidate_name = None
    ignored_keywords = ["resume", "curriculum", "vitae", "cv", "page", "email", "phone", "profile", "contact"]
    
    for line in lines[:5]:
        if "@" in line or any(d in line for d in "0123456789+"):
            continue
        cleaned = re.sub(r'[^a-zA-Z\s]', '', line).strip()
        words = cleaned.split()
        if 1 <= len(words) <= 4 and len(cleaned) < 35:
            if not any(k in cleaned.lower() for k in ignored_keywords):
                candidate_name = cleaned.title()
                break

    return {
        "candidate_name": candidate_name,
        "email": email,
        "phone": phone
    }

def detect_sections(text: str) -> Dict[str, bool]:
    """Check for standard resume sections."""
    text_lower = text.lower()
    return {
        "summary": bool(re.search(r'\b(summary|objective|profile|about\s+me|professional\s+summary)\b', text_lower)),
        "skills": bool(re.search(r'\b(skills|technical\s+skills|core\s+competencies|technologies|tools)\b', text_lower)),
        "experience": bool(re.search(r'\b(experience|work\s+experience|employment|work\s+history|professional\s+experience)\b', text_lower)),
        "education": bool(re.search(r'\b(education|academic|qualifications|degrees|university|college)\b', text_lower)),
        "projects": bool(re.search(r'\b(projects|personal\s+projects|academic\s+projects|portfolio)\b', text_lower)),
        "certifications": bool(re.search(r'\b(certifications|certificates|licenses|achievements|awards)\b', text_lower))
    }

def extract_skills_from_text(text: str) -> List[str]:
    """Find known technical and professional skills in the text."""
    found = []
    text_lower = f" {text.lower()} "
    for skill in KNOWN_SKILLS:
        pattern = r'(?<![a-zA-Z0-9])' + re.escape(skill.lower()) + r'(?![a-zA-Z0-9])'
        if re.search(pattern, text_lower):
            found.append(skill)
    return list(dict.fromkeys(found))

def analyze_experience_bullets(text: str) -> Dict[str, Any]:
    """Analyze action verbs and quantifiable results."""
    lines = [l.strip() for l in text.split('\n') if len(l.strip()) > 15]
    
    action_verb_count = 0
    quantifiable_count = 0
    sample_weak_bullets = []
    sample_strong_bullets = []

    metric_regex = re.compile(r'(\d+[\d,]*%|\$\d+[\d,]*|₹\d+[\d,]*|\b\d+\+\b|\b\d+\s*(?:users|clients|records|teams|members|requests|ms|seconds|hours|x)\b)', re.IGNORECASE)

    for line in lines:
        words = re.findall(r'[a-zA-Z]+', line)
        if not words:
            continue
        first_word = words[0].lower()
        has_verb = first_word in ACTION_VERBS
        has_metric = bool(metric_regex.search(line))

        if has_verb:
            action_verb_count += 1
        if has_metric:
            quantifiable_count += 1
            if len(sample_strong_bullets) < 3:
                sample_strong_bullets.append(line)
        elif not has_verb and len(line) > 25 and len(sample_weak_bullets) < 3:
            # Candidate for improvement
            if not any(header in line.lower() for header in ["education", "experience", "projects", "skills"]):
                sample_weak_bullets.append(line)

    return {
        "action_verb_count": action_verb_count,
        "quantifiable_count": quantifiable_count,
        "sample_weak_bullets": sample_weak_bullets,
        "sample_strong_bullets": sample_strong_bullets
    }

def analyze_resume_ats(
    file_bytes: bytes,
    filename: str,
    job_description: Optional[str] = None
) -> Dict[str, Any]:
    """Main ATS analysis engine."""
    extracted_text = extract_text_from_file(file_bytes, filename)
    
    # Check if text was parsed
    word_count = len(extracted_text.split())
    contact = extract_contact_info(extracted_text)
    candidate_name = contact["candidate_name"] or filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
    sections = detect_sections(extracted_text)
    resume_skills = extract_skills_from_text(extracted_text)
    bullet_analysis = analyze_experience_bullets(extracted_text)

    # Job description comparison
    has_jd = bool(job_description and len(job_description.strip()) > 20)
    jd_skills = extract_skills_from_text(job_description) if has_jd else []
    
    if has_jd and jd_skills:
        matched_skills = [s for s in jd_skills if s in resume_skills]
        missing_skills = [s for s in jd_skills if s not in resume_skills]
        keyword_match = min(100, max(20, int((len(matched_skills) / max(len(jd_skills), 1)) * 100)))
        skills_match = min(100, max(25, int((len(matched_skills) / max(len(jd_skills), 1)) * 95) + 5))
    else:
        # Standalone ATS check
        matched_skills = resume_skills
        # Identify recommended complementary skills based on what's present
        complementary_pool = ["Docker", "AWS", "CI/CD", "REST API", "Kubernetes", "Git", "Unit Testing", "System Design", "PostgreSQL", "Redis"]
        missing_skills = [s for s in complementary_pool if s not in resume_skills][:4]
        
        # Keyword score based on skill depth
        keyword_match = min(95, max(35, len(resume_skills) * 8 + 20))
        skills_match = min(95, max(40, len(resume_skills) * 9 + 15))

    # Structure Score (out of 100)
    section_score = (
        (25 if sections["skills"] else 0) +
        (25 if sections["experience"] else 0) +
        (20 if sections["education"] else 0) +
        (15 if sections["projects"] else 0) +
        (15 if sections["summary"] else 0)
    )
    structure_score = min(100, max(30, section_score))

    # Experience Relevance & Quality
    q_count = bullet_analysis["quantifiable_count"]
    v_count = bullet_analysis["action_verb_count"]
    experience_score = min(96, max(30, 40 + (q_count * 12) + (v_count * 5)))

    # Education Score
    has_degree = bool(re.search(r'\b(bachelor|master|b\.tech|m\.tech|b\.s\.|m\.s\.|degree|b\.sc|m\.sc|phd|diploma)\b', extracted_text.lower()))
    education_score = 90 if has_degree else (75 if sections["education"] else 50)

    # Formatting Score
    formatting_score = 85
    if word_count < 150:
        formatting_score = 45
    elif word_count < 300:
        formatting_score = 65
    elif word_count > 1500:
        formatting_score = 70
    if not contact["email"] or not contact["phone"]:
        formatting_score -= 10
    formatting_score = min(95, max(35, formatting_score))

    # Overall ATS Score (Weighted)
    overall_ats_score = int(round(
        (0.25 * keyword_match) +
        (0.25 * skills_match) +
        (0.15 * structure_score) +
        (0.15 * experience_score) +
        (0.10 * education_score) +
        (0.10 * formatting_score)
    ))
    overall_ats_score = min(97, max(30, overall_ats_score))

    # Breakdown array for frontend UI
    breakdown = [
        {"label": "Keyword Match", "value": keyword_match, "info": "How well your keywords align with industry expectations or job criteria."},
        {"label": "Skills Match", "value": skills_match, "info": "Percentage of relevant technical and domain skills present in your resume."},
        {"label": "Resume Structure", "value": structure_score, "info": "Quality of section headings and standard ATS document layout."},
        {"label": "Experience Relevance", "value": experience_score, "info": "Strength of action verbs and measurable achievements in work experience."},
        {"label": "Education", "value": education_score, "info": "Degree and academic credentials formatting match."},
        {"label": "Formatting", "value": formatting_score, "info": "ATS-friendly formatting, contact clarity, and optimal text density."}
    ]

    # Dynamic Issues Hurting Score
    issues = []
    if missing_skills:
        issues.append({
            "icon": "Target",
            "title": "Missing Keywords",
            "description": "Your resume could rank higher with high-impact industry keywords.",
            "tags": missing_skills[:4],
            "btnLabel": "Add Keywords",
            "iconColor": "bg-red-500"
        })
    
    if not sections["summary"] or word_count < 250:
        issues.append({
            "icon": "FileText",
            "title": "Weak Resume Summary",
            "description": "Your summary does not clearly state your core value proposition and key technical strengths.",
            "btnLabel": "Improve Summary",
            "iconColor": "bg-amber-500"
        })

    if q_count < 2:
        issues.append({
            "icon": "Briefcase",
            "title": "Weak Experience Description",
            "description": "Add measurable achievements (percentages, revenue, user numbers, latency improvements).",
            "btnLabel": "Improve Experience",
            "iconColor": "bg-orange-500"
        })

    if not contact["email"] or not contact["phone"]:
        issues.append({
            "icon": "Shield",
            "title": "Contact Details Incomplete",
            "description": "Ensure your professional email and contact phone number are prominently listed in the header.",
            "btnLabel": "Fix Contact",
            "iconColor": "bg-violet-500"
        })
    elif formatting_score < 75:
        issues.append({
            "icon": "Shield",
            "title": "Formatting Warning",
            "description": "Adjust word density and ensure clean bullet points without nested tables.",
            "btnLabel": "View Layout Tips",
            "iconColor": "bg-violet-500"
        })

    # Optimization Checklist
    checklist = [
        {"label": "Contact information (Email & Phone)", "done": bool(contact["email"] and contact["phone"])},
        {"label": "Standard section headings", "done": bool(sections["skills"] and sections["experience"] and sections["education"])},
        {"label": "Relevant technical skills detected", "done": len(resume_skills) >= 4},
        {"label": "Job-specific keywords match", "done": keyword_match >= 75},
        {"label": "Add measurable achievements & metrics", "done": q_count >= 2},
        {"label": "Professional summary present", "done": sections["summary"]},
        {"label": "Action verbs at start of bullets", "done": v_count >= 3},
        {"label": "Optimal resume length (350–1000 words)", "done": 250 <= word_count <= 1200}
    ]

    # Dynamic Improvement Suggestions (Before vs After)
    top_skills_str = ", ".join(resume_skills[:4]) if resume_skills else "Python, SQL, REST APIs"
    
    # Custom suggestion 1: Missing keywords bullet
    weak_bullet = bullet_analysis["sample_weak_bullets"][0] if bullet_analysis["sample_weak_bullets"] else "Worked on backend development and system tasks."
    enhanced_bullet = f"Engineered scalable backend solutions using {top_skills_str}, improving application response time by 35% and automating deployment workflows."

    # Custom suggestion 2: Summary improvement
    orig_summary = "Software engineer looking for growth opportunities in development."
    enhanced_summary = f"Results-driven software engineer with proven expertise in {top_skills_str}. Experienced in building high-performance applications, database design, and end-to-end API integration."

    # Custom suggestion 3: Quantifiable achievement
    weak_project = "Developed a web application for user data processing."
    enhanced_project = "Designed and deployed a full-stack web application processing 10,000+ daily user requests, reducing manual operations by 40%."

    suggestions = [
        {
            "label": "Recommendation 1 — Add Missing Keywords & Technologies",
            "current": weak_bullet,
            "suggestion": enhanced_bullet,
            "actions": [
                {"label": "Apply Suggestion", "style": "bg-indigo-600 text-white hover:bg-indigo-700"},
                {"label": "Copy", "style": "bg-slate-100 text-slate-700 hover:bg-slate-200"}
            ]
        },
        {
            "label": "Recommendation 2 — Strengthen Professional Summary",
            "current": orig_summary,
            "suggestion": enhanced_summary,
            "actions": [
                {"label": "Accept", "style": "bg-emerald-600 text-white hover:bg-emerald-700"},
                {"label": "Edit", "style": "bg-slate-100 text-slate-700 hover:bg-slate-200"},
                {"label": "Regenerate", "style": "bg-violet-100 text-violet-700 hover:bg-violet-200 flex items-center gap-1"}
            ]
        },
        {
            "label": "Recommendation 3 — Inject Quantifiable Metrics",
            "current": weak_project,
            "suggestion": enhanced_project,
            "actions": [
                {"label": "Improve Bullet", "style": "bg-indigo-600 text-white hover:bg-indigo-700"},
                {"label": "Copy Text", "style": "bg-slate-100 text-slate-700 hover:bg-slate-200"}
            ]
        }
    ]

    # Natural Language Summary
    score_label = "Excellent" if overall_ats_score >= 80 else "Good" if overall_ats_score >= 60 else "Needs Improvement"
    summary_text = (
        f"Resume parsed for {candidate_name}. Overall ATS score is {overall_ats_score}/100 ({score_label}). "
        f"Identified {len(resume_skills)} technical skills. "
        + (f"Matched {len(matched_skills)}/{len(jd_skills)} required skills from the job description. " if has_jd and jd_skills else "")
        + f"{'Consider adding measurable metrics to bullet points.' if q_count < 2 else 'Good use of quantifiable metrics.'}"
    )

    # After optimization projected score
    projected_score = min(96, overall_ats_score + 14)

    return {
        "candidateName": candidate_name,
        "email": contact["email"],
        "phone": contact["phone"],
        "fileName": filename,
        "atsScore": overall_ats_score,
        "projectedScore": projected_score,
        "scoreLabel": score_label,
        "breakdown": breakdown,
        "issues": issues,
        "suggestions": suggestions,
        "checklist": checklist,
        "matchedSkills": matched_skills,
        "missingSkills": missing_skills,
        "summary": summary_text,
        "wordCount": word_count,
        "extractedText": extracted_text[:3000] # First 3000 chars
    }
