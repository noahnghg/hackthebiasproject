from fastapi import APIRouter, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional
from app.services.resume import ResumeService
from app.services.users import UserService
from app.services.job import JobService 
from models.job import JobCreate

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

class UploadResumeRequest(BaseModel):
    user_id: str

@router.post("/upload-resume")
async def upload_and_store_resume(user_id: str = Form(...), file: UploadFile = File(...)):
    """
    Upload a resume (PDF) to be parsed, anonymized, and stored.
    - If user doesn't exist, creates new user with extracted data
    - If user exists, updates their data with new resume info
    Returns the user with extracted skills, experience, education.
    """
    # Parse and extract data from resume
    extracted_data = ResumeService.NLP_pipeline(file)
    
    # Convert lists to comma-separated strings for storage
    skills_str = ", ".join(extracted_data.get("skills", []))
    experience_str = " | ".join(extracted_data.get("experience", []))
    education_str = ", ".join(extracted_data.get("education", []))
    
    # Create or update user
    user = UserService.create_or_update_user(
        user_id=user_id,
        skills=skills_str,
        experience=experience_str,
        education=education_str
    )
    
    return {
        "user_id": user.id,
        "skills": user.skills,
        "experience": user.experience,
        "education": user.education,
        "message": "User profile created/updated successfully"
    }

@router.get("/{user_id}")
async def get_user(user_id: str):
    """Get user profile by ID."""
    from fastapi import HTTPException
    user = UserService.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "id": user.id,
        "skills": user.skills,
        "experience": user.experience,
        "education": user.education
    }

@router.post("/{user_id}/jobs")
async def create_job_for_user(user_id: str, job: JobCreate):
    """Create a new job posting for a user."""
    return JobService.create_job(user_id, job)

@router.get("/{user_id}/jobs")
async def get_jobs_by_user(user_id: str):
    """Get all jobs posted by a user."""
    return JobService.get_jobs_by_user(user_id)
