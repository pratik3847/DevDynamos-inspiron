# EDI Parser & Validator Backend

A multi-agent, pipeline-based backend for processing US Healthcare EDI transactions using FastAPI and MongoDB.

## Architecture Overview
- **Routes**: Exposed API endpoints (FastAPI).
- **Pipeline**: The workflow orchestrator driving the state model via MongoDB.
- **Agents**: Lightweight phase-handlers that pull/push state into the DB and invoke Services.
- **Services**: Pure business logic (e.g., Parser, Validator, LLM).
