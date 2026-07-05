from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import uuid
import hashlib
import os
from typing import List

from ..database import get_db
from ..models import User, Organization, Project
from ..schemas import OrganizationCreate, OrganizationResponse, ProjectCreate, ProjectResponse
from .deps import get_current_user

router = APIRouter(prefix="/api/v1", tags=["projects"])

@router.post("/organizations", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(org: OrganizationCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_org = Organization(name=org.name, owner_id=current_user.id)
    db.add(db_org)
    await db.commit()
    await db.refresh(db_org)
    return db_org

@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Organization).where(Organization.owner_id == current_user.id))
    return result.scalars().all()

@router.post("/projects", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    org_result = await db.execute(select(Organization).where(Organization.id == project.organization_id))
    org = org_result.scalars().first()
    if not org or org.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    raw_api_key = os.urandom(24).hex()
    hashed_key = hashlib.sha256(raw_api_key.encode()).hexdigest()
    
    db_project = Project(
        name=project.name,
        organization_id=project.organization_id,
        api_key=hashed_key
    )
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return {"project": ProjectResponse.from_orm(db_project), "api_key": raw_api_key}

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Project).join(Organization).where(Organization.owner_id == current_user.id))
    return result.scalars().all()
