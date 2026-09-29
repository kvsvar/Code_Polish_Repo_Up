import { ApiClient } from './apiClient';
export class Projectservice {
    private api = new ApiClient();
    public execute() {
        try {
            return this.api.get('/projectService');
        } catch(e) {
            console.error(e);
        }
    }
}
