#!/usr/bin/env python3
"""Translate a self-contained MQL5 Expert Advisor into C++ for the MQL5 emulator.

The translation is line-preserving (a #line directive maps every compiler
diagnostic back to the original .mq5 line).  Besides translating, it lints the
source for constructs that are valid C++ but NOT valid MQL5, so that a clean
C++ build is a strong indication that MetaEditor will compile the file too.

usage: translate.py input.mq5 output.cpp [--strict]
  --strict : inputs become `const` (detects writes to input variables, which
             MQL5 forbids); used for the compile-only check.
"""
import re
import sys

MQL_TYPES = r"(?:bool|char|uchar|short|ushort|int|uint|long|ulong|float|double|string|datetime|color|Mql\w+|ENUM_\w+|[A-Z]\w*)"
BUILTIN_STRUCTS = {"MqlTick", "MqlRates", "MqlDateTime", "MqlTradeRequest", "MqlTradeResult",
                   "MqlTradeCheckResult", "MqlCalendarValue", "MqlCalendarEvent", "MqlCalendarCountry",
                   "MqlBookInfo", "MqlTradeTransaction", "MqlParam"}
FORBIDDEN = [
    (r"->", "operator -> does not exist in MQL5 (use '.')"),
    (r"\bstd::", "no C++ standard library in MQL5"),
    (r"\bnullptr\b", "use NULL in MQL5"),
    (r"\bauto\b", "'auto' is not MQL5"),
    (r"\btemplate\s*<", "avoid templates (not needed)"),
    (r"\btypename\b", "'typename' is not MQL5"),
    (r"\b(static|reinterpret|const|dynamic)_cast\b", "C++ casts are not MQL5"),
    (r"\bnamespace\b", "namespaces are not used"),
    (r"\busing\b", "'using' is not MQL5"),
    (r"\bnew\s+\w", "dynamic allocation avoided"),
    (r"\bdelete\s+\w", "dynamic allocation avoided"),
    (r"\blong\s+long\b", "'long long' is not MQL5 (long is 64-bit)"),
    (r"\bunsigned\b", "'unsigned' is not MQL5 (use uint/ulong/...)"),
    (r"\bgoto\b", "'goto' is not MQL5"),
    (r"\bconstexpr\b", "'constexpr' is not MQL5"),
    (r"\bnoexcept\b", "'noexcept' is not MQL5"),
    (r"\bthrow\b|\btry\b|\bcatch\b", "no exceptions in MQL5"),
    (r"\[\s*[&=]?\s*\]\s*\(", "no lambdas in MQL5"),
    (r"\bthis\s*->", "use this. in MQL5"),
    (r"\bC'|\bD'", "color/date literals not supported by the emulator"),
    (r"#\s*include", "the EA must be self-contained for the emulator"),
    (r"\bsizeof\s*\(\s*string", "sizeof(string) differs in MQL5"),
]


def mask_strings_and_comments(line, in_block):
    """Return (code_only_line_with_strings_blanked, still_in_block_comment)."""
    out = []
    i = 0
    n = len(line)
    while i < n:
        if in_block:
            j = line.find("*/", i)
            if j < 0:
                out.append(" " * (n - i)); i = n; break
            out.append(" " * (j + 2 - i)); i = j + 2; in_block = False; continue
        c = line[i]
        if line.startswith("//", i):
            out.append(" " * (n - i)); break
        if line.startswith("/*", i):
            in_block = True; out.append("  "); i += 2; continue
        if c == '"':
            j = i + 1
            while j < n and line[j] != '"':
                j += 2 if line[j] == "\\" else 1
            out.append('"' + "_" * (j - i - 1) + '"'); i = j + 1; continue
        if c == "'":
            j = i + 1
            while j < n and line[j] != "'":
                j += 2 if line[j] == "\\" else 1
            out.append("'" + "_" * (j - i - 1) + "'"); i = j + 1; continue
        out.append(c); i += 1
    return "".join(out), in_block


def wrap_string_literals(line, masked):
    """Wrap every "..." literal (found via the masked line) into S_("...")."""
    res = []
    i = 0
    for m in re.finditer(r'"_*"', masked):
        s, e = m.span()
        res.append(line[i:s]); res.append("S_(" + line[s:e] + ")"); i = e
    res.append(line[i:])
    return "".join(res)


def translate(src, strict):
    lines = src.split("\n")
    out = []
    errors = []
    in_block = False
    depth = 0
    struct_stack = []          # brace depth at which a struct/class body starts
    user_structs = set(re.findall(r"\b(?:struct|class)\s+(\w+)", src))
    struct_names = BUILTIN_STRUCTS | user_structs
    handlers = []
    for idx, line in enumerate(lines, start=1):
        masked, in_block_after = mask_strings_and_comments(line, in_block)
        code = masked
        stripped = code.strip()
        in_block = in_block_after
        for pat, why in FORBIDDEN:
            if re.search(pat, code):
                errors.append(f"{idx}: {why}: {line.strip()}")
        # in-class member initialisers are not allowed in MQL5
        if struct_stack and depth == struct_stack[-1] + 1:
            if re.match(r"^\s*(?:static\s+)?(?:const\s+)?" + MQL_TYPES + r"\s+\w+\s*=", code) and "(" not in code.split("=")[0]:
                errors.append(f"{idx}: member initialisers inside struct/class are not MQL5: {line.strip()}")
        # objects (structs) must be passed by reference
        for m in re.finditer(r"[(,]\s*(?:const\s+)?(\w+)\s+(\w+)\s*(?=[,)])", code):
            if m.group(1) in struct_names and re.match(r"^\s*(?:\w+\s+)+\w+\s*\(", code):
                errors.append(f"{idx}: struct parameter '{m.group(2)}' must be passed by reference in MQL5")
        # local reference variables do not exist in MQL5
        if depth > 0 and re.match(r"^\s*(?:const\s+)?\w+\s*&\s*\w+\s*=", code):
            errors.append(f"{idx}: reference variables are not MQL5: {line.strip()}")
        for m in re.finditer(r"\b(OnInit|OnDeinit|OnTick|OnTimer|OnTester|OnTrade|OnTradeTransaction|OnChartEvent)\s*\(", code):
            if re.match(r"^\s*(?:int|void|double)\s+" + m.group(1), code):
                handlers.append(m.group(1))
        # track structure bodies / brace depth
        if re.match(r"^\s*(struct|class)\s+\w+", code) and ";" not in code:
            struct_stack.append(depth)
        opened = code.count("{"); closed = code.count("}")
        depth += opened - closed
        while struct_stack and depth <= struct_stack[-1] and closed:
            struct_stack.pop()

        new = line
        if stripped.startswith("#property"):
            new = ""
        elif re.match(r"^\s*input\s+group\b", code):
            new = ""
        else:
            m = re.match(r"^(\s*)(?:input|sinput)\s+(.*?)\b(\w+)\s*=(.*?);", code)
            if m:
                typ, name = m.group(2).strip(), m.group(3)
                value = line[m.start(4):m.end(4)]
                rest_comment = line[m.end(0):]
                if strict:
                    new = f"{m.group(1)}const {typ} {name} ={value}; {rest_comment}"
                else:
                    new = f"{m.group(1)}{typ} {name} ={value}; REG_INPUT({name}) {rest_comment}"
                masked2, _ = mask_strings_and_comments(new, False)
                new = wrap_string_literals(new, masked2)
                out.append(new)
                continue
            # dynamic array parameters:  TYPE &name[]  ->  MqlArray<TYPE> &name
            new_masked = masked
            pat_param = re.compile(r"(\bconst\s+)?\b(\w+)\s*&\s*(\w+)\s*\[\s*\]")
            pat_decl = re.compile(r"\b(" + MQL_TYPES + r")\s+(\w+)\s*\[\s*\]")
            def apply(p, repl, text, msk):
                res = []; i = 0
                for mm in p.finditer(msk):
                    res.append(text[i:mm.start()]); res.append(repl(mm)); i = mm.end()
                res.append(text[i:])
                return "".join(res)
            new = apply(pat_param, lambda mm: f"{mm.group(1) or ''}MqlArray<{mm.group(2)}> &{mm.group(3)}", new, new_masked)
            new_masked, _ = mask_strings_and_comments(new, False) if not in_block else (new, True)
            new = apply(pat_decl, lambda mm: f"MqlArray<{mm.group(1)}> {mm.group(2)}", new, new_masked)
            new_masked, _ = mask_strings_and_comments(new, False) if not in_block else (new, True)
            if re.search(r'"_*"', new_masked):
                new = wrap_string_literals(new, new_masked)
        out.append(new)
    return "\n".join(out), errors, sorted(set(handlers))


def main():
    if len(sys.argv) < 3:
        print(__doc__); sys.exit(2)
    src = open(sys.argv[1], encoding="utf-8-sig").read().replace("\r\n", "\n")
    strict = "--strict" in sys.argv
    body, errors, handlers = translate(src, strict)
    if errors:
        print("MQL5 compatibility lint FAILED:")
        for e in errors:
            print("  line", e)
        sys.exit(1)
    hdr = ["// generated by translate.py - do not edit"]
    for h in handlers:
        hdr.append(f"#define HAS_{h.upper()} 1")
    hdr.append("#pragma GCC diagnostic push")
    for w in ["-Wconversion", "-Wsign-conversion", "-Wshadow", "-Wfloat-conversion", "-Wsign-compare",
              "-Wunused-variable", "-Wunused-but-set-variable", "-Wuninitialized", "-Wmaybe-uninitialized",
              "-Wparentheses", "-Wreturn-type", "-Wswitch", "-Wimplicit-fallthrough", "-Wdangling-else",
              "-Wempty-body", "-Wfloat-equal"]:
        if w == "-Wfloat-equal":
            continue  # MQL5 does not warn on float equality
        hdr.append(f'#pragma GCC diagnostic error "{w}"')
    hdr.append(f'#line 1 "{sys.argv[1]}"')
    open(sys.argv[2], "w").write("\n".join(hdr) + "\n" + body + "\n#pragma GCC diagnostic pop\n")
    print(f"translated OK ({len(body.splitlines())} lines, handlers: {', '.join(handlers)})")


if __name__ == "__main__":
    main()
