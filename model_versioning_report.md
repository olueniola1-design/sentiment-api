\# Model Versioning and Rollback Strategy



\## Model Versioning

Our model and API are versioned using Docker image tags and GitHub commit hashes. 

\- Every time code is pushed to the `main` branch, a specific version tag (e.g., `v1.0.0`) should be assigned to the Docker image before pushing to Docker Hub.

\- `olueniola1/sentiment-api:latest` represents the most recent stable build, but immutable tags (like `olueniola1/sentiment-api:v1.0`) are used in the Kubernetes deployment file for trackability.



\## Rollback Procedure

If a newly deployed model version contains bugs or regressions, we can roll back to the previous stable version using Kubernetes with zero downtime.



To roll back to the previous deployment state, use the following Kubernetes command:

`kubectl rollout undo deployment/sentiment-api-deployment`



To manually roll back to a specific, older Docker image tag (e.g., v1.0), use:

`kubectl set image deployment/sentiment-api-deployment sentiment-api=olueniola1/sentiment-api:v1.0`

