COMMIT_MESSAGE: Add ticket satisfaction feedback and supervisor reviews

## Summary
- Added one-to-one MySQL feedback persistence, submission workflow, agent satisfaction reporting, and supervisor low-rated/pending-feedback reviews.
- Added DTOs, service/repository layers, role-aware principal dependency, idempotent feedback storage startup integration, and customer association support for tickets.
- Documented all feedback routes and pagination behavior.

## Verification
- `python -m compileall app` passed using the repository's pinned dependencies.
- `python -c "from app.main import app; assert app is not None"` passed using the repository's pinned dependencies.
- No automated test framework is configured, so no test suite was added or run.
- The deployment script was boot-attempted 3/3 times using a non-conflicting port. Each attempt reached FastAPI startup but failed because MySQL at `localhost:3310` refused the connection; Docker daemon access was unavailable for Compose and Dockerfile build-run verification.

## Deployment
- Existing Dockerfile and docker-compose.yml remain the service and MySQL deployment artifacts.
- Added `start_job-d70b6efb-f274-4cd0-8156-fb8858a7fcdd.sh` as the deployment entry point.
