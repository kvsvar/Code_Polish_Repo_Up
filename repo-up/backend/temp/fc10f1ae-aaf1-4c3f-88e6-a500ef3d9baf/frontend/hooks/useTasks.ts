import { TaskService } from '../services/taskService';

export function useTasks() {
    const service = new TaskService();
    return service.getTasks();
}
