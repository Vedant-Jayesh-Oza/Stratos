"""
Simple test for Planner orchestrator
"""

import asyncio
import json
import os
import subprocess
from dotenv import load_dotenv

load_dotenv(override=True)

os.environ['MOCK_LAMBDAS'] = 'true'

from src import Database
from src.schemas import JobCreate

def setup_test_data():
    """Ensure test data exists and create a test job"""
    print("Ensuring test data exists...")
    result = subprocess.run(
        ["uv", "run", "reset_db.py", "--with-test-data", "--skip-drop"],
        cwd="../database",
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Warning: Could not ensure test data: {result.stderr}")
    
    db = Database()
    
    test_user_id = "test_user_001"
    
    user = db.users.find_by_clerk_id(test_user_id)
    if not user:
        raise ValueError(f"Test user {test_user_id} not found. Please run: cd ../database && uv run reset_db.py --with-test-data")
    
    job_create = JobCreate(
        clerk_user_id=test_user_id,
        job_type="portfolio_analysis",
        request_payload={"analysis_type": "comprehensive", "test": True}
    )
    job_id = db.jobs.create(job_create.model_dump())
    
    return job_id

def test_planner():
    """Test the planner orchestrator"""
    
    job_id = setup_test_data()
    
    test_event = {
        "job_id": job_id
    }
    
    print("Testing Planner Orchestrator...")
    print(f"Job ID: {job_id}")
    print("=" * 60)
    
    from lambda_handler import lambda_handler
    
    result = lambda_handler(test_event, None)
    
    print(f"Status Code: {result['statusCode']}")
    
    if result['statusCode'] == 200:
        body = json.loads(result['body'])
        print(f"Success: {body.get('success', False)}")
        print(f"Message: {body.get('message', 'N/A')}")
    else:
        print(f"Error: {result['body']}")
    
    print("=" * 60)

if __name__ == "__main__":
    test_planner()