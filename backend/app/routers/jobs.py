import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from ..db import get_db, Base, engine
from ..models import Job, JobStatus, User
from ..schemas import Job as JobSchema, JobUpdate
from ..storage import upload_file
from ..auth import get_current_user, get_current_superuser
    

router = APIRouter()
INPUT_BUCKET = "cv-input"
RESULT_BUCKET = "cv-result"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# create tables
Base.metadata.create_all(bind=engine)

@router.post("/jobs/", response_model=JobSchema)
async def create_job(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    file_size = file.file.seek(0, 2)
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds {MAX_FILE_SIZE}MB limit"
        )
    
    # create a job belonging to the current user
    job = Job(user_id=current_user.id, status=JobStatus.Pending)
    db.add(job)
    db.commit()
    db.refresh(job)
    key = f"{job.id}/{file.filename}"
    try:
        upload_file(INPUT_BUCKET, key, file.file)
    except Exception as e:
        db.delete(job)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
    job.file_key = key
    db.commit()
    db.refresh(job)
    return job

@router.get("/jobs/", response_model=list[JobSchema])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # superusers see all jobs; regular users see only their own
    query = db.query(Job)
    if not current_user.is_superuser:
        query = query.filter(Job.user_id == current_user.id)
    jobs = query.order_by(Job.created_at.desc()).all()
    return jobs

@router.patch("/jobs/{job_id}", response_model=JobSchema)
def update_job(
    job_id: int,
    update: JobUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_superuser),
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    job.status = update.status
    if update.result_key is not None:
        job.result_key = update.result_key
    db.commit()
    db.refresh(job)
    return job