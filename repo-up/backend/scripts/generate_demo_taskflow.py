import os
import zipfile
import shutil

def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

def generate_taskflow(output_dir):
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    # ---------------------------------------------------------
    # BACKEND (PYTHON)
    # ---------------------------------------------------------
    
    # --- Models (Deep Inheritance: Base -> Auditable -> SoftDelete -> Task) ---
    create_file(f"{output_dir}/backend/models/base.py", """
from pydantic import BaseModel as PydanticBase

class BaseModel(PydanticBase):
    id: str
    created_at: str
    updated_at: str
    
    def save(self):
        pass
""")
    create_file(f"{output_dir}/backend/models/auditable.py", """
from backend.models.base import BaseModel

class AuditableModel(BaseModel):
    created_by: str
    updated_by: str
    audit_trail: list = []
    
    def log_audit(self, action: str):
        self.audit_trail.append(action)
""")
    create_file(f"{output_dir}/backend/models/soft_delete.py", """
from backend.models.auditable import AuditableModel

class SoftDeleteModel(AuditableModel):
    is_deleted: bool = False
    deleted_at: str = None
    
    def delete(self):
        self.is_deleted = True
""")
    create_file(f"{output_dir}/backend/models/task.py", """
from backend.models.soft_delete import SoftDeleteModel
from backend.models.user import User
from backend.models.project import Project

class Task(SoftDeleteModel):
    title: str
    description: str
    status: str
    assignee_id: str
    project_id: str
    
    def assign_to(self, user: User):
        self.assignee_id = user.id
""")
    create_file(f"{output_dir}/backend/models/user.py", """
from backend.models.soft_delete import SoftDeleteModel

class User(SoftDeleteModel):
    username: str
    email: str
    password_hash: str
""")
    create_file(f"{output_dir}/backend/models/project.py", """
from backend.models.soft_delete import SoftDeleteModel
from backend.models.user import User

class Project(SoftDeleteModel):
    name: str
    owner_id: str
""")
    create_file(f"{output_dir}/backend/models/comment.py", """
from backend.models.base import BaseModel
from backend.models.task import Task
from backend.models.user import User

class Comment(BaseModel):
    task_id: str
    author_id: str
    content: str
""")
    for model in ['attachment', 'team', 'notification', 'audit_log', 'tag', 'milestone']:
        create_file(f"{output_dir}/backend/models/{model}.py", f"""
from backend.models.base import BaseModel

class {model.capitalize()}(BaseModel):
    name: str
    description: str
""")

    # --- Services (Circular Dep: Task -> Notification -> Audit -> Task) ---
    # TaskService -> NotificationService
    create_file(f"{output_dir}/backend/services/task_service.py", """
from backend.models.task import Task
from backend.services.notification_service import NotificationService
from backend.utils.logger import Logger

class TaskService:
    def __init__(self):
        self.logger = Logger()
        self.notif_service = NotificationService()
        
    def create_task(self, data):
        task = Task(**data)
        self.notif_service.notify_task_created(task)
        self.logger.info(f"Task created: {task.id}")
        return task
""")
    # NotificationService -> AuditService
    create_file(f"{output_dir}/backend/services/notification_service.py", """
from backend.models.notification import Notification
from backend.services.audit_service import AuditService
from backend.utils.logger import Logger

class NotificationService:
    def __init__(self):
        self.audit = AuditService()
        self.logger = Logger()
        
    def notify_task_created(self, task):
        n = Notification(name="Task Created", description=task.title, id="1", created_at="now", updated_at="now")
        self.audit.log_notification(n)
        self.logger.info("Notification sent")
""")
    # AuditService -> TaskService (CIRCULAR)
    create_file(f"{output_dir}/backend/services/audit_service.py", """
from backend.models.audit_log import AuditLog
from backend.services.task_service import TaskService
from backend.utils.logger import Logger

class AuditService:
    def __init__(self):
        self.task_service = TaskService()  # Circular dependency
        self.logger = Logger()
        
    def log_notification(self, notif):
        # might need to fetch task details
        self.logger.info("Logging notification")
""")
    
    # ProjectService (God Class)
    create_file(f"{output_dir}/backend/services/project_service.py", """
from backend.models.project import Project
from backend.utils.logger import Logger

class ProjectService:
    def __init__(self):
        self.logger = Logger()
        
    def create_project(self): pass
    def update_project(self): pass
    def delete_project(self): pass
    def get_project(self): pass
    def list_projects(self): pass
    def add_member(self): pass
    def remove_member(self): pass
    def assign_role(self): pass
    def get_statistics(self): pass
    def generate_report(self): pass
    def export_data(self): pass
    def import_data(self): pass
    def sync_with_external(self): pass
    def archive_project(self): pass
    def unarchive_project(self): pass
    def duplicate_project(self): pass
    def calculate_billing(self): pass
""")

    # EmailService (Hardcoded Secret)
    create_file(f"{output_dir}/backend/services/email_service.py", """
from backend.utils.logger import Logger
import smtplib

class EmailService:
    def __init__(self):
        self.logger = Logger()
        self.api_key = "AKIAIOSFODNN7EXAMPLE" # Hardcoded AWS key
        
    def send_email(self, to, subject, body):
        self.logger.info(f"Sending email to {to}")
        try:
            # IO operation WITH error handling
            pass
        except Exception as e:
            self.logger.error(str(e))
""")

    # FileUploadService (I/O missing try/except)
    create_file(f"{output_dir}/backend/services/file_upload_service.py", """
import os
from backend.utils.logger import Logger

class FileUploadService:
    def __init__(self):
        self.logger = Logger()
        
    def upload_file(self, filename, content):
        # Missing try/except for file I/O
        with open(filename, 'w') as f:
            f.write(content)
        self.logger.info("File uploaded")
""")

    # WebhookService (I/O missing try/except)
    create_file(f"{output_dir}/backend/services/webhook_service.py", """
import requests
from backend.utils.logger import Logger

class WebhookService:
    def __init__(self):
        self.logger = Logger()
        self.webhook_secret = "token='a1b2c3d4e5f6g7h8i9j0'" # Another secret
        
    def trigger(self, url, payload):
        # Missing try/except for network I/O
        res = requests.post(url, json=payload)
        self.logger.info(f"Webhook triggered: {res.status_code}")
""")

    # IntegrationService (Eval usage - High severity)
    create_file(f"{output_dir}/backend/services/integration_service.py", """
from backend.utils.logger import Logger

class IntegrationService:
    def __init__(self):
        self.logger = Logger()
        
    def load_dynamic_plugin(self, plugin_code):
        self.logger.info("Loading plugin dynamically")
        # Dangerous eval
        eval(plugin_code)
""")

    # Other basic services
    for srv in ['auth_service', 'search_service', 'report_service']:
        create_file(f"{output_dir}/backend/services/{srv}.py", f"""
from backend.utils.logger import Logger

class {srv.capitalize().replace('_', '')}:
    def __init__(self):
        self.logger = Logger()
        
    def execute(self):
        self.logger.info("Executing {srv}")
""")

    # --- Routes ---
    for route in ['user', 'project', 'task', 'comment', 'team', 'notification', 'audit', 'search']:
        create_file(f"{output_dir}/backend/routes/{route}_routes.py", f"""
from backend.services.{route if route in ['user','project','task','notification','audit','search'] else 'task'}_service import {route.capitalize() if route in ['user','project','task','notification','audit','search'] else 'Task'}Service

def register_routes(app):
    app.add_route('/{route}', lambda: "OK")
""")

    # --- Utils ---
    create_file(f"{output_dir}/backend/utils/logger.py", """
class Logger:
    def info(self, msg): print(f"INFO: {msg}")
    def error(self, msg): print(f"ERROR: {msg}")
""")
    create_file(f"{output_dir}/backend/utils/validator.py", """
def validate_email(email): return "@" in email
""")
    create_file(f"{output_dir}/backend/utils/config_loader.py", """
import json
import os

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {}
""")
    create_file(f"{output_dir}/backend/utils/date_helper.py", "def now(): return '2023-01-01'")
    create_file(f"{output_dir}/backend/utils/cache.py", "class Cache: pass")
    create_file(f"{output_dir}/backend/utils/rate_limiter.py", "class RateLimiter: pass")
    
    # Legitimate eval config script
    create_file(f"{output_dir}/backend/build_config.py", """
# Build script configuration
def compile_config(expression):
    # Legitimate config eval
    return eval(expression)
""")

    # --- DB ---
    create_file(f"{output_dir}/backend/db/connection.py", """
import sqlite3
def get_db():
    try:
        conn = sqlite3.connect('app.db')
        return conn
    except Exception as e:
        print(e)
""")
    create_file(f"{output_dir}/backend/db/migrations.py", "def run_migrations(): pass")

    create_file(f"{output_dir}/backend/config.py", """
# Hub node
DB_URI = "sqlite:///:memory:"
API_PORT = 8000
""")
    
    # Committed .env and .env.example
    create_file(f"{output_dir}/backend/.env.example", "DB_PASS=your_password_here\n")
    create_file(f"{output_dir}/backend/.env", "DB_PASS=super_secret_prod_password_123\n")


    # ---------------------------------------------------------
    # FRONTEND (TYPESCRIPT)
    # ---------------------------------------------------------
    
    # --- Services (Circular Dep: useTasks -> taskService -> apiClient -> useTasks) ---
    create_file(f"{output_dir}/frontend/services/apiClient.ts", """
import { useTasks } from '../hooks/useTasks';

export class ApiClient {
    public get(url: string) {
        // Circular reference to useTasks
        const tasks = useTasks();
        return fetch(url); // missing try/catch for fetch
    }
}
""")
    create_file(f"{output_dir}/frontend/services/taskService.ts", """
import { ApiClient } from './apiClient';

export class TaskService {
    private api = new ApiClient();
    
    public getTasks() {
        return this.api.get('/tasks');
    }
}
""")
    create_file(f"{output_dir}/frontend/hooks/useTasks.ts", """
import { TaskService } from '../services/taskService';

export function useTasks() {
    const service = new TaskService();
    return service.getTasks();
}
""")
    
    # Other frontend services
    for srv in ['authService', 'projectService', 'notificationService']:
        create_file(f"{output_dir}/frontend/services/{srv}.ts", f"""
import {{ ApiClient }} from './apiClient';
export class {srv.capitalize()} {{
    private api = new ApiClient();
    public execute() {{
        try {{
            return this.api.get('/{srv}');
        }} catch(e) {{
            console.error(e);
        }}
    }}
}}
""")

    # --- Hooks ---
    create_file(f"{output_dir}/frontend/hooks/useAuth.ts", """
import { AuthService } from '../services/authService';
export function useAuth() { return new AuthService(); }
""")
    create_file(f"{output_dir}/frontend/hooks/useNotifications.ts", """
import { NotificationService } from '../services/notificationService';
export function useNotifications() { return new NotificationService(); }
""")
    create_file(f"{output_dir}/frontend/hooks/useDebounce.ts", "export function useDebounce(val: any) { return val; }")

    # --- Components ---
    # God component
    create_file(f"{output_dir}/frontend/components/ProjectBoard.tsx", """
import { TaskCard } from './TaskCard';
import { useTasks } from '../hooks/useTasks';

export class ProjectBoard {
    render() {}
    handleDrag() {}
    handleDrop() {}
    sortTasks() {}
    filterTasks() {}
    groupByAssignee() {}
    groupByStatus() {}
    exportToCSV() {}
    importFromCSV() {}
    printBoard() {}
    shareBoard() {}
    archiveCompleted() {}
    changeTheme() {}
    sendNotifications() {}
    calculateProgress() {}
    openSettings() {}
    closeSettings() {}
}
""")
    create_file(f"{output_dir}/frontend/components/TaskCard.tsx", """
import { UserAvatar } from './UserAvatar';
export class TaskCard { render() {} }
""")
    create_file(f"{output_dir}/frontend/components/UserAvatar.tsx", "export class UserAvatar { render() {} }")
    
    for comp in ['CommentThread', 'NotificationBell', 'Sidebar', 'Header', 'Modal', 'FormInput', 'Dropdown', 'FileUploader', 'SearchBar']:
        create_file(f"{output_dir}/frontend/components/{comp}.tsx", f"export class {comp} {{ render() {{}} }}")

    # --- Utils (Eval usage) ---
    create_file(f"{output_dir}/frontend/utils/dynamicParser.ts", """
export function parseDynamicRule(ruleString: string) {
    // Dangerous eval in TS
    return eval(ruleString);
}
""")
    create_file(f"{output_dir}/frontend/utils/formatters.ts", "export function formatDate(d: Date) { return d.toISOString(); }")
    create_file(f"{output_dir}/frontend/utils/validators.ts", "export function isEmail(s: string) { return s.includes('@'); }")
    create_file(f"{output_dir}/frontend/utils/constants.ts", "export const API_URL = 'http://localhost:8000';")


    # ---------------------------------------------------------
    # README
    # ---------------------------------------------------------
    create_file(f"{output_dir}/README.md", """
# TaskFlow Demo Repository

This is a realistic demo repository designed to showcase Repo-Up's analysis pipeline.
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
""")

    # Zip the directory
    zip_path = output_dir + ".zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)

    print(f"Generated {sum([len(files) for r, d, files in os.walk(output_dir)])} files in {output_dir}")
    print(f"Zipped to {zip_path}")

if __name__ == "__main__":
    generate_taskflow("e:/Mini_project/repo-up/test_fixtures/demo_taskflow")
