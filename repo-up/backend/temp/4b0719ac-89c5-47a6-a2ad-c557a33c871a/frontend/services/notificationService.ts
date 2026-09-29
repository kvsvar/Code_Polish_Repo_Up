import { ApiClient } from './apiClient';
export class Notificationservice {
    private api = new ApiClient();
    public execute() {
        try {
            return this.api.get('/notificationService');
        } catch(e) {
            console.error(e);
        }
    }
}
