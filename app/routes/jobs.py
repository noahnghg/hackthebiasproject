from fastapi import APIRouter 
from models.job import Job 
from app.services.job import JobService 

router = APIRouter(
    prefix="/jobs",
    tags=["jobs"]
)

@router.post("/")
async def create_job(job: Job):
    """Create a new job posting."""
    return JobService.create_job(job)

@router.get("/")
async def get_all_jobs():
    """Get all job postings."""
    return JobService.get_all_jobs() 

@router.get("/user/{user_id}")
async def get_jobs_by_user(user_id: str):
    """Get all jobs posted by a specific user."""
    return JobService.get_jobs_by_user(user_id)

@router.get("/{job_id}")
async def get_job_by_id(job_id: str):
    """Get a specific job by ID."""
    from fastapi import HTTPException
    job = JobService.get_job_by_id(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
