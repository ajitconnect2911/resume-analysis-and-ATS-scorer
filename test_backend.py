import io
import json
import analyzer
import models
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

def run_tests():
    sample_resume = b"""Rahul Sharma
Email: rahul.sharma@example.com
Phone: +91 9876543210
Skills: Python, FastAPI, React, SQL, PostgreSQL, Docker, Git, REST API
Experience:
- Developed scalable REST APIs using FastAPI and PostgreSQL, serving 10,000+ daily active users.
- Optimized database queries and indexes, reducing response latency by 35%.
Education:
- Bachelor of Technology in Computer Science, 2023
Summary:
Results-driven software engineer experienced in building performant backend web services and REST APIs.
"""

    print("--- 1. Testing Analyzer Engine ---")
    analysis = analyzer.analyze_resume_ats(
        file_bytes=sample_resume,
        filename="Rahul_Sharma_Resume.txt",
        job_description="Looking for Python and FastAPI developer with Docker and AWS experience."
    )
    print("Candidate Name:", analysis["candidateName"])
    print("Email:", analysis["email"])
    print("Phone:", analysis["phone"])
    print("ATS Score:", analysis["atsScore"])
    print("Matched Skills:", analysis["matchedSkills"])
    print("Missing Skills:", analysis["missingSkills"])
    print("Breakdown Count:", len(analysis["breakdown"]))
    print("Checklist Count:", len(analysis["checklist"]))
    print("Suggestions Count:", len(analysis["suggestions"]))

    print("\n--- 2. Testing Database Persistence ---")
    db = SessionLocal()
    db_record = models.ResumeAnalysis(
        file_name=analysis["fileName"],
        candidate_name=analysis.get("candidateName"),
        candidate_email=analysis.get("email"),
        candidate_phone=analysis.get("phone"),
        ats_score=analysis["atsScore"],
        projected_score=analysis.get("projectedScore", 88),
        score_label=analysis.get("scoreLabel", "Good"),
        job_description="Looking for Python and FastAPI developer with Docker and AWS experience.",
        summary=analysis["summary"],
        breakdown_json=json.dumps(analysis.get("breakdown", [])),
        issues_json=json.dumps(analysis.get("issues", [])),
        suggestions_json=json.dumps(analysis.get("suggestions", [])),
        checklist_json=json.dumps(analysis.get("checklist", [])),
        matched_skills_json=json.dumps(analysis.get("matchedSkills", [])),
        missing_skills_json=json.dumps(analysis.get("missingSkills", [])),
        extracted_text=analysis.get("extractedText", "")
    )
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    print("Saved Record ID:", db_record.id)

    print("\n--- 3. Testing Database Query ---")
    records = db.query(models.ResumeAnalysis).all()
    print("Total Records in DB:", len(records))
    latest = records[-1].to_dict()
    print("Latest Record Dict:", {
        "id": latest["id"],
        "name": latest["candidateName"],
        "score": latest["atsScore"],
        "skills": latest["matchedSkills"]
    })
    db.close()
    print("\nALL BACKEND & DATABASE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    run_tests()
