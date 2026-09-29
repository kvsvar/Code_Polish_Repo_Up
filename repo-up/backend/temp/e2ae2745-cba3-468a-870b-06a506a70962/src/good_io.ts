import * as fs from 'fs';
export function readFile() {
    try {
        fs.readFileSync('test.txt');
    } catch(e) {}
}
