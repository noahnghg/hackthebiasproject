from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class JobCreate(BaseModel):
    """Model for creating a job (user_id comes from URL)"""
    title: str
    company: str
    description: str
    requirements: str

class Job(BaseModel):
    """Full job model including user_id"""
    title: str
    user_id: str
    company: str
    description: str
    requirements: str
