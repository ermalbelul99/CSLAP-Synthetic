"""Cross-check the two blind anchor extractions against W/evidence/ANCHOR_SPEC.md (P1 step 2, DBR).

Modes
-----
``compare_anchors.py [--root DIR]``               Compares ``W/evidence/anchors.json`` (A) with
                                                    ``W/evidence/independent/anchors_B.json`` (B).
``compare_anchors.py --documents [--root DIR]``    Compares ``W/evidence/independent/
                                                    document_values_A.json`` with
                                                    ``document_values_B.json``, and checks the
                                                    merged ``W/evidence/document_values.json``.

Both modes derive their required-key list at run time by parsing the governing spec file
(``ANCHOR_SPEC.md`` or ``DOCUMENT_VALUES_SPEC.md``) found under the given ``--root``, rather than
hard-coding the real repository's (much larger) key set. That is what lets a small fixture tree
ship its own miniature spec and exercise this script's comparison logic without needing hundreds of
keys (P1 check-author brief, "Part A fixtures": under 50 keys, under 20 lines per file).

Root argument
-------------
``--root`` defaults to the repository root, computed as ``Path(__file__).resolve().parents[4]``
from this script's location under ``W/tools/``. Whichever root is used -- default or explicit --
is confirmed by checking that ``<root>/reports/horizon_robustness_results/
WRITING_ORCHESTRATION_PLAN_20260914.md`` exists, a plain file-existence check that never invokes
git (user decision U8).

This script performs no writes and starts no subprocess.

Fix round 1 (P1 seq 31), findings fixed here: F-045, F-046, F-047, F-048, F-049, F-050, F-051,
F-055 (spec-cell escaped pipe, unknown anchor keys), Q-012, Q-013, Q-015. Each change below carries
a short comment naming the finding.
"""
from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

W_REL = "reports/horizon_robustness_results/writing"
ROOT_MARKER_REL = "reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md"

N_VALUES = ["10937", "21874", "43748"]  # <n>: fixed by the P1 check-author brief, item 1.

FRAGMENT_RE = re.compile(r"`([^`]+)`")
PLACEHOLDER_RE = re.compile(r"<(ARM|SEED|H|DELTA|n)>")
SECTION_HEAD_RE = re.compile(r"^##\s+([A-E])\.", re.MULTILINE)
FOR_WORD_RE = re.compile(r"\bfor\b")


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def resolve_root(root_arg: str | None) -> Path:
    script_path = Path(__file__).resolve()
    return Path(root_arg).resolve() if root_arg else script_path.parents[4]


def root_confirmed(root: Path) -> bool:
    # Confirms the resolved root (default or explicit) is plausibly the repository root, without
    # ever running git (U8). A fixture root carries its own tiny stub of this marker file.
    return (root / ROOT_MARKER_REL).is_file()


def load_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def try_parse_fraction(text: str) -> Fraction | None:
    s = text.strip()
    try:
        if "/" in s:
            p, q = s.split("/", 1)
            return Fraction(int(p.strip()), int(q.strip()))
        return Fraction(int(s))
    except (ValueError, ZeroDivisionError):
        return None


# ---------------------------------------------------------------------------
# ANCHOR_SPEC.md parsing
# ---------------------------------------------------------------------------

def parse_conventions(spec_text: str) -> tuple[list[str], list[str]]:
    """Extract the global arm-token and seed lists from the spec's Conventions section, e.g.
    '**Arm tokens.** NOM, TIGHT, HIST_ACT (stored `HIST+ACT`), HIST_ACT_T (stored `HIST+ACT-T`),
    HIST. Seeds are `s11`, `s22`, `s33`.'"""
    m = re.search(r"\*\*Arm tokens\.\*\*\s*(.+?)\.\s*Seeds are\s*(.+?)\.", spec_text, re.DOTALL)
    if not m:
        return [], []
    arm_text = re.sub(r"\([^)]*\)", "", m.group(1))
    arms = [tok.strip(" `") for tok in arm_text.split(",") if tok.strip(" `")]
    seeds = [tok.strip(" `") for tok in m.group(2).split(",") if tok.strip(" `")]
    return arms, seeds


def parse_r_mapping(spec_text: str) -> str:
    m = re.search(r"`R`\s*=\s*`([^`]+)`", spec_text)
    return m.group(1) if m else "reports/horizon_robustness_results"


ALLOWED_INPUTS_BLOCK_RE = re.compile(r"\*\*Allowed inputs\.\*\*[^\n]*\n(.*?)(?:\n\s*\n|\Z)", re.DOTALL)


def parse_anchor_allowed_inputs(spec_text: str, r_value: str) -> list[str]:
    # F-050: ANCHOR_SPEC's "Allowed inputs" bullets become fnmatch-style glob patterns; <name>
    # (a campaign directory name) becomes a wildcard and a leading "R/" is expanded to the spec's
    # own R mapping.
    m = ALLOWED_INPUTS_BLOCK_RE.search(spec_text)
    if not m:
        return []
    patterns: list[str] = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        for frag in FRAGMENT_RE.findall(line):
            frag = frag.replace("<name>", "*")
            if frag.startswith("R/"):
                frag = r_value + frag[1:]
            patterns.append(frag)
    return patterns


def anchor_source_path_ok(path_rel: str | None, allowed_patterns: list[str]) -> bool:
    # F-050: an anchors sources[].path must match one of ANCHOR_SPEC's allowed-input patterns; an
    # absolute path or one with a ".." segment is rejected outright, regardless of the patterns.
    if not path_rel:
        return False
    norm = path_rel.replace("\\", "/")
    if norm.startswith("/") or (len(norm) > 1 and norm[1] == ":"):
        return False
    if ".." in norm.split("/"):
        return False
    return any(fnmatch.fnmatchcase(norm, pat) for pat in allowed_patterns)


def flatten_sources(sources) -> list[dict]:
    # F-050: "A sources entry may be an object or a list of objects, and both builders use both
    # shapes. Flatten one level before checking."
    if sources is None:
        return []
    if isinstance(sources, dict):
        return [sources]
    out: list[dict] = []
    if isinstance(sources, list):
        for s in sources:
            if isinstance(s, dict):
                out.append(s)
            elif isinstance(s, list):
                out.extend(x for x in s if isinstance(x, dict))
    return out


def section_body(spec_text: str, letter: str) -> str | None:
    heads = list(SECTION_HEAD_RE.finditer(spec_text))
    for i, m in enumerate(heads):
        if m.group(1) == letter:
            end = heads[i + 1].start() if i + 1 < len(heads) else len(spec_text)
            return spec_text[m.end():end]
    return None


def split_table_row(line: str) -> list[str]:
    # F-055 (spec cells): an escaped "\|" inside a cell is a literal pipe, not a cell delimiter.
    # Protect it before splitting on "|", then restore it in each cell's text.
    placeholder = "\x00ESCAPED-PIPE\x00"
    protected = line.replace("\\|", placeholder)
    return [c.strip().replace(placeholder, "\\|") for c in protected.strip("|").split("|")]


def table_rows(body: str) -> list[list[str]]:
    rows = []
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = split_table_row(line)
        if not cells:
            continue
        if set(cells[0]) <= {"-", ":"}:
            continue  # separator row
        if cells[0].lower() in ("key", "key pattern", "anchor key"):
            continue  # header row
        rows.append(cells)
    return rows


def find_for_clause_split(key_cell: str) -> int | None:
    # F-045: a for-clause's values may themselves be backticked (`for `NOM`, `TIGHT``); the split
    # between the key-pattern part and the for-clause must happen on backtick-depth parity (an
    # even number of backticks before the match means we are outside any backtick span), before
    # any backtick scanning of the whole cell runs -- otherwise those values leak into the key
    # patterns (F-045) and vanish from the restriction (F-046).
    for m in FOR_WORD_RE.finditer(key_cell):
        if key_cell[:m.start()].count("`") % 2 == 0:
            return m.start()
    return None


def extract_key_patterns(key_cell: str) -> list[str]:
    """A row's key cell may hold one pattern, or several comma-separated backtick fragments,
    followed optionally by a for-clause. A fragment after the first that starts with '.' extends
    the prefix of the first fragment (the text before its last '.' segment); any other later
    fragment is an independent full key. F-045: only the part of the cell before the for-clause is
    scanned for key patterns; backticked for-clause values are never treated as keys."""
    split = find_for_clause_split(key_cell)
    head = key_cell[:split] if split is not None else key_cell
    frags = FRAGMENT_RE.findall(head)
    if not frags:
        return []
    patterns = [frags[0]]
    prefix = frags[0].rsplit(".", 1)[0]
    for frag in frags[1:]:
        patterns.append(prefix + frag if frag.startswith(".") else frag)
    return patterns


def local_restriction(key_cell: str) -> tuple[str | None, list[str]]:
    """Look for a trailing 'for <TOKEN> in a, b, c' or bare 'for a, b, c' clause (the latter always
    restricts <ARM>, the only placeholder the real spec restricts this way). F-045: values may be
    plain or backticked; backticks are stripped from each value, never treated as key fragments."""
    split = find_for_clause_split(key_cell)
    if split is None:
        return None, []
    tail = key_cell[split:]
    m = re.match(r"for\s+([A-Z][A-Z_]*)\s+in\s+(.+)$", tail)
    if m:
        values = [v.strip(" `") for v in m.group(2).split(",") if v.strip(" `")]
        return m.group(1), values
    m = re.match(r"for\s+(.+)$", tail)
    if m:
        # F-046: a bare "for ..." clause that resolves to zero usable values (e.g. "for ,") is an
        # explicit, empty ARM restriction -- not "no restriction found" (which would wrongly fall
        # back to the global arm list and mask the broken row).
        values = [v.strip(" `") for v in m.group(1).split(",") if v.strip(" `")]
        return "ARM", values
    return None, []


def expand_pattern(
    pattern: str, restriction: tuple[str | None, list[str]], arms: list[str], seeds: list[str]
) -> tuple[list[str], str | None]:
    # F-046: a placeholder with no domain (H/DELTA with no local restriction), or a restriction
    # token absent from the pattern's own placeholders, is now a reported error instead of a
    # silent empty expansion.
    tokens = sorted(set(PLACEHOLDER_RE.findall(pattern)))
    rtoken, rvalues = restriction
    # F-062: the restriction-token check now runs before the "no placeholders" early return below,
    # so a "for ..." clause attached to a pattern that carries no placeholders at all is reported
    # as a SPEC ERROR instead of being silently ignored (the early return used to fire first,
    # discarding rtoken/rvalues without ever comparing them against the pattern's tokens).
    if rtoken is not None and rtoken not in tokens:
        return [], f"restriction token <{rtoken}> is not one of the pattern's placeholders {tokens}"
    if not tokens:
        return [pattern], None
    domain: dict[str, list[str]] = {}
    for tok in tokens:
        if tok == rtoken:
            domain[tok] = rvalues
        elif tok == "ARM":
            domain[tok] = arms
        elif tok == "SEED":
            domain[tok] = seeds
        elif tok == "n":
            domain[tok] = N_VALUES
        else:
            return [], f"placeholder <{tok}> has no domain (no local restriction for H or DELTA)"
        if not domain[tok]:
            return [], f"placeholder <{tok}> resolves to an empty domain"
    results = [pattern]
    for tok in tokens:
        results = [r.replace(f"<{tok}>", v) for r in results for v in domain[tok]]
    return results, None


def required_keys_for_section(
    spec_text: str, letter: str, arms: list[str], seeds: list[str], spec_errors: list[str]
) -> dict[str, bool]:
    # F-046: a missing section, and any row that yields zero keys, is now a reported SPEC ERROR
    # instead of silently dropping out of the required set.
    body = section_body(spec_text, letter)
    if body is None:
        spec_errors.append(f"SPEC ERROR section {letter}: missing from the spec")
        return {}
    keys: dict[str, bool] = {}
    rows = table_rows(body)
    if not rows:
        spec_errors.append(f"SPEC ERROR section {letter}: no table rows parsed")
        return {}
    for cells in rows:
        key_cell = cells[0]
        definition = cells[2] if len(cells) > 2 else ""
        # F-049: optional also covers a definition that names UNAVAILABLE directly, matching the
        # rule already used for DOCUMENT_VALUES_SPEC keys.
        optional = "optional" in definition.lower() or "unavailable" in definition.lower()
        restriction = local_restriction(key_cell)
        patterns = extract_key_patterns(key_cell)
        if not patterns:
            spec_errors.append(f"SPEC ERROR section {letter} row has no key pattern: {key_cell!r}")
            continue
        row_key_count = 0
        row_had_error = False
        for pat in patterns:
            expanded, err = expand_pattern(pat, restriction, arms, seeds)
            if err:
                spec_errors.append(f"SPEC ERROR section {letter} row {key_cell!r}: {err}")
                row_had_error = True
                continue
            for k in expanded:
                keys[k] = keys.get(k, False) or optional
                row_key_count += 1
        if row_key_count == 0 and not row_had_error:
            spec_errors.append(f"SPEC ERROR section {letter} row yields no keys: {key_cell!r}")
    return keys


def parse_section_e(spec_text: str, arms: list[str], spec_errors: list[str]) -> dict[str, str]:
    # F-046: a Section E row that does not parse is now a reported SPEC ERROR.
    body = section_body(spec_text, "E")
    if body is None:
        spec_errors.append("SPEC ERROR section E: missing from the spec")
        return {}
    out: dict[str, str] = {}
    for cells in table_rows(body):
        if len(cells) < 2:
            spec_errors.append(f"SPEC ERROR section E row does not parse: {cells!r}")
            continue
        key_parts = [p.strip() for p in cells[0].split("/")]
        val_parts = [p.strip() for p in cells[1].split("/")]
        if len(key_parts) != len(val_parts):
            spec_errors.append(
                f"SPEC ERROR section E row does not parse (key/value count mismatch): {cells[0]!r} / {cells[1]!r}"
            )
            continue
        first_frags = FRAGMENT_RE.findall(key_parts[0])
        if not first_frags:
            spec_errors.append(f"SPEC ERROR section E row does not parse (no key pattern): {cells[0]!r}")
            continue
        base_key = first_frags[0]
        out[base_key] = val_parts[0]
        if len(key_parts) > 1:
            prefix = base_key.rsplit(".", 1)[0]
            segs = base_key.split(".")
            arm_idx = next((i for i, s in enumerate(segs) if s in arms), None)
            for kp, vp in zip(key_parts[1:], val_parts[1:]):
                frag = kp.strip(" `")
                if frag.startswith("."):
                    out[prefix + frag] = vp
                elif arm_idx is not None:
                    new_segs = list(segs)
                    new_segs[arm_idx] = frag
                    out[".".join(new_segs)] = vp
                else:
                    spec_errors.append(
                        f"SPEC ERROR section E row does not parse (no arm segment to substitute): {cells[0]!r}"
                    )
    return out


def whole_key_present(key: str, text: str) -> bool:
    # F-048: the anchor key must appear as a whole key, not as a prefix of a longer dotted key
    # (e.g. a card naming "drift.holdout.hist_tv_max.like_for_like" must not waive
    # "drift.holdout.hist_tv_max").
    pattern = r"(?<![\w.])" + re.escape(key) + r"(?![\w.])"
    return re.search(pattern, text) is not None


def section_e_waived(root: Path, key: str) -> bool:
    q_dir = root / W_REL / "governance" / "questions"
    found = False
    if q_dir.is_dir():
        for f in sorted(q_dir.glob("Q-*.md")):
            text = f.read_text(encoding="utf-8", errors="replace")
            # F-048: "Resolution:" must carry non-empty text on the SAME line -- [ \t]*, not \s*,
            # so an empty "Resolution:" line followed later by other text no longer counts as
            # closed.
            if whole_key_present(key, text) and re.search(r"^Resolution:[ \t]*\S.*$", text, re.MULTILINE):
                found = True
                break
    if not found:
        return False
    errata_path = root / W_REL / "evidence" / "interpretation_errata.md"
    if not errata_path.is_file():
        return False
    return whole_key_present(key, errata_path.read_text(encoding="utf-8", errors="replace"))


# ---------------------------------------------------------------------------
# Value agreement (anchors mode)
# ---------------------------------------------------------------------------

def compare_value(a_entry: dict, b_entry: dict) -> bool:
    a_exact, b_exact = a_entry.get("value_exact"), b_entry.get("value_exact")
    fa = try_parse_fraction(str(a_exact)) if a_exact is not None else None
    fb = try_parse_fraction(str(b_exact)) if b_exact is not None else None
    if fa is not None and fb is not None:
        return fa == fb
    try:
        ja, jb = json.loads(a_exact), json.loads(b_exact)
        if isinstance(ja, (list, dict)) and isinstance(jb, (list, dict)):
            return json.dumps(ja, sort_keys=True) == json.dumps(jb, sort_keys=True)
    except (json.JSONDecodeError, TypeError):
        pass
    fa_f, fb_f = a_entry.get("value_float"), b_entry.get("value_float")
    if not isinstance(fa_f, (int, float)) or not isinstance(fb_f, (int, float)):
        return False
    if fa_f == 0 or fb_f == 0:
        return abs(fa_f - fb_f) <= 1e-15
    return abs(fa_f - fb_f) <= 1e-12 * max(abs(fa_f), abs(fb_f))


def numeric_value_of_exact(value_exact) -> float | None:
    if value_exact is None or value_exact == "UNAVAILABLE":
        return None
    s = str(value_exact)
    fr = try_parse_fraction(s)
    if fr is not None:
        return float(fr)
    try:
        return float(s)
    except ValueError:
        return None


def value_float_ok(entry: dict) -> bool:
    # F-051: wherever value_exact parses as an integer, a rational p/q or a decimal, value_float
    # must agree with it within a relative 1e-12 (absolute 1e-15 near zero).
    numeric = numeric_value_of_exact(entry.get("value_exact"))
    if numeric is None:
        return True
    vf = entry.get("value_float")
    if not isinstance(vf, (int, float)):
        return False
    if numeric == 0 or vf == 0:
        return abs(vf - numeric) <= 1e-15
    return abs(vf - numeric) <= 1e-12 * max(abs(vf), abs(numeric))


# ---------------------------------------------------------------------------
# Default (anchors) mode
# ---------------------------------------------------------------------------

def cmd_anchors(root: Path) -> int:
    evidence_dir = root / W_REL / "evidence"
    spec_path = evidence_dir / "ANCHOR_SPEC.md"
    a_path = evidence_dir / "anchors.json"
    b_path = evidence_dir / "independent" / "anchors_B.json"

    if not spec_path.is_file():
        print(f"MISMATCH <spec>: {spec_path} not found")
        print("ANCHORS CROSS-CHECK FAILED (1)")
        return 1
    spec_text = spec_path.read_text(encoding="utf-8")
    arms, seeds = parse_conventions(spec_text)
    r_value = parse_r_mapping(spec_text)
    allowed_inputs = parse_anchor_allowed_inputs(spec_text, r_value)

    # F-046: spec-structural problems (missing section, zero-key row, unresolved placeholder, a
    # restriction token absent from its pattern, an unparseable Section E row) are collected first
    # and, if any exist, fail the check immediately -- before anchors.json/anchors_B.json are even
    # compared -- since the required-key set itself would otherwise be untrustworthy.
    spec_errors: list[str] = []
    required: dict[str, bool] = {}
    for letter in "ABCD":
        required.update(required_keys_for_section(spec_text, letter, arms, seeds, spec_errors))
    section_e = parse_section_e(spec_text, arms, spec_errors)
    if spec_errors:
        for e in spec_errors:
            print(e)
        print(f"ANCHORS CROSS-CHECK FAILED ({len(spec_errors)})")
        return 1
    if not required:
        print(f"MISMATCH <spec>: no required keys parsed from {spec_path.name}")
        print("ANCHORS CROSS-CHECK FAILED (1)")
        return 1

    a_raw, b_raw = load_json(a_path), load_json(b_path)
    problems: list[str] = []
    if a_raw is None:
        problems.append(f"MISMATCH <file>: {a_path} not found or not valid JSON")
    if b_raw is None:
        problems.append(f"MISMATCH <file>: {b_path} not found or not valid JSON")
    a = a_raw if isinstance(a_raw, dict) else {}
    b = b_raw if isinstance(b_raw, dict) else {}

    for key, optional in sorted(required.items()):
        a_has, b_has = key in a, key in b
        if not a_has or not b_has:
            missing = [lbl for lbl, has in (("A", a_has), ("B", b_has)) if not has]
            problems.append(f"MISMATCH {key}: missing from {', '.join(missing)}")
            continue
        a_entry, b_entry = a[key], b[key]
        a_unavail = a_entry.get("value_exact") == "UNAVAILABLE"
        b_unavail = b_entry.get("value_exact") == "UNAVAILABLE"
        if a_unavail or b_unavail:
            # F-049: UNAVAILABLE is allowed only for keys the spec marks optional.
            if not optional:
                problems.append(f"MISMATCH {key}: UNAVAILABLE but the spec does not mark this key optional")
            elif a_unavail != b_unavail:
                problems.append(f"MISMATCH {key}: one file says UNAVAILABLE and the other does not")
            continue
        if not compare_value(a_entry, b_entry):
            problems.append(
                f"MISMATCH {key}: value disagrees (A value_exact={a_entry.get('value_exact')!r}, "
                f"B value_exact={b_entry.get('value_exact')!r})"
            )
        # F-051: value_float must agree with value_exact in both files.
        if not value_float_ok(a_entry) or not value_float_ok(b_entry):
            problems.append(f"MISMATCH {key}: value_float disagrees with value_exact")
        # F-050/F-061: sources[].path must match one of ANCHOR_SPEC's allowed inputs, and (F-061,
        # the F-050 remainder) a non-UNAVAILABLE entry must carry a non-empty flattened sources
        # list, each source needing path, sha256 and selector -- previously an absent or empty
        # sources field produced zero loop iterations below and therefore no problem at all.
        for label, entry in (("A", a_entry), ("B", b_entry)):
            flat_sources = flatten_sources(entry.get("sources"))
            if not flat_sources:
                problems.append(f"MISMATCH {key} ({label}): no sources")
                continue
            for src in flat_sources:
                path = src.get("path")
                if not anchor_source_path_ok(path, allowed_inputs):
                    problems.append(f"MISMATCH {key} ({label}): source path not allowed by ANCHOR_SPEC ({path!r})")
                if not path or not src.get("sha256") or not src.get("selector"):
                    problems.append(f"MISMATCH {key} ({label}): source missing path, sha256 or selector")

    # F-055 (unknown keys): a key in either file that the spec does not require, and that lacks
    # the extra. prefix, is a problem.
    for label, data in (("A", a), ("B", b)):
        for key in data.keys():
            if key not in required and not key.startswith("extra."):
                problems.append(f"MISMATCH {key} ({label}): key is not required by ANCHOR_SPEC and lacks the extra. prefix")

    # Section E cross-check (item 3): keys named there are always a subset of A-D, checked
    # directly against A regardless of set membership in `required`.
    for key, displayed in sorted(section_e.items()):
        if key not in a:
            problems.append(f"MISMATCH {key}: section E displayed value has no matching key in A")
            continue
        a_entry = a[key]
        if a_entry.get("value_exact") == "UNAVAILABLE":
            continue
        decimals = len(displayed.split(".", 1)[1]) if "." in displayed else 0
        a_float = a_entry.get("value_float")
        if not isinstance(a_float, (int, float)):
            fa = try_parse_fraction(str(a_entry.get("value_exact")))
            a_float = float(fa) if fa is not None else None
        if a_float is None:
            problems.append(f"MISMATCH {key}: section E cannot compute a numeric value for A")
            continue
        formatted = f"{a_float:.{decimals}f}"
        if formatted != displayed:
            if section_e_waived(root, key):
                continue
            problems.append(f"MISMATCH {key}: displayed {displayed!r} but A rounds to {formatted!r}")

    for p in problems:
        print(p)
    if problems:
        print(f"ANCHORS CROSS-CHECK FAILED ({len(problems)})")
        return 1
    print(f"ANCHORS CROSS-CHECK PASSED ({len(required)} keys)")
    return 0


# ---------------------------------------------------------------------------
# --documents mode
# ---------------------------------------------------------------------------

def parse_document_value_keys(spec_text: str, spec_errors: list[str]) -> dict[str, bool]:
    # F-060 (F-046 remainder): a row whose key cell yields no backtick key, or whose key pattern
    # carries a placeholder (DOCUMENT_VALUES_SPEC keys carry none), is now a reported SPEC ERROR
    # instead of a silent drop -- mirroring sections A-D's treatment of the same problems.
    m = re.search(r"^## Keys\s*$", spec_text, re.MULTILINE)
    if not m:
        spec_errors.append("SPEC ERROR Keys: section missing from the spec")
        return {}
    body = spec_text[m.end():]
    m2 = re.search(r"^## ", body, re.MULTILINE)
    if m2:
        body = body[:m2.start()]
    keys: dict[str, bool] = {}
    rows = table_rows(body)
    if not rows:
        spec_errors.append("SPEC ERROR Keys: no table rows parsed")
        return {}
    for cells in rows:
        key_cell = cells[0]
        definition = cells[2] if len(cells) > 2 else ""
        optional = "unavailable" in definition.lower() or "optional" in definition.lower()
        patterns = extract_key_patterns(key_cell)
        if not patterns:
            spec_errors.append(f"SPEC ERROR Keys row has no key pattern: {key_cell!r}")
            continue
        for pat in patterns:
            if PLACEHOLDER_RE.search(pat):
                spec_errors.append(f"SPEC ERROR Keys row key pattern carries a placeholder: {pat!r}")
                continue
            keys[pat] = keys.get(pat, False) or optional
    return keys


DOCUMENT_ALLOWED_SOURCES_RE = re.compile(r"\*\*Allowed sources:\*\*\s*\n(.*?)(?:\n\s*\n|\Z)", re.DOTALL)


def parse_document_allowed_sources(spec_text: str) -> list[str]:
    # F-050: a bullet may list several comma-separated backtick filenames where only the first
    # carries a directory prefix (matching the spec's own ".suffix continuation" convention for
    # key-pattern cells); a later bare filename in the same bullet inherits that prefix.
    m = DOCUMENT_ALLOWED_SOURCES_RE.search(spec_text)
    if not m:
        return []
    allowed: list[str] = []
    for line in m.group(1).splitlines():
        line = line.strip()
        if not line.startswith("-"):
            continue
        prefix = ""
        for frag in FRAGMENT_RE.findall(line):
            if "/" in frag:
                prefix = frag.rsplit("/", 1)[0]
                allowed.append(frag)
            elif prefix:
                allowed.append(f"{prefix}/{frag}")
            else:
                allowed.append(frag)
    return allowed


BANNED_SOURCE_RE = re.compile(r"(^|/)(IJPR_CSLAP_[^/]*|C&OR_CSLAP\.tex)$")


def document_source_path_ok(path_rel: str | None, allowed: list[str]) -> bool:
    # F-050: a document source.path must be one of DOCUMENT_VALUES_SPEC's allowed sources, given
    # as a relative path. An absolute path, a ".." segment, or any IJPR_CSLAP_*/C&OR_CSLAP.tex file
    # (banned by U5) is a problem regardless of what the allowlist contains.
    if not path_rel:
        return False
    norm = path_rel.replace("\\", "/")
    if norm.startswith("/") or (len(norm) > 1 and norm[1] == ":"):
        return False
    if ".." in norm.split("/"):
        return False
    if BANNED_SOURCE_RE.search(norm):
        return False
    return norm in allowed


def normalize_document_value(raw) -> tuple[str, float | None]:
    # Q-015: in LaTeX sources a "~" (non-breaking space) counts as whitespace.
    text = str(raw).replace("~", " ")
    s = " ".join(text.strip().split())
    numeric = s.replace("{,}", "").replace("\\,", "").replace(",", "").replace("%", "").strip()
    try:
        return s, float(numeric)
    except ValueError:
        return s, None


def document_value_agrees(a_entry: dict, b_entry: dict) -> bool:
    a_ws, a_num = normalize_document_value(a_entry.get("value_exact"))
    b_ws, b_num = normalize_document_value(b_entry.get("value_exact"))
    if a_num is not None and b_num is not None:
        return a_num == b_num
    return a_ws == b_ws


def merged_value_matches(merged_exact, agreement_entry: dict) -> bool:
    m_ws, m_num = normalize_document_value(merged_exact)
    a_ws, a_num = normalize_document_value(agreement_entry.get("value_exact"))
    if m_num is not None and a_num is not None:
        return m_num == a_num
    return m_ws == a_ws


VALID_STREAM_END_SEMANTICS = ("length", "last_index")


def semantics_consistent(a: dict, b: dict, merged: dict) -> list[str]:
    # F-047 (Q-013): prov.stream_end must carry `semantics` in A, B and the merged file, with the
    # same value in all three.
    se_a = (a.get("prov.stream_end") or {}).get("semantics")
    se_b = (b.get("prov.stream_end") or {}).get("semantics")
    se_m = (merged.get("prov.stream_end") or {}).get("semantics")
    if se_a not in VALID_STREAM_END_SEMANTICS or se_b not in VALID_STREAM_END_SEMANTICS or se_m not in VALID_STREAM_END_SEMANTICS:
        return [f"MISMATCH prov.stream_end: semantics missing or invalid (A={se_a!r}, B={se_b!r}, merged={se_m!r})"]
    if not (se_a == se_b == se_m):
        return [f"MISMATCH prov.stream_end: semantics differs across A ({se_a!r}), B ({se_b!r}) and merged ({se_m!r})"]
    return []


def check_tail_unused(merged: dict) -> bool:
    # F-047 (Q-013): only the formula that matches the merged prov.stream_end.semantics is valid;
    # the old code accepted either formula regardless of semantics.
    entry, se, ts = merged.get("prov.tail_unused"), merged.get("prov.stream_end"), merged.get("prov.tail_start")
    if not entry or not se or not ts:
        return False
    semantics = se.get("semantics")
    _, value = normalize_document_value(entry.get("value_exact"))
    _, stream_end = normalize_document_value(se.get("value_exact"))
    _, tail_start = normalize_document_value(ts.get("value_exact"))
    if value is None or stream_end is None or tail_start is None:
        return False
    if semantics == "length":
        return value == stream_end - tail_start
    if semantics == "last_index":
        return value == stream_end + 1 - tail_start
    return False


def cmd_documents(root: Path) -> int:
    evidence_dir = root / W_REL / "evidence"
    spec_path = evidence_dir / "DOCUMENT_VALUES_SPEC.md"
    a_path = evidence_dir / "independent" / "document_values_A.json"
    b_path = evidence_dir / "independent" / "document_values_B.json"
    merged_path = evidence_dir / "document_values.json"

    if not spec_path.is_file():
        print(f"MISMATCH <spec>: {spec_path} not found")
        print("DOCUMENT VALUES CROSS-CHECK FAILED (1)")
        return 1
    spec_text = spec_path.read_text(encoding="utf-8")
    # F-060 (F-046 remainder): spec-structural problems in the Keys table are collected and, if
    # any exist, fail the check immediately -- before document_values_A/B.json or the merged file
    # are even read -- mirroring cmd_anchors's spec_errors handling for sections A-D.
    spec_errors: list[str] = []
    required = parse_document_value_keys(spec_text, spec_errors)
    if spec_errors:
        for e in spec_errors:
            print(e)
        print(f"DOCUMENT VALUES CROSS-CHECK FAILED ({len(spec_errors)})")
        return 1
    if not required:
        print(f"MISMATCH <spec>: no required keys parsed from {spec_path.name}")
        print("DOCUMENT VALUES CROSS-CHECK FAILED (1)")
        return 1
    allowed_sources = parse_document_allowed_sources(spec_text)

    a_raw, b_raw, m_raw = load_json(a_path), load_json(b_path), load_json(merged_path)
    problems: list[str] = []
    if a_raw is None:
        problems.append(f"MISMATCH <file>: {a_path} not found or not valid JSON")
    if b_raw is None:
        problems.append(f"MISMATCH <file>: {b_path} not found or not valid JSON")
    if m_raw is None:
        problems.append(f"MISMATCH <file>: {merged_path} not found or not valid JSON")
    a = a_raw if isinstance(a_raw, dict) else {}
    b = b_raw if isinstance(b_raw, dict) else {}
    merged = m_raw if isinstance(m_raw, dict) else {}

    n_checked = 0
    for key, optional in sorted(required.items()):
        n_checked += 1
        missing = [lbl for lbl, d in (("A", a), ("B", b), ("merged", merged)) if key not in d]
        if missing:
            problems.append(f"MISMATCH {key}: missing from {', '.join(missing)}")
            continue
        a_entry, b_entry, m_entry = a[key], b[key], merged[key]

        # F-049: UNAVAILABLE is allowed only for keys the spec marks optional; this used to be
        # ignored entirely in --documents mode.
        a_unavail = a_entry.get("value_exact") == "UNAVAILABLE"
        b_unavail = b_entry.get("value_exact") == "UNAVAILABLE"
        m_unavail = m_entry.get("value_exact") == "UNAVAILABLE"
        if a_unavail or b_unavail or m_unavail:
            if not optional:
                problems.append(f"MISMATCH {key}: UNAVAILABLE but the spec does not mark this key optional")
            elif not (a_unavail and b_unavail and m_unavail):
                problems.append(f"MISMATCH {key}: UNAVAILABLE does not agree across A, B and merged")
            continue

        if not document_value_agrees(a_entry, b_entry):
            problems.append(
                f"MISMATCH {key}: value_exact disagrees between A ({a_entry.get('value_exact')!r}) "
                f"and B ({b_entry.get('value_exact')!r})"
            )
            continue
        if not merged_value_matches(m_entry.get("value_exact"), a_entry):
            problems.append(f"MISMATCH {key}: merged value_exact does not equal the agreed value")
        extracted_by = m_entry.get("extracted_by") or []
        # F-063: an identity with no family is discarded before families are counted, so it can no
        # longer stand in as a second, distinct "family" of None alongside one real family.
        families = {e.get("family") for e in extracted_by if isinstance(e, dict) and e.get("family")}
        if len(extracted_by) < 2 or len(families) < 2:
            problems.append(f"MISMATCH {key}: merged extracted_by does not hold two identities of different families")

    # prov.tail_unused: derived, merged-only (never extracted in A or B).
    if "prov.tail_unused" not in merged:
        problems.append("MISMATCH prov.tail_unused: missing from merged")
    else:
        n_checked += 1
        if "prov.tail_unused" in a or "prov.tail_unused" in b:
            problems.append("MISMATCH prov.tail_unused: derived key must not be extracted in A or B")
        # F-047 (Q-013): the semantics field must agree across A, B and merged before the formula
        # itself is checked.
        problems.extend(semantics_consistent(a, b, merged))
        if not check_tail_unused(merged):
            problems.append("MISMATCH prov.tail_unused: does not equal its recorded computation")

    # Source checks (item 3): every file, every key that is not UNAVAILABLE-and-optional.
    # F-050: source.path is checked against DOCUMENT_VALUES_SPEC's allowed sources BEFORE any
    # filesystem access, so a disallowed path (an IJPR_CSLAP_* file, an absolute path, a ".."
    # segment) is reported and never opened, hashed or read.
    for label, data in (("A", a), ("B", b), ("merged", merged)):
        for key in sorted(required):
            entry = data.get(key)
            if entry is None:
                continue
            optional = required.get(key, False)
            if entry.get("value_exact") == "UNAVAILABLE":
                if optional:
                    continue
                continue  # not optional: already reported above; no real source to check
            src = entry.get("source") or {}
            src_path_rel = src.get("path")
            if not document_source_path_ok(src_path_rel, allowed_sources):
                problems.append(f"MISMATCH {key} ({label}): source.path is not an allowed source ({src_path_rel!r})")
                continue
            src_path = root / src_path_rel
            if not src_path.is_file():
                problems.append(f"MISMATCH {key} ({label}): source.path does not exist ({src_path_rel!r})")
                continue
            if sha256_file(src_path) != src.get("sha256"):
                problems.append(f"MISMATCH {key} ({label}): source.sha256 does not match the file's current bytes")
            lines = src_path.read_text(encoding="utf-8", errors="replace").splitlines()
            lineno = src.get("line")
            quoted = src.get("quoted_text")
            ok_line = isinstance(lineno, int) and 1 <= lineno <= len(lines)
            if not ok_line or not quoted or quoted not in lines[lineno - 1]:
                problems.append(f"MISMATCH {key} ({label}): source.quoted_text is not a substring of line {lineno} of {src_path_rel}")

    for p in problems:
        print(p)
    if problems:
        print(f"DOCUMENT VALUES CROSS-CHECK FAILED ({len(problems)})")
        return 1
    print(f"DOCUMENT VALUES CROSS-CHECK PASSED ({n_checked} keys)")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None)
    parser.add_argument("--documents", action="store_true")
    args = parser.parse_args(argv)

    root = resolve_root(args.root)
    if not root_confirmed(root):
        marker = root / ROOT_MARKER_REL
        print(f"MISMATCH <root>: {marker} not found (wrong --root?)")
        if args.documents:
            print("DOCUMENT VALUES CROSS-CHECK FAILED (1)")
        else:
            print("ANCHORS CROSS-CHECK FAILED (1)")
        return 1

    if args.documents:
        return cmd_documents(root)
    return cmd_anchors(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
