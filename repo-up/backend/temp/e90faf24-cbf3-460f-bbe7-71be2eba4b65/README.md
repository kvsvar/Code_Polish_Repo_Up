# TaskFlow Demo Repository

This is a realistic demo repository designed to showcase CodePolish's analysis pipeline.
It contains both a Python backend and a TypeScript frontend.

## Embedded Issues Documented:

### Structural Issues
1. **Circular Dependency (Backend)**: `backend/services/task_service.py` -> `notification_service.py` -> `audit_service.py` -> `task_service.py`
2. **Circular Dependency (Frontend)**: `frontend/hooks/useTasks.ts` -> `frontend/services/taskService.ts` -> `frontend/services/apiClient.ts` -> `frontend/hooks/useTasks.ts`
3. **God Class (Backend)**: `ProjectService` in `backend/services/project_service.py` (17 methods)
4. **God Class (Frontend)**: `ProjectBoard` in `frontend/components/ProjectBoard.tsx` (17 methods)
5. **Deep Inheritance (Backend)**: `BaseModel` -> `AuditableModel` -> `SoftDeleteModel` -> `Task` (4 levels) in `backend/models/task.py`

### Security / Error Handling
6. **Committed Environment File**: `backend/.env` contains fake credentials alongside `.env.example`.
7. **Hardcoded Secrets**: `backend/services/email_service.py` (AWS Key) and `backend/services/webhook_service.py` (API Token).
8. **Missing Error Handling (I/O)**: `backend/services/file_upload_service.py`, `backend/services/webhook_service.py`, and `frontend/services/apiClient.ts`.
9. **Proper Error Handling (Good)**: `backend/services/email_service.py` and `frontend/services/projectService.ts` contain try/catch.
10. **Dangerous Eval Usage**: `backend/services/integration_service.py` and `frontend/utils/dynamicParser.ts`.
11. **Legitimate Eval Usage**: `backend/build_config.py` (build context).
