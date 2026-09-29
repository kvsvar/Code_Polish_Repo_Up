// sec_bad.ts — Intentionally vulnerable TypeScript fixture for Phase 3 security tests
// WARNING: All secrets are FAKE. This code is intentionally bad for testing.

import * as crypto from 'crypto';
import { exec, execSync } from 'child_process';
import * as fs from 'fs';

// --- CWE-327: Weak Cryptographic Hash ---

function hashData(data: string): string {
    // UNSAFE: MD5 for hashing
    return crypto.createHash('md5').update(data).digest('hex');
}

function weakChecksum(data: string): string {
    // UNSAFE: SHA-1
    return crypto.createHash('sha1').update(data).digest('hex');
}

// --- CWE-78: Dangerous Command Execution ---

function runUserCommand(userInput: string): void {
    // UNSAFE: child_process.exec with user input
    exec(`ls ${userInput}`);
}

function runSync(cmd: string): string {
    // UNSAFE: execSync — synchronous shell
    return execSync(cmd).toString();
}

function dangerousEval(code: string): unknown {
    // UNSAFE: eval on arbitrary input
    return eval(code);
}

// --- CWE-703: Missing Exception Handling ---

async function fetchData(url: string): Promise<unknown> {
    // UNSAFE: fetch without try/catch
    const response = await fetch(url);
    return response.json();
}

function readFileUnsafe(path: string): string {
    // UNSAFE: readFileSync without try/catch
    return fs.readFileSync(path, 'utf8');
}

// --- CWE-798: Hardcoded Secrets (FAKE values) ---
const FAKE_API_TOKEN = "api_key = 'x7kP9mNqR2wL5vB8tH3jE6yF1cA4dG0'";
const FAKE_AWS = "AKIAIOSFODNN7EXAMPLE";

// --- Safe counterparts (should NOT be flagged) ---

function safeHash(data: string): string {
    // SHA-256 is safe
    return crypto.createHash('sha256').update(data).digest('hex');
}

async function safeFetch(url: string): Promise<unknown> {
    try {
        const response = await fetch(url);
        return response.json();
    } catch (err) {
        console.error('Fetch failed:', err);
        return null;
    }
}

function safeReadFile(path: string): string | null {
    try {
        return fs.readFileSync(path, 'utf8');
    } catch (err) {
        return null;
    }
}
