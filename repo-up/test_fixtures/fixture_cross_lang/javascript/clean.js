// JavaScript cross-language fixture — clean.js
import * as crypto from 'crypto';

class UserService {
    constructor() {
        this._store = {};
    }

    authenticate(username, password) {
        const digest = crypto.createHash('sha256').update(password).digest('hex');
        return this._lookup(username, digest);
    }

    _lookup(username, digest) {
        try {
            const stored = this._store[username];
            return stored === digest;
        } catch (err) {
            return false;
        }
    }
}

export default UserService;
