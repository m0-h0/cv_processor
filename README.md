# CV Processing System Documentation

## Architecture

### Components
1. **Frontend** (Angular)
   - User authentication and registration
   - CV file upload interface
   - Job status monitoring
   - Port: 4200

2. **Backend** (FastAPI)
   - RESTful API
   - User management
   - Job management
   - MinIO integration
   - Port: 8000

3. **Airflow**
   - Automated CV processing
   - Job status management
   - Scheduled every 5 minutes

4. **Storage**
   - MinIO (S3-compatible storage)
   - PostgreSQL (Relational database)
   - Redis (Airflow message broker)

## Setup and Deployment

### Prerequisites
- Docker and Docker Compose
- Node.js (for local frontend development)
- Python 3.9+ (for local backend development)

### Environment Variables
```env
# PostgreSQL
POSTGRES_USER=<postgres_username>
POSTGRES_PASSWORD=<postgres_password>
POSTGRES_DB=<database_name>
POSTGRES_PORT=5432

# MinIO
MINIO_ROOT_USER=<minio_username>
MINIO_ROOT_PASSWORD=<minio_password>
MINIO_PORT=9000
MINIO_CONSOLE_PORT=9001

# Redis
REDIS_PORT=6379

# Backend
BACKEND_PORT=8000
DATABASE_URL=<database_url>
MINIO_ENDPOINT=minio:${MINIO_PORT}
MINIO_ACCESS_KEY=${MINIO_ROOT_USER}
MINIO_SECRET_KEY=${MINIO_ROOT_PASSWORD}
MINIO_SECURE=false
SECRET_KEY=<your_secret_key>
ADMIN_USER=<admin_username>
ADMIN_PASSWORD=<admin_password>

# Airflow
AIRFLOW_PORT=8080
AIRFLOW_EXECUTOR=CeleryExecutor
AIRFLOW_DATABASE_URL=<database_url>
AIRFLOW_BROKER_URL=redis://redis:${REDIS_PORT}/0
AIRFLOW_LOAD_EXAMPLES=false
BACKEND_URL=http://backend:${BACKEND_PORT}

# Frontend
FRONTEND_PORT=4200
```

### Deployment
1. Start all services:
```bash
docker-compose up -d
```

2. Access points:
   - Frontend: http://localhost:4200
   - Backend API: http://localhost:8000
   - MinIO Console: http://localhost:9001

## Data Flow

1. **User Upload**
   - User uploads CSV file through frontend
   - Backend creates job record and stores file in MinIO
   - Job status set to "Pending"

2. **Processing**
   - Airflow DAG polls for pending jobs every 5 minutes
   - Downloads CSV from MinIO input bucket
   - Processes CSV
   - Uploads result to MinIO result bucket
   - Updates job status to "Completed"

3. **Error Handling**
   - Failed jobs are marked with "Failed" status
   - Exceptions are logged in Airflow logs

## Development

### Frontend Development
```bash
cd frontend
npm install
ng serve
```

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Airflow DAG Development
```bash
cd airflow/dags
# Edit cv_processing_dag.py
```

## Security Considerations

**Authentication**
   - JWT-based authentication
   - Password hashing using bcrypt
   - Role-based access control (admin/regular users)

**File Storage**
   - Separate input/output buckets
   - File size limits
   - CSV file type validation