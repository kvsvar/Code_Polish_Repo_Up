import { ApiClient } from './apiClient';

export class TaskService {
    private api = new ApiClient();
    
    public getTasks() {
        return this.api.get('/tasks');
    }
}
