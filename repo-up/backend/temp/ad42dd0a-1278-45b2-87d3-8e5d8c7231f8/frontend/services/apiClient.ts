import { useTasks } from '../hooks/useTasks';

export class ApiClient {
    public get(url: string) {
        // Circular reference to useTasks
        const tasks = useTasks();
        return fetch(url); // missing try/catch for fetch
    }
}
