from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    name: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

class OrganizationCreate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    id: uuid.UUID
    name: str
    owner_id: uuid.UUID
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class ProjectCreate(BaseModel):
    name: str
    organization_id: uuid.UUID

class ProjectResponse(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True

class RetryPolicyBase(BaseModel):
    strategy: str
    base_delay_ms: int = 1000
    max_retries: int = 3
    max_delay_ms: int = 60000

class RetryPolicyCreate(RetryPolicyBase):
    pass

class RetryPolicyResponse(RetryPolicyBase):
    id: uuid.UUID
    queue_id: Optional[uuid.UUID]

    class Config:
        orm_mode = True
        from_attributes = True

class QueueBase(BaseModel):
    name: str
    priority: int = 0
    concurrency_limit: int = 10
    is_paused: bool = False

class QueueCreate(QueueBase):
    project_id: uuid.UUID
    default_retry_policy: Optional[RetryPolicyCreate] = None

class QueueUpdate(BaseModel):
    priority: Optional[int] = None
    concurrency_limit: Optional[int] = None
    is_paused: Optional[bool] = None

class QueueResponse(QueueBase):
    id: uuid.UUID
    project_id: uuid.UUID
    default_retry_policy_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True
