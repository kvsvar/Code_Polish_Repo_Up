// TypeScript cross-language fixture — smell.ts

class ThinService {
    onlyOne(): string { return "only one method"; }  // CODE-TOO-FEW-PUBLIC-METHODS
}

function inconsistentLoad(data: string | null): string | void {
    if (!data) return;           // bare return
    return data.toUpperCase();  // valued return — CODE-INCONSISTENT-RETURN
}

function unusedVarExample(): string {
    const unused = "never referenced";  // CODE-UNUSED-VARIABLE
    const result = "used";
    return result;
}

// Long line (>100 chars) — CODE-LONG-LINE
const VERY_LONG_CONFIG: string = "this_is_a_very_long_string_that_exists_purely_to_exceed_the_one_hundred_character_line_limit_threshold";
