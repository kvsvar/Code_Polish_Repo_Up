export function parseDynamicRule(ruleString: string) {
    // Dangerous eval in TS
    return eval(ruleString);
}
