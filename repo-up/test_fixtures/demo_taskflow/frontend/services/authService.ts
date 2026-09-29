import { ApiClient } from './apiClient';
export class Authservice {
    private api = new ApiClient();
    public execute() {
        try {
            return this.api.get('/authService');
        } catch(e) {
            console.error(e);
        }
    }
}
