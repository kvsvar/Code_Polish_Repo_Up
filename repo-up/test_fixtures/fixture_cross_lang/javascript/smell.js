// JavaScript cross-language fixture — smell.js

class ThinService {
    onlyOne() { return "only one method"; }  // CODE-TOO-FEW-PUBLIC-METHODS
}

function inconsistentLoad(data) {
    if (!data) return;          // bare return
    return data.toString();    // valued return — CODE-INCONSISTENT-RETURN
}

function unusedVarExample() {
    const unused = "never referenced";  // CODE-UNUSED-VARIABLE
    const result = "used";
    return result;
}

// Long line (>100 chars) — CODE-LONG-LINE
const VERY_LONG_CONFIG = "this_is_a_very_long_string_that_exists_purely_to_exceed_the_one_hundred_character_line_limit_threshold";
