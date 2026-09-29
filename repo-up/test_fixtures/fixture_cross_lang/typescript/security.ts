// TypeScript cross-language fixture — security.ts
import * as crypto from 'crypto';
import { exec } from 'child_process';
import * as fs from 'fs';

// Weak crypto — SEC-WEAK-CRYPTO
function hashIt(data: string): string {
    return crypto.createHash('sha1').update(data).digest('hex');
}

// Dangerous execution — SEC-DANGEROUS-EXEC
function runCmd(cmd: string): void {
    exec(cmd);
}

// Eval — SEC-DANGEROUS-EXEC (CWE-95)
function runCode(code: string): unknown {
    return eval(code);
}

// Missing exception handling — SEC-CWE-703
function readData(path: string): string {
    return fs.readFileSync(path, 'utf8');
}

// Fake secret — SEC-HARDCODED-SECRET (FAKE value)
const FAKE_API_KEY: string = "api_key = 'x7kP9mNqR2wL5vB8tH3jE6yF1cA4dG0'";
