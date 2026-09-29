// smell_bad.ts — intentional code smell fixture for TypeScript smell rules
// This file is intentionally bad for testing purposes.

// Too-few-public-methods: class with only 1 public method
class TinyHelper {
    compute(): number {
        return 42;
    }
}

// Inconsistent return: sometimes returns value, sometimes bare return
function inconsistentLoad(data: string | null): string | void {
    if (data === null) {
        return;  // bare return
    }
    if (data === "error") {
        return;  // another bare return
    }
    const result = data.toUpperCase();
    return result;  // valued return
}

// Long line (over 100 characters intentionally)
const aVeryLongVariableNameThatExceedsOneHundredCharactersWhenThisValueIsAssigned = "some long string value that makes this exceed the limit";

// Unused variable in a function
function unusedVarExample(): string {
    const unused = "never used";
    const working = "used";
    return working;
}

// Duplicate structure (structural clone of cloneA)
function cloneA(x: number): number {
    let result = x * 2;
    result = result + 10;
    result = result - 5;
    return result;
}

function cloneB(y: number): number {
    let result = y * 2;
    result = result + 10;
    result = result - 5;
    return result;
}

// Clean function — no smells
function cleanCompute(value: number): number {
    return value * 2;
}
