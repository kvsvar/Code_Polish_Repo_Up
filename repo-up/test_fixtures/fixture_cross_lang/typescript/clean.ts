// TypeScript cross-language fixture — clean.ts
import * as crypto from 'crypto';

class UserService {
    private store: Map<string, string> = new Map();

    authenticate(username: string, password: string): boolean {
        const digest = crypto.createHash('sha256').update(password).digest('hex');
        return this._lookup(username, digest);
    }

    private _lookup(username: string, digest: string): boolean {
        try {
            return this.store.get(username) === digest;
        } catch {
            return false;
        }
    }
}

export default UserService;
