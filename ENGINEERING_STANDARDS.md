# Engineering Standards

## Purpose

This document defines simple engineering standards used in this project.

## 1) Naming Conventions

- Use clear, descriptive names for files, variables, and functions.
- Frontend (TypeScript/React):
  - Components in `PascalCase`.
  - Variables/functions in `camelCase`.
- Backend (Python):
  - Modules/functions/variables in `snake_case`.
  - Classes in `PascalCase`.

## 2) Project Structure

- Keep frontend code under `frontend/src` by feature and responsibility.
- Keep backend code under `backend/app` with clear layers:
  - `api/` for routes,
  - `services/` for domain logic,
  - `models/` for schemas,
  - `core/` for configuration/dependencies.

## 3) Documentation

- Keep README sections updated when behavior changes.
- Add short docstrings/comments for non-obvious logic.
- Record important architecture or design trade-offs in markdown docs.

## 4) Code Quality

- Prefer small, focused functions.
- Avoid duplicated logic where practical.
- Validate user input at API boundaries.
- Keep error messages actionable and safe.

## 5) Testing

- Add or update tests for changed behavior.
- Keep unit tests fast and deterministic.
- Separate optional live-provider tests from default CI tests.

## 6) Security and Secrets

- Never hardcode credentials or API keys.
- Use environment variables for secrets.
- Apply least-privilege principles for external services.

## 7) Review and Change Control

- Review generated code before merge.
- Keep commits small and focused.
- Prefer readability and maintainability over premature optimization.

## 8) Standards Intentionally Skipped (for now)

- Full formal ADR process for every design choice (kept lightweight in this phase).
- Strict SLA/SLO error-budget governance (planned when moving to production).
- Mandatory end-to-end performance benchmarking in CI (deferred due to scope/time).
