"""
User service to store and manage user profiles in database
"""
from typing import Optional
from core.database import User, add_user, get_user, get_user_by_email
from sqlmodel import Session
from core.database import engine

class UserService:

    @staticmethod
    def create_user(skills: str, experience: str, education: str) -> User:
        """Create a new user profile with extracted resume data."""
        user = User(
            skills=skills,
            experience=experience,
            education=education
        )
        return add_user(user)

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID."""
        return get_user(user_id)

    @staticmethod 
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email."""
        return get_user_email(email)

    @staticmethod
    def create_or_update_user(user_id: str, skills: str, experience: str, education: str) -> User:
        """
        Create or update a user profile:
        - If user doesn't exist, create new user with provided ID
        - If user exists, update their skills, experience, education
        """
        with Session(engine) as session:
            existing_user = session.get(User, user_id)
            
            if existing_user:
                # Update existing user
                existing_user.skills = skills
                existing_user.experience = experience
                existing_user.education = education
                session.add(existing_user)
                session.commit()
                session.refresh(existing_user)
                return existing_user
            else:
                # Create new user with provided ID
                new_user = User(
                    id=user_id,
                    skills=skills,
                    experience=experience,
                    education=education
                )
                session.add(new_user)
                session.commit()
                session.refresh(new_user)
                return new_user
