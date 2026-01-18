from fastapi import APIRouter 
from models.application import ApplicationSubmit 
from app.services.application import ApplicationService



router = APIRouter(
    prefix="/applications",
    tags=["applications"]
)

@router.post("/")
async def create_application(application: ApplicationSubmit): 
    return ApplicationService.create_application(application)

@router.get("/user/{userId}")
async def get_applications_of_user(userId: str): 
    """Get all applications submitted by a user."""
    return ApplicationService.get_applications_of_user(userId)

@router.get("/job/{jobId}")
async def get_applications_of_job(jobId: str):
    """Get all applications for a specific job (for job posters to view applicants)."""
    return ApplicationService.get_applications_of_job(jobId)
