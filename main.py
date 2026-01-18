from fastapi import FastAPI
from app.routes.users import router as users_router
from app.routes.jobs import router as jobs_router
from app.routes.applications import router as applications_router
from app.routes.auth import router as auth_router
from core.database import create_db_and_tables, seed_sample_jobs, seed_test_user, seed_sample_applications

app = FastAPI(
    title="HackTheBias API",
    description="API for parsing, anonymizing, and analyzing resumes to reduce hiring bias.",
    version="0.1.0"
)

# Include Routers
app.include_router(auth_router)
app.include_router(jobs_router)
app.include_router(users_router)
app.include_router(applications_router)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()
    seed_test_user()  # Must run before jobs/applications
    seed_sample_jobs()
    seed_sample_applications()

@app.get("/")
async def root():
    return {"message": "Welcome to HackTheBias API. Visit /docs for documentation."}
