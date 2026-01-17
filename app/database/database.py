from sqlmodel import Field, SQLModel, create_engine, Session, select
from typing import List, Optional

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    skills: str
    experience: str
    education: str

class Application(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    userId: int = Field(foreign_key="user.id")
    jobId: int = Field(foreign_key="job.id")
    score: float

class Job(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    description: str
    company: str
    requirements: str

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
SQLModel.metadata.create_all(engine)


# Database session dependency
def get_session():
    with Session(engine) as session:
        yield session


# ==================== USER CRUD OPERATIONS ====================

def create_user(user: User, session: Session) -> User:
    """Create a new user in the database."""
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def get_user_by_id(user_id: int, session: Session) -> Optional[User]:
    """Get a user by their ID."""
    return session.get(User, user_id)


def get_all_users(session: Session) -> List[User]:
    """Get all users from the database."""
    statement = select(User)
    return session.exec(statement).all()


def update_user(user_id: int, user_data: dict, session: Session) -> Optional[User]:
    """Update a user's information."""
    user = session.get(User, user_id)
    if not user:
        return None
    
    for key, value in user_data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def delete_user(user_id: int, session: Session) -> bool:
    """Delete a user from the database."""
    user = session.get(User, user_id)
    if not user:
        return False
    
    session.delete(user)
    session.commit()
    return True


# ==================== APPLICATION CRUD OPERATIONS ====================

def create_application(application: Application, session: Session) -> Application:
    """Create a new application in the database."""
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def get_application_by_id(application_id: int, session: Session) -> Optional[Application]:
    """Get an application by its ID."""
    return session.get(Application, application_id)


def get_all_applications(session: Session) -> List[Application]:
    """Get all applications from the database."""
    statement = select(Application)
    return session.exec(statement).all()


def get_applications_by_job(job_id: int, session: Session) -> List[Application]:
    """Get all applications for a specific job."""
    statement = select(Application).where(Application.jobId == job_id)
    return session.exec(statement).all()


def get_applications_by_user(user_id: int, session: Session) -> List[Application]:
    """Get all applications for a specific user."""
    statement = select(Application).where(Application.userId == user_id)
    return session.exec(statement).all()


def update_application(application_id: int, application_data: dict, session: Session) -> Optional[Application]:
    """Update an application's information."""
    application = session.get(Application, application_id)
    if not application:
        return None
    
    for key, value in application_data.items():
        if hasattr(application, key):
            setattr(application, key, value)
    
    session.add(application)
    session.commit()
    session.refresh(application)
    return application


def delete_application(application_id: int, session: Session) -> bool:
    """Delete an application from the database."""
    application = session.get(Application, application_id)
    if not application:
        return False
    
    session.delete(application)
    session.commit()
    return True


# ==================== JOB CRUD OPERATIONS ====================

def create_job(job: Job, session: Session) -> Job:
    """Create a new job in the database."""
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def get_job_by_id(job_id: int, session: Session) -> Optional[Job]:
    """Get a job by its ID."""
    return session.get(Job, job_id)


def get_all_jobs(session: Session) -> List[Job]:
    """Get all jobs from the database."""
    statement = select(Job)
    return session.exec(statement).all()


def search_jobs_by_title(title: str, session: Session) -> List[Job]:
    """Search jobs by title (case-insensitive partial match)."""
    statement = select(Job).where(Job.title.ilike(f"%{title}%"))
    return session.exec(statement).all()


def search_jobs_by_company(company: str, session: Session) -> List[Job]:
    """Search jobs by company (case-insensitive partial match)."""
    statement = select(Job).where(Job.company.ilike(f"%{company}%"))
    return session.exec(statement).all()


def update_job(job_id: int, job_data: dict, session: Session) -> Optional[Job]:
    """Update a job's information."""
    job = session.get(Job, job_id)
    if not job:
        return None
    
    for key, value in job_data.items():
        if hasattr(job, key):
            setattr(job, key, value)
    
    session.add(job)
    session.commit()
    session.refresh(job)
    return job


def delete_job(job_id: int, session: Session) -> bool:
    """Delete a job from the database."""
    job = session.get(Job, job_id)
    if not job:
        return False
    
    session.delete(job)
    session.commit()
    return True