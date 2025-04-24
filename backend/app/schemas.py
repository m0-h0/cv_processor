from pydantic import BaseModel
from enum import Enum
from typing import Optional, List
from datetime import datetime

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime

    class Config:
        orm_mode = True

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class JobStatus(str, Enum):
    Pending = "Pending"
    Running = "Running"
    Completed = "Completed"
    Failed = "Failed"

class Job(BaseModel):
    id: int
    file_key: str
    result_key: Optional[str]
    status: JobStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

class JobUpdate(BaseModel):
    status: JobStatus
    result_key: Optional[str] = None