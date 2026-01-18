from typing import List, Optional
from models.job import Job, JobCreate
from core.database import add_job, get_job, get_all_jobs, search_jobs as db_search_jobs
from core.database import Job as DBJob, Session, engine, select

class JobService:
    @staticmethod
    def create_job(user_id: str, data: JobCreate) -> DBJob:
        """Creates a new job posting for a user."""
        job = DBJob(
            user_id=user_id,
            title=data.title,
            company=data.company,
            description=data.description,
            requirements=data.requirements
        )
        return add_job(job)

    @staticmethod
    def get_all_jobs() -> List[DBJob]:
        """Returns all job postings."""
        return get_all_jobs()

    @staticmethod
    def get_job_by_id(job_id: str) -> Optional[DBJob]:
        """Returns a job by its ID."""
        return get_job(job_id)

    @staticmethod
    def get_jobs_by_user(user_id: str) -> List[DBJob]:
        """Returns all jobs posted by a specific user."""
        with Session(engine) as session:
            statement = select(DBJob).where(DBJob.user_id == user_id)
            return session.exec(statement).all()

    @staticmethod
    def search_jobs(query: str) -> List[DBJob]:
        """Searches jobs by title, company, or description."""
        if not query:
            return get_all_jobs()
        return db_search_jobs(query)
