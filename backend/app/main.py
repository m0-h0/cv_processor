import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base, SessionLocal
from .routers import jobs
from .auth import router as auth_router, get_password_hash

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(auth_router, prefix="/auth")
app.include_router(jobs.router)
@app.on_event("startup")
def on_startup():
    # create tables and default admin
    Base.metadata.create_all(bind=engine)
    admin_user = os.getenv("ADMIN_USER")
    admin_password = os.getenv("ADMIN_PASSWORD")
    if admin_user and admin_password:
        db = SessionLocal()
        from .models import User
        if not db.query(User).filter(User.username == admin_user).first():
            hashed = get_password_hash(admin_password)
            admin = User(
                username=admin_user,
                email=None,
                hashed_password=hashed,
                is_superuser=True,
            )
            db.add(admin)
            db.commit()
        db.close()

@app.get("/")
def read_root():
    return {"message": "CV Processing API"}