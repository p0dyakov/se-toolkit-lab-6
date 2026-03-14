# Task 4 Plan: VM Deploy & Autochecker Submission

## Goal
Deploy the current `main` application state to the course VM and verify that the deployed service is reachable for autochecker evaluation.

## Scope
- Prepare runtime secrets on VM (autochecker credentials, LMS API key, LLM provider config).
- Build and start Docker Compose stack on VM.
- Verify service health and key endpoints.
- Verify agent can call the local API from VM runtime.
- Record deployment evidence and submission instructions.

## Steps
1. Connect to VM and ensure repository is on branch `4-task-vm-deploy-autochecker-submission`.
2. Configure `.env.docker.secret` and `.env.agent.secret` on VM.
3. Restart stack with `docker compose --env-file .env.docker.secret up -d --build`.
4. Run smoke checks (`/docs`, `/items/`, pipeline sync trigger).
5. Run a local agent CLI check using VM environment variables.
6. Document verification results and required LMS key for chat submission.

## Risks
- Port conflicts with previous lab containers.
- DNS resolution issues in Innopolis network.
- Wrong runtime secret file path or missing env vars.

## Mitigations
- Stop previous lab stacks before deploy.
- If DNS fails, switch VM resolver to public DNS and retry pulls/API calls.
- Keep env files in repo root on VM and run compose from that directory.
