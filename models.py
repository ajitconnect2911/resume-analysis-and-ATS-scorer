import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from database import Base

class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String, index=True)
    candidate_name = Column(String, nullable=True)
    candidate_email = Column(String, nullable=True)
    candidate_phone = Column(String, nullable=True)
    
    ats_score = Column(Integer)
    projected_score = Column(Integer, default=85)
    score_label = Column(String, default="Good")
    
    job_description = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    
    # JSON serialized structures
    breakdown_json = Column(Text, nullable=True)
    issues_json = Column(Text, nullable=True)
    suggestions_json = Column(Text, nullable=True)
    checklist_json = Column(Text, nullable=True)
    matched_skills_json = Column(Text, nullable=True)
    missing_skills_json = Column(Text, nullable=True)
    extracted_text = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        """Serialize model to a dictionary suitable for API responses."""
        def safe_json_loads(val, default):
            if not val:
                return default
            try:
                return json.loads(val)
            except Exception:
                return default

        return {
            "id": self.id,
            "fileName": self.file_name,
            "candidateName": self.candidate_name,
            "email": self.candidate_email,
            "phone": self.candidate_phone,
            "atsScore": self.ats_score,
            "projectedScore": self.projected_score or min(96, (self.ats_score or 70) + 14),
            "scoreLabel": self.score_label or ("Excellent" if (self.ats_score or 0) >= 80 else "Good"),
            "jobDescription": self.job_description,
            "summary": self.summary,
            "breakdown": safe_json_loads(self.breakdown_json, []),
            "issues": safe_json_loads(self.issues_json, []),
            "suggestions": safe_json_loads(self.suggestions_json, []),
            "checklist": safe_json_loads(self.checklist_json, []),
            "matchedSkills": safe_json_loads(self.matched_skills_json, []),
            "missingSkills": safe_json_loads(self.missing_skills_json, []),
            "savedAt": self.created_at.isoformat() if self.created_at else None
        }
