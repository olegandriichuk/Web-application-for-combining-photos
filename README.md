# Web Application for Image Stitching

This README file explains the contents of each folder in the project.

The `backend` folder contains the FastAPI server application. It includes the REST API,
the background worker that processes image stitching jobs, database models, and all
business logic. The worker communicates with [Exposea](https://github.com/DCGM/Exposea) —
an external image stitching CLI — via subprocess.

The `frontend` folder contains the Vue 3 single-page application. It provides the user
interface for managing projects, uploading aerial photos, configuring and submitting
stitching jobs, and viewing results on an interactive map.

The `deploy` folder contains everything needed to build and run the system with Docker.
Docker was chosen due to the project's GPU and ML dependencies, making it a practical
choice for managing them. The folder includes a `Dockerfile`, a `docker-compose.yml` for
orchestrating the `app` and `worker` containers, and a helper script `update.sh` for
common build and run commands. A separate `README.md` in this folder lists all
prerequisites, explains how to set up environment variables, and provides instructions
for both Docker-based deployment and local development without Docker.
