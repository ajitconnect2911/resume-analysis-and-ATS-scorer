import os
import json
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Database & Models
import models
from database import engine, get_db
from analyzer import analyze_resume_ats

# Automatically create database tables with updated schema
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="ResumeAI SaaS Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "ResumeAI SaaS API",
        "endpoints": ["/api/ats-analyze", "/api/history", "/api/candidates"]
    }

@app.post("/api/ats-analyze")
async def analyze_ats(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Parses the uploaded resume (PDF, DOCX, TXT), runs real ATS scoring,
    extracts skills, detects issues, provides tailored AI suggestions,
    and stores the complete analysis in the SQLite database.
    """
    valid_extensions = ('.pdf', '.docx', '.doc', '.txt')
    if not any(file.filename.lower().endswith(ext) for ext in valid_extensions):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{file.filename}'. Allowed formats: PDF, DOCX, TXT."
        )

    try:
        contents = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Run ATS analysis engine
    try:
        analysis = analyze_resume_ats(
            file_bytes=contents,
            filename=file.filename,
            job_description=job_description
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis engine error: {str(e)}")

    # Save Record to Database
    try:
        db_record = models.ResumeAnalysis(
            file_name=analysis["fileName"],
            candidate_name=analysis.get("candidateName"),
            candidate_email=analysis.get("email"),
            candidate_phone=analysis.get("phone"),
            ats_score=analysis["atsScore"],
            projected_score=analysis.get("projectedScore", 88),
            score_label=analysis.get("scoreLabel", "Good"),
            job_description=job_description,
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
        
        response_data = db_record.to_dict()
        response_data["databaseSaved"] = True
        return response_data
    except Exception as e:
        db.rollback()
        # Fallback to returning analysis even if db has write warning
        analysis["databaseSaved"] = False
        analysis["dbError"] = str(e)
        return analysis

@app.get("/api/history")
def get_history(db: Session = Depends(get_db)):
    """Fetch history of all uploaded and analyzed resumes from the database."""
    analyses = db.query(models.ResumeAnalysis).order_by(models.ResumeAnalysis.created_at.desc()).all()
    return [a.to_dict() for a in analyses]

@app.get("/api/history/{analysis_id}")
def get_analysis_by_id(analysis_id: int, db: Session = Depends(get_db)):
    """Fetch a single analysis record by ID."""
    record = db.query(models.ResumeAnalysis).filter(models.ResumeAnalysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    return record.to_dict()

@app.delete("/api/history/{analysis_id}")
def delete_analysis(analysis_id: int, db: Session = Depends(get_db)):
    """Delete an analysis record."""
    record = db.query(models.ResumeAnalysis).filter(models.ResumeAnalysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")
    db.delete(record)
    db.commit()
    return {"success": True, "message": f"Deleted analysis #{analysis_id}"}

@app.get("/api/candidates")
def get_candidates(db: Session = Depends(get_db)):
    """Get candidate list derived from analyses stored in the database."""
    records = db.query(models.ResumeAnalysis).order_by(models.ResumeAnalysis.created_at.desc()).all()
    results = []
    colors = ['#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ec4899']
    
    for i, r in enumerate(records):
        data = r.to_dict()
        name = data.get("candidateName") or "Candidate"
        initials = "".join([part[0] for part in name.split()[:2]]).upper() or "CA"
        ats = data.get("atsScore", 75)
        status = "Shortlisted" if ats >= 80 else "Review" if ats >= 60 else "Rejected"
        results.append({
            "id": data["id"],
            "name": name,
            "email": data.get("email") or "Not provided",
            "phone": data.get("phone") or "Not provided",
            "role": "Software Engineer",
            "exp": "2+ Years",
            "skills": (data.get("matchedSkills") or [])[:5],
            "match": min(98, ats + 4),
            "ats": ats,
            "status": status,
            "initials": initials,
            "color": colors[i % len(colors)],
            "date": data.get("savedAt")
        })
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
