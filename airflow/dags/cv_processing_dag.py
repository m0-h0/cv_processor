import os
import csv
import io
import logging
import requests
import boto3
from botocore.client import Config
from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator

import os
# Configuration from environment
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minio")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minio123")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"

# Auth credentials for backend
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

INPUT_BUCKET = "cv-input"
RESULT_BUCKET = "cv-result"

# Initialize S3 client for MinIO
s3_client = boto3.client(
    "s3",
    endpoint_url=f"http{'s' if MINIO_SECURE else ''}://{MINIO_ENDPOINT}",
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    config=Config(signature_version="s3v4"),
)

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 1, 1),
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="cv_processing",
    default_args=default_args,
    schedule_interval=timedelta(minutes=5),
    catchup=False,
    is_paused_upon_creation=False,
) as dag:

    def process_pending_jobs():
        # Authenticate and fetch jobs
        auth_resp = requests.post(
            f"{BACKEND_URL}/auth/token",
            data={"username": ADMIN_USER, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        auth_resp.raise_for_status()
        token = auth_resp.json().get("access_token")
        headers = {
            "Authorization": f"Bearer {token}"
        }
        resp = requests.get(f"{BACKEND_URL}/jobs/", headers=headers)
        resp.raise_for_status()
        jobs = resp.json()
        for job in jobs:
            if job.get("status") != "Pending":
                continue
            job_id = job.get("id")
            file_key = job.get("file_key")
            filename = file_key.split("/", 1)[-1]
            try:
                # Mark as Running
                requests.patch(
                    f"{BACKEND_URL}/jobs/{job_id}",
                    json={"status": "Running"},
                    headers=headers,
                )
                # Download input from MinIO
                buffer_in = io.BytesIO()
                s3_client.download_fileobj(INPUT_BUCKET, file_key, buffer_in)
                buffer_in.seek(0)
                # Process CSV: uppercase all fields
                text_in = io.TextIOWrapper(buffer_in, encoding="utf-8")
                reader = csv.reader(text_in)
                buffer_out = io.StringIO()
                writer = csv.writer(buffer_out)
                for row in reader:
                    writer.writerow([cell.upper() for cell in row])
                buffer_out.seek(0)
                # Upload result to MinIO
                result_key = f"{job_id}/result-{filename}"
                put_object(
                    bucket=RESULT_BUCKET,
                    key=result_key,
                    body=buffer_out.getvalue().encode("utf-8"),
                )
                # Mark as Completed
                requests.patch(
                    f"{BACKEND_URL}/jobs/{job_id}",
                    json={"status": "Completed", "result_key": result_key},
                    headers=headers,
                )
            except Exception:
                logging.exception(f"Processing job {job_id} failed")
                try:
                    requests.patch(
                        f"{BACKEND_URL}/jobs/{job_id}",
                        json={"status": "Failed"},
                        headers=headers,
                    )
                except Exception:
                    logging.error(f"Failed to update job {job_id} status to Failed")

    def ensure_bucket(bucket: str):
        try:
            s3_client.head_bucket(Bucket=bucket)
        except Exception:
            s3_client.create_bucket(Bucket=bucket)

    def put_object(bucket: str, key: str, body):
        ensure_bucket(bucket)
        s3_client.put_object(
            Bucket=bucket,
            Key=key,
            Body=body,
        )
        


    process_task = PythonOperator(
        task_id="process_cv_jobs",
        python_callable=process_pending_jobs,
    )