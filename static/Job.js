document.addEventListener("DOMContentLoaded", function () {
    // Elements
    const jobForm = document.getElementById("add-job-form");
    const jobListContainer = document.getElementById("job-list");
    const filterForm = document.getElementById("filter-form");
    const recommendationsContainer = document.getElementById("recommendations");

    // Fetch all jobs and display them
    async function fetchJobs() {
        const response = await fetch("http://localhost:8000/jobs");
        const jobs = await response.json();
        displayJobs(jobs);
    }

    // Display jobs in the job list
    function displayJobs(jobs) {
        jobListContainer.innerHTML = ""; // Clear previous jobs
        jobs.forEach(job => {
            const jobElement = document.createElement("div");
            jobElement.classList.add("job");
            jobElement.innerHTML = `
                <h3>${job.title}</h3>
                <p><strong>Company:</strong> ${job.company}</p>
                <p><strong>Location:</strong> ${job.location}</p>
                <p><strong>Experience:</strong> ${job.Experience}</p>
                <p><strong>Skills:</strong> ${job.Skills}</p>
                <p><strong>Type:</strong> ${job.type}</p>
                <p><strong>Salary:</strong> ${job.salary}</p>
                <p><strong>Description:</strong> ${job.description}</p>
                <p><strong>Category:</strong> ${job.category || "N/A"}</p>
                <button onclick="deleteJob(${job.id})">Delete Job</button>
            `;
            jobListContainer.appendChild(jobElement);
        });
    }

    // Handle adding a job
    jobForm.addEventListener("submit", async function (event) {
        event.preventDefault(); // Prevent default form submission

        const jobData = {
            title: document.getElementById("title").value,
            company: document.getElementById("company").value,
            location: document.getElementById("location").value,
            Experience: document.getElementById("Experience").value,
            Skills: document.getElementById("Skills").value,
            type: document.getElementById("type").value,
            salary: document.getElementById("salary").value,
            description: document.getElementById("description").value,
            category: document.getElementById("category").value,
        };

        try {
            const response = await fetch("http://localhost:8000/jobs", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(jobData),
            });

            if (!response.ok) {
                throw new Error("Failed to add job");
            }

            const addedJob = await response.json();
            console.log("Job added:", addedJob);
            fetchJobs(); // Refresh the job list

        } catch (error) {
            console.error("Error adding job:", error);
        }
    });

    // Fetch jobs when the page loads
    fetchJobs();

    // Handle filtering jobs
    filterForm.addEventListener("submit", async function (event) {
        event.preventDefault();

        const jobType = document.getElementById("filter-type").value;
        const location = document.getElementById("filter-location").value;
        const category = document.getElementById("filter-category").value;

        // Create URLSearchParams only for non-empty fields
        const params = new URLSearchParams();
        if (jobType) params.append('job_type', jobType);
        if (location) params.append('location', location);
        if (category) params.append('category', category);

        try {
            const response = await fetch(`http://localhost:8000/jobs?${params}`);
            if (!response.ok) {
                throw new Error("Failed to fetch filtered jobs");
            }
            const filteredJobs = await response.json();
            displayJobs(filteredJobs);
        } catch (error) {
            console.error("Error fetching filtered jobs:", error);
        }
    });

    // Fetch job recommendations based on title
    async function recommendJobsByTitle() {
        const jobTitle = document.getElementById("recommendation-title").value;
        const response = await fetch(`http://localhost:8000/recommendations/jobs?job_title=${jobTitle}`);

        if (response.ok) {
            const recommendedJobs = await response.json();
            displayRecommendations(recommendedJobs);
        } else {
            const error = await response.json();
            console.error(error.detail);
        }
    }

    // Fetch job recommendations based on skills
    async function recommendJobsBySkills() {
        const skills = document.getElementById("recommendation-skills").value;
        const response = await fetch(`http://localhost:8000/recommendations/skills?skills=${skills}`);

        if (response.ok) {
            const recommendedJobs = await response.json();
            displayRecommendations(recommendedJobs);
        } else {
            const error = await response.json();
            console.error(error.detail);
        }
    }

    function displayRecommendations(recommendedJobs) {
        recommendationsContainer.innerHTML = ""; // Clear previous recommendations
        recommendedJobs.forEach(job => {
            const jobElement = document.createElement("div");
            jobElement.classList.add("recommendation");
            
            // Ensure the correct field for skills is displayed
            const jobSkills = job.skills || job.Skills || "Not specified";
    
            jobElement.innerHTML = `
                <h4>${job.title}</h4>
                <p><strong>Company:</strong> ${job.company}</p>
                <p><strong>Location:</strong> ${job.location}</p>
                <p><strong>Skills:</strong> ${jobSkills}</p>
            `;
            recommendationsContainer.appendChild(jobElement);
        });
    }
    

    // Delete job function
    window.deleteJob = async function(jobId) {
        if (confirm("Are you sure you want to delete this job?")) {
            try {
                const response = await fetch(`http://localhost:8000/jobs/${jobId}`, {
                    method: "DELETE",
                });

                if (!response.ok) {
                    throw new Error("Failed to delete job");
                }

                console.log("Job deleted successfully");
                fetchJobs(); // Refresh job list

            } catch (error) {
                console.error("Error deleting job:", error);
            }
        }
    }

    // Event listeners for recommendations
    document.getElementById("recommend-by-title").addEventListener("click", recommendJobsByTitle);
    document.getElementById("recommend-by-skills").addEventListener("click", recommendJobsBySkills);
});
