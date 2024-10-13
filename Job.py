from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import os

# FastAPI instance
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allowing all origins for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files from the 'static' directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# Serve index.html when visiting the root URL '/'
@app.get("/")
def serve_homepage():
    return FileResponse(os.path.join("static", "Job.html"))

# Load jobs from CSV file
def load_jobs():
    if os.path.exists("jobs.csv"):
        return pd.read_csv("jobs.csv")
    return pd.DataFrame(columns=["id", "title", "company", "location", "Experience", "Skills", "type", "salary", "description", "category"])

# Save jobs to CSV file
def save_jobs(jobs_df):
    jobs_df.to_csv("jobs.csv", index=False)

# Load jobs into a DataFrame
jobs_df = load_jobs()
job_id_counter = len(jobs_df) + 1

# Pydantic model for Job
class Job(BaseModel):
    id: Optional[int] = None
    title: str
    company: str
    location: str
    Experience: str
    Skills: str
    type: str
    salary: str
    description: str
    category: Optional[str] = None

# Get all jobs or filter by job type, location, or category with pagination
@app.get("/jobs", response_model=List[Job])
def get_jobs(
    job_type: Optional[str] = None,
    location: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=100)
):
    filtered_jobs = jobs_df.to_dict(orient='records')
    if job_type:
        filtered_jobs = [job for job in filtered_jobs if job_type.lower() in job['type'].lower()]
    if location:
        filtered_jobs = [job for job in filtered_jobs if location.lower() in job['location'].lower()]
    if category:
        filtered_jobs = [job for job in filtered_jobs if category.lower() in job.get('category', '').lower()]
    return filtered_jobs[skip: skip + limit]

# Function to recommend jobs based on a job title
def recommend_jobs(job_title, similarity_threshold=0.1):
    jobs_df['combined_features'] = jobs_df['title'] + " " + jobs_df['description'] + " " + jobs_df['category'].fillna('')
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(jobs_df['combined_features'])
    
    try:
        idx = jobs_df[jobs_df['title'] == job_title].index[0]
    except IndexError:
        return []
    
    cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)
    sim_scores = list(enumerate(cosine_sim[idx]))

    relevant_jobs = [i for i in sim_scores if i[1] >= similarity_threshold]
    
    relevant_jobs = sorted(relevant_jobs, key=lambda x: x[1], reverse=True)

    job_indices = [i[0] for i in relevant_jobs]
    return jobs_df.iloc[job_indices][['title', 'company', 'location', 'category']].to_dict(orient='records')

# Get job recommendations based on a job title
@app.get("/recommendations/jobs")
def get_job_recommendations(job_title: str):
    recommended_jobs = recommend_jobs(job_title)
    if not recommended_jobs:
        raise HTTPException(status_code=404, detail="Job title not found")
    return recommended_jobs

# Function to recommend jobs based on skills
def recommend_skills_based_jobs(skills_input: str, similarity_threshold=0.1):
    jobs_df['Skills'] = jobs_df['Skills'].fillna('')  # Handle missing Skills values
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(jobs_df['Skills'])
    
    input_skills_vector = vectorizer.transform([skills_input])
    cosine_sim = cosine_similarity(input_skills_vector, tfidf_matrix)
    
    sim_scores = list(enumerate(cosine_sim[0]))

    relevant_jobs = [i for i in sim_scores if i[1] >= similarity_threshold]
    relevant_jobs = sorted(relevant_jobs, key=lambda x: x[1], reverse=True)

    job_indices = [i[0] for i in relevant_jobs]
    return jobs_df.iloc[job_indices][['title', 'company', 'location', 'Skills']].to_dict(orient='records')

# Get job recommendations based on skills
@app.get("/recommendations/skills")
def get_skills_based_recommendations(skills: str):
    recommended_jobs = recommend_skills_based_jobs(skills)
    if not recommended_jobs:
        raise HTTPException(status_code=404, detail="No jobs found for the given skills")
    return recommended_jobs

# Add a new job
@app.post("/jobs", response_model=Job)
def add_job(job: Job):
    global job_id_counter
    if not all([job.title, job.company, job.location, job.Experience, job.Skills, job.type, job.salary, job.description]):
        raise HTTPException(status_code=400, detail="All job fields are required")
    job.id = job_id_counter
    jobs_df.loc[len(jobs_df)] = [job.id, job.title, job.company, job.location, job.Experience, job.Skills, job.type, job.salary, job.description, job.category]
    save_jobs(jobs_df)  # Save to CSV whenever a job is added
    job_id_counter += 1
    return job

# Delete a job by ID
@app.delete("/jobs/{job_id}")
def delete_job(job_id: int):
    global jobs_df
    if job_id in jobs_df['id'].values:
        jobs_df.drop(jobs_df[jobs_df['id'] == job_id].index, inplace=True)
        save_jobs(jobs_df)  # Update CSV after deletion
        return {"message": "Job deleted successfully"}
    raise HTTPException(status_code=404, detail="Job not found")
