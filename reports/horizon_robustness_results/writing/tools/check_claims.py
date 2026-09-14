"""Trace, validate and cover the claim register (P1 step 5; plan Appendix D).

Modes
-----
``check_claims.py [--root DIR]``              Default: numeric trace of every claim's statement,
                                                allowed_wording and required_qualifiers text against
                                                anchors.json / document_values.json.
``check_claims.py --schema [--root DIR]``      jsonschema validation of claims.json,
                                                requirements_map.json, document_values.json and
                                                anchors.json against plan Appendix D.
``check_claims.py --coverage [--root DIR]``    Every requirements_map.json row resolves to a claim
                                                or a forbidden-wording entry, and P1 step 4's three
                                                source files are represented.
``check_claims.py --argument [--root DIR]``    (P4) Validates the argument-option file named by the
                                                Q-ARGUMENT decision record.

Root argument
-------------
``--root`` defaults to the repository root, computed as ``Path(__file__).resolve().parents[4]``
from this script's location under ``W/tools/``. Whichever root is used -- default or explicit --
is confirmed by checking that ``<root>/reports/horizon_robustness_results/
WRITING_ORCHESTRATION_PLAN_20260914.md`` exists, a plain file-existence check that never invokes
git (user decision U8).

This script performs no writes and starts no subprocess.

Fix round 1 (P1 seq 31), findings fixed here: F-052, F-053, F-054, F-055 (units, year exemption,
extra. keys); Q-016 option (a). Each change below carries a short comment naming the finding.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

import jsonschema

W_REL = "reports/horizon_robustness_results/writing"
ROOT_MARKER_REL = "reports/horizon_robustness_results/WRITING_ORCHESTRATION_PLAN_20260914.md"

# F-053/Q-016(a): tokens are found by a plain digit-run scan (no lookbehind); sign, slash and
# prefix exemptions are then applied per-match with full context, since a lookbehind-based regex
# cannot tell a range separator from a minus sign or a letter-prefixed code from a bare number.
RAW_NUM_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
MINUS_CHARS = "-−"  # hyphen-minus and the Unicode minus sign both count as minus (Q-016a).
PHRASE_PREFIXES = ("n = ", "line ", "lines ")
SINGLE_LETTER_PREFIXES = ("§", "Q-", "C-", "F", "H", "D", "U", "P", "S")
YEAR_RE = re.compile(r"^\d{4}$")
# F-055 (year remainder): a citation list inside parentheses that ends in the year -- "(Smith,
# YEAR)", "(Smith et al., YEAR)" or "(Smith and Jones, YEAR)". Matched against the text immediately
# before the year, anchored at the end of that slice.
CITATION_PAREN_RE = re.compile(
    r"\([A-Z][A-Za-z.]*(?:\s+et\s+al\.|\s+and\s+[A-Z][A-Za-z.]*)?,\s*$"
)


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
    return (root / ROOT_MARKER_REL).is_file()


def load_json(path: Path):
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def load_claims(root: Path) -> list[dict] | None:
    data = load_json(root / W_REL / "evidence" / "claims.json")
    if data is None:
        return None
    if isinstance(data, dict) and "claims" in data:
        data = data["claims"]
    if not isinstance(data, list):
        return None
    return data


def load_drs(root: Path) -> list[dict]:
    decisions_dir = root / W_REL / "governance" / "decisions"
    drs = []
    if not decisions_dir.is_dir():
        return drs
    for f in sorted(decisions_dir.glob("DR-*.md")):
        text = f.read_text(encoding="utf-8")
        m = re.match(r"\s*```json\s*\n(.*?)\n```", text, re.DOTALL)
        data = None
        if m:
            try:
                data = json.loads(m.group(1))
            except json.JSONDecodeError:
                data = None
        drs.append({"_file": f.name, "_data": data})
    return drs


# ---------------------------------------------------------------------------
# Default mode: numeric trace
# ---------------------------------------------------------------------------

def _word_boundary_before(text: str, pos: int) -> bool:
    if pos <= 0:
        return True
    ch = text[pos - 1]
    return not (ch.isalnum() or ch == "_")


def _prefix_exempt(text: str, start: int) -> bool:
    # F-053/Q-016(a): the phrase prefixes and the single-letter prefixes exempt a number only when
    # a word boundary comes before the prefix itself. The old code checked only
    # ``preceding.endswith(prefix)`` with no boundary requirement, so "mean = 3.231630" (via
    # "n = "... no: via no boundary before "line " inside "baseline ") and "baseline 3.85" were
    # wrongly exempt.
    before = text[:start]
    for phrase in PHRASE_PREFIXES:
        if before.endswith(phrase) and _word_boundary_before(text, start - len(phrase)):
            return True
    for prefix in SINGLE_LETTER_PREFIXES:
        if before.endswith(prefix) and _word_boundary_before(text, start - len(prefix)):
            return True
    return False


def is_exempt_small_int(signed_text: str, claim_has_count_or_bool: bool) -> bool:
    # Q-016(a): integers from 0 to 10 are exempt only when the claim cites no anchor or document
    # value whose unit is count or bool.
    if claim_has_count_or_bool:
        return False
    no_sep = signed_text.replace(",", "")
    if "." in no_sep:
        return False
    try:
        return 0 <= int(no_sep) <= 10
    except ValueError:
        return False


def is_exempt_year(token: str, text: str, start: int) -> bool:
    # F-055 (year remainder): a year is exempt only when (1) the whole parenthesised content is the
    # year -- "(YEAR)", including the narrative "Name (YEAR)"/"Name et al. (YEAR)" form, whose
    # parentheses likewise hold nothing but the year -- or (2) it closes a citation list inside
    # parentheses ("(Smith, YEAR)", "(Smith et al., YEAR)", "(Smith and Jones, YEAR)"). Both forms
    # require the year to be immediately followed by ")"; "(2000 rows)" and "in 2000 blocks" match
    # neither (the first has trailing text before the closing paren, the second has no parens at
    # all) and must count as numbers, unlike the old open-paren/close-within-40-chars heuristic.
    if not YEAR_RE.match(token):
        return False
    year = int(token)
    if not (1900 <= year <= 2099):
        return False
    end = start + len(token)
    if text[end:end + 1] != ")":
        return False
    before = text[:start]
    if before[-1:] == "(":
        return True
    return bool(CITATION_PAREN_RE.search(before[-60:]))


def find_numeric_tokens(text: str, claim_has_count_or_bool: bool) -> list[tuple[str, str, int]]:
    """Scan text for numeric tokens that must trace. Returns (raw_token, signed_text, start) for
    each: raw_token is exactly as it appears (used in UNTRACED messages), signed_text additionally
    carries a leading "-" when the preceding character is a genuine minus sign rather than a range
    separator or a letter-prefixed code (Q-016a)."""
    out: list[tuple[str, str, int]] = []
    for m in RAW_NUM_RE.finditer(text):
        start, end = m.start(), m.end()
        raw = m.group(0)
        signed_text = raw
        exempt = False

        # F-053/Q-016(a): hyphen handling. A letter immediately before the hyphen exempts the
        # number (Q-008, C-3). A digit before the hyphen makes it a range separator (the number is
        # unsigned but still counts). Anything else (space, start of text, other punctuation) makes
        # it a minus sign: the number is negative and still counts.
        if start > 0 and text[start - 1] in MINUS_CHARS:
            hyphen_pos = start - 1
            before_hyphen = text[hyphen_pos - 1] if hyphen_pos > 0 else ""
            if before_hyphen.isalpha():
                exempt = True
            elif before_hyphen.isdigit():
                pass
            else:
                signed_text = "-" + raw

        # F-053/Q-016(a): slash handling. A letter immediately before the slash exempts the number
        # (as in "n/a"); a digit before the slash means digits/digits, and both integers count.
        if not exempt and start > 0 and text[start - 1] == "/":
            slash_pos = start - 1
            before_slash = text[slash_pos - 1] if slash_pos > 0 else ""
            if before_slash.isalpha():
                exempt = True

        if exempt:
            continue
        if _prefix_exempt(text, start):
            continue
        if is_exempt_small_int(signed_text, claim_has_count_or_bool):
            continue
        if is_exempt_year(raw, text, start):
            continue
        out.append((raw, signed_text, start))
    return out


RANGE_UPPER_UNIT_RE = re.compile(
    r"^[-–−]\d[\d,]*(?:\.\d+)?(?P<unit>\s*\\%|\s*%|\s*pp\b)"
)


def token_unit_hint(text: str, end: int) -> str | None:
    # F-055 (units): a token followed by "%"/"\%" traces only to unit pct; followed by "pp" traces
    # only to unit pp.
    rest = text[end:]
    if re.match(r"\s*\\%", rest) or re.match(r"\s*%", rest):
        return "pct"
    if re.match(r"\s*pp\b", rest):
        return "pp"
    # F-065: in a range "a-b unit" or "a–b unit" the unit written after the upper end restricts
    # BOTH ends -- so the lower end (here, `rest` starts with the range's dash and the upper number)
    # inherits the same unit hint instead of being left unrestricted.
    m = RANGE_UPPER_UNIT_RE.match(rest)
    if m:
        unit_str = m.group("unit")
        if "%" in unit_str:
            return "pct"
        if "pp" in unit_str:
            return "pp"
    return None


def token_value_and_decimals(signed_text: str) -> tuple[float, int]:
    no_sep = signed_text.replace(",", "")
    decimals = len(no_sep.split(".", 1)[1]) if "." in no_sep else 0
    return float(no_sep), decimals


def normalize_document_number(raw) -> Decimal | None:
    # F-052: normalise the same way compare_anchors.py's normalize_document_value does (strip
    # thousands separators, "{,}", "\," and "%"), then parse as a Decimal so a plain int() no
    # longer fails on "284,862" and a decimal document value can trace at all.
    if raw is None:
        return None
    text = str(raw).replace("~", " ")
    s = " ".join(text.strip().split())
    numeric = s.replace("{,}", "").replace("\\,", "").replace(",", "").replace("%", "").strip()
    try:
        return Decimal(numeric)
    except InvalidOperation:
        return None


def quantize_half_up(value: Decimal, decimals: int) -> Decimal | None:
    # F-064: rounding for the trace uses ROUND_HALF_UP (Python's own round()/Decimal's default
    # context both round half-even, so 13.65 would round to 13.6 at one decimal, not 13.7).
    quant = Decimal("1e-{0}".format(decimals)) if decimals else Decimal("1")
    try:
        return value.quantize(quant, rounding=ROUND_HALF_UP)
    except InvalidOperation:
        return None


def value_matches_token(decimals: int, signed_text: str, entry: dict) -> bool:
    # F-064: both the entry value and the token are quantized half-up at the token's own shown
    # decimals, then compared exactly -- for a value_float entry, from Decimal(repr(value_float))
    # rather than from Python's round().
    dec_token = normalize_document_number(signed_text)
    if dec_token is None:
        return False
    token_q = quantize_half_up(dec_token, decimals)
    if token_q is None:
        return False

    vf = entry.get("value_float")
    if isinstance(vf, (int, float)):
        vf_q = quantize_half_up(Decimal(repr(vf)), decimals)
        if vf_q is not None and vf_q == token_q:
            return True

    ve = entry.get("value_exact")
    if ve is None or ve == "UNAVAILABLE":
        return False
    # F-052: document values carry no value_float; compare as a Decimal at the token's shown
    # decimals instead of the old int()-only fallback.
    dec_entry = normalize_document_number(ve)
    if dec_entry is None:
        return False
    entry_q = quantize_half_up(dec_entry, decimals)
    return entry_q is not None and entry_q == token_q


def source_ok(root: Path, src: dict, manifest_by_path: dict[str, str]) -> bool:
    path_rel = src.get("path")
    sha = src.get("sha256")
    if not path_rel:
        return False
    fp = root / path_rel
    if not fp.is_file():
        return False
    if sha256_file(fp) != sha:
        return False
    pinned = manifest_by_path.get(path_rel)
    if pinned is not None and pinned != sha:
        return False
    return True


def load_manifest_hashes(root: Path) -> dict[str, str]:
    manifest = load_json(root / W_REL / "governance" / "source_manifest.json") or {}
    out = {}
    for e in manifest.get("files", []) if isinstance(manifest, dict) else []:
        if isinstance(e, dict) and e.get("path"):
            out[e["path"]] = e.get("sha256")
    return out


def cmd_trace(root: Path) -> int:
    claims = load_claims(root)
    if claims is None:
        print("UNTRACED <file>: claims.json not found or not valid JSON")
        print("CLAIMS TRACE FAILED (1)")
        return 1
    if not claims:
        print("UNTRACED <file>: claims.json has no claims")
        print("CLAIMS TRACE FAILED (1)")
        return 1

    anchors = load_json(root / W_REL / "evidence" / "anchors.json") or {}
    doc_values = load_json(root / W_REL / "evidence" / "document_values.json") or {}
    manifest_by_path = load_manifest_hashes(root)

    problems: list[str] = []
    n_tokens = 0

    for claim in claims:
        cid = claim.get("id", "<no-id>")

        for src in claim.get("sources", []) or []:
            if not source_ok(root, src, manifest_by_path):
                problems.append(f"UNTRACED {cid}: source {src.get('path')!r} does not resolve or its hash does not match")

        for ak in claim.get("anchor_keys", []) or []:
            if ak not in anchors:
                problems.append(f"UNTRACED {cid}: anchor_keys {ak!r} not found in anchors.json")
        for dk in claim.get("document_value_keys", []) or []:
            if dk not in doc_values:
                problems.append(f"UNTRACED {cid}: document_value_keys {dk!r} not found in document_values.json")

        candidate_entries = []
        for ak in claim.get("anchor_keys", []) or []:
            # F-055 (extra. keys): an anchor_keys[] entry that starts with extra. was never
            # spec-checked, so it cannot trace a number even though it must still exist (above).
            if ak in anchors and not ak.startswith("extra."):
                candidate_entries.append(anchors[ak])
        for dk in claim.get("document_value_keys", []) or []:
            if dk in doc_values:
                candidate_entries.append(doc_values[dk])

        # Q-016(a): the 0-10 exemption is suppressed for the whole claim when it cites any count or
        # bool value, since those are exactly the small integers most likely to be wrong.
        claim_has_count_or_bool = any(e.get("unit") in ("count", "bool") for e in candidate_entries)

        texts = [claim.get("statement", "")]
        texts += list(claim.get("allowed_wording", []) or [])
        texts += [q.get("text", "") for q in (claim.get("required_qualifiers", []) or [])]

        for text in texts:
            text = text or ""
            for token, signed_text, start in find_numeric_tokens(text, claim_has_count_or_bool):
                n_tokens += 1
                end = start + len(token)
                unit_hint = token_unit_hint(text, end)
                pool = candidate_entries
                if unit_hint is not None:
                    pool = [e for e in candidate_entries if e.get("unit") == unit_hint]
                _, decimals = token_value_and_decimals(signed_text)
                if not any(value_matches_token(decimals, signed_text, e) for e in pool):
                    problems.append(f"UNTRACED {cid}: {token}")

    for p in problems:
        print(p)
    if problems:
        print(f"CLAIMS TRACE FAILED ({len(problems)})")
        return 1
    print(f"CLAIMS TRACE PASSED ({len(claims)} claims, {n_tokens} tokens)")
    return 0


# ---------------------------------------------------------------------------
# --schema mode
# ---------------------------------------------------------------------------

FORBIDDEN_WORDING_SCHEMA = {
    "oneOf": [
        {"type": "string", "minLength": 1},
        {
            "type": "object",
            "required": ["text", "conditional_on"],
            "properties": {
                "text": {"type": "string"},
                "conditional_on": {
                    "type": "object",
                    "required": ["q_card", "outcome"],
                    "properties": {"q_card": {"type": "string"}, "outcome": {"type": "string"}},
                },
            },
        },
    ]
}

CLAIM_SCHEMA = {
    "type": "object",
    "required": ["id", "type", "endpoint_status", "statement"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "type": {
            "enum": [
                "assumption", "definition", "derivation", "observation", "interpretation",
                "limitation", "recommendation", "context", "disclosure", "scope", "premise",
            ]
        },
        "endpoint_status": {
            "enum": [
                "predeclared_primary", "predeclared_secondary", "additional_descriptive",
                "exploratory", "not_applicable",
            ]
        },
        "statement": {"type": "string", "minLength": 1},
        "allowed_wording": {"type": "array", "items": {"type": "string"}},
        "required_qualifiers": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["text", "discharge"],
                "properties": {
                    "text": {"type": "string", "minLength": 1},
                    "discharge": {"enum": ["sentence", "scope_paragraph"]},
                },
            },
        },
        "forbidden_wording": {"type": "array", "items": FORBIDDEN_WORDING_SCHEMA},
    },
}

# F-054: file-level schemas now require at least one item/property, so an empty [] or {} file
# fails instead of passing vacuously. Per-entry schemas for claims and requirements_map keep the
# seq 25 rules unchanged.
CLAIMS_FILE_SCHEMA = {"type": "array", "minItems": 1, "items": CLAIM_SCHEMA}

REQUIREMENTS_ROW_SCHEMA = {
    "type": "object",
    "required": ["req_id", "source", "text", "maps_to"],
    "properties": {
        "req_id": {"type": "string", "minLength": 1},
        "source": {"type": "string"},
        "text": {"type": "string"},
        "maps_to": {"type": "string", "minLength": 1},
    },
}
REQUIREMENTS_FILE_SCHEMA = {"type": "array", "minItems": 1, "items": REQUIREMENTS_ROW_SCHEMA}

SOURCE_OBJ_SCHEMA = {
    "type": "object",
    "required": ["path", "sha256", "selector"],
    "properties": {
        "path": {"type": "string", "minLength": 1},
        "sha256": {"type": "string"},
        "selector": {"type": "string"},
    },
}
# F-050: an anchor entry's sources[] item may be a single object or a list of such objects
# (flattened one level by compare_anchors.py); the schema accepts both shapes per item.
SOURCES_ITEM_SCHEMA = {"oneOf": [SOURCE_OBJ_SCHEMA, {"type": "array", "items": SOURCE_OBJ_SCHEMA, "minItems": 1}]}

# F-054: every anchors entry now requires value_exact, value_float (number or null), unit,
# display_rounding (integer or null), a non-empty sources array and computation -- previously only
# value_exact was required, so a bare {"value_exact": "..."}  entry (or the whole file being "{}")
# passed.
ANCHOR_ENTRY_SCHEMA = {
    "type": "object",
    "required": ["value_exact", "value_float", "unit", "display_rounding", "sources", "computation"],
    "properties": {
        "value_exact": {"type": "string"},
        "value_float": {"type": ["number", "null"]},
        "unit": {"type": "string"},
        "display_rounding": {"type": ["integer", "null"]},
        "sources": {"type": "array", "minItems": 1, "items": SOURCES_ITEM_SCHEMA},
        "computation": {"type": "string"},
    },
}
ANCHORS_FILE_SCHEMA = {"type": "object", "minProperties": 1, "additionalProperties": ANCHOR_ENTRY_SCHEMA}

DOC_SOURCE_SCHEMA = {
    "type": "object",
    "required": ["path", "line", "sha256", "quoted_text"],
    "properties": {
        "path": {"type": "string", "minLength": 1},
        "line": {"type": "integer"},
        "sha256": {"type": "string"},
        "quoted_text": {"type": "string"},
    },
}

# F-054: every merged document_values.json entry now requires value_exact, unit, source and
# extracted_by (checked for two distinct families separately, below -- plain JSON Schema cannot
# express "at least two distinct values of a sub-property" using only minItems/uniqueItems, since
# uniqueItems compares whole items, not just their "family" field).
MERGED_DOC_VALUE_ENTRY_SCHEMA = {
    "type": "object",
    "required": ["value_exact", "unit", "source", "extracted_by"],
    "properties": {
        "value_exact": {"type": "string"},
        "unit": {"type": "string"},
        "source": DOC_SOURCE_SCHEMA,
        "extracted_by": {"type": "array", "minItems": 2},
    },
}
# F-054: the merged-only prov.tail_unused requires value_exact, unit and computation, and must
# carry no source (it is computed, not extracted).
TAIL_UNUSED_ENTRY_SCHEMA = {
    "type": "object",
    "required": ["value_exact", "unit", "computation"],
    "not": {"required": ["source"]},
    "properties": {
        "value_exact": {"type": "string"},
        "unit": {"type": "string"},
        "computation": {"type": "string"},
    },
}
DOCUMENT_VALUES_FILE_SCHEMA = {
    "type": "object",
    "minProperties": 1,
    "properties": {"prov.tail_unused": TAIL_UNUSED_ENTRY_SCHEMA},
    "additionalProperties": MERGED_DOC_VALUE_ENTRY_SCHEMA,
}

# F-061 (F-050 remainder): the per-extraction document-value schema for
# independent/document_values_A.json and document_values_B.json -- each entry carries value_exact,
# unit and source, like the merged file, but never extracted_by (that field is added only once the
# two extractions are merged) and never prov.tail_unused (derived, merged-only; never extracted).
DOCUMENT_VALUE_ENTRY_SCHEMA = {
    "type": "object",
    "required": ["value_exact", "unit", "source"],
    "properties": {
        "value_exact": {"type": "string"},
        "unit": {"type": "string"},
        "source": DOC_SOURCE_SCHEMA,
    },
}
DOCUMENT_VALUES_INDEPENDENT_FILE_SCHEMA = {
    "type": "object",
    "minProperties": 1,
    "additionalProperties": DOCUMENT_VALUE_ENTRY_SCHEMA,
}


def schema_errors(label: str, data, schema: dict) -> list[str]:
    validator = jsonschema.Draft7Validator(schema)
    out = []
    for err in validator.iter_errors(data):
        loc = "/".join(str(p) for p in err.absolute_path) or "<root>"
        out.append(f"SCHEMA ERROR {label} {loc}: {err.message}")
    return out


def document_values_family_errors(data) -> list[str]:
    # F-054/F-063: extracted_by must hold two identities of DIFFERENT, non-null families -- an
    # identity with no family is discarded before families are counted, so it can no longer stand
    # in as a second, distinct "family" of None alongside one real family.
    out = []
    if not isinstance(data, dict):
        return out
    for key, entry in data.items():
        if key == "prov.tail_unused" or not isinstance(entry, dict):
            continue
        eb = entry.get("extracted_by")
        if isinstance(eb, list) and len(eb) >= 2:
            families = {e.get("family") for e in eb if isinstance(e, dict) and e.get("family")}
            if len(families) < 2:
                out.append(
                    f"SCHEMA ERROR document_values.json {key}/extracted_by: does not hold two identities of different families"
                )
    return out


def cmd_schema(root: Path) -> int:
    evidence = root / W_REL / "evidence"
    problems: list[str] = []

    claims = load_json(evidence / "claims.json")
    if isinstance(claims, dict) and "claims" in claims:
        claims = claims["claims"]
    if claims is None:
        problems.append("SCHEMA ERROR claims.json <root>: not found or not valid JSON")
    else:
        problems += schema_errors("claims.json", claims, CLAIMS_FILE_SCHEMA)

    reqs = load_json(evidence / "requirements_map.json")
    if reqs is None:
        problems.append("SCHEMA ERROR requirements_map.json <root>: not found or not valid JSON")
    else:
        problems += schema_errors("requirements_map.json", reqs, REQUIREMENTS_FILE_SCHEMA)

    doc_values = load_json(evidence / "document_values.json")
    if doc_values is None:
        problems.append("SCHEMA ERROR document_values.json <root>: not found or not valid JSON")
    else:
        problems += schema_errors("document_values.json", doc_values, DOCUMENT_VALUES_FILE_SCHEMA)
        problems += document_values_family_errors(doc_values)

    anchors = load_json(evidence / "anchors.json")
    if anchors is None:
        problems.append("SCHEMA ERROR anchors.json <root>: not found or not valid JSON")
    else:
        problems += schema_errors("anchors.json", anchors, ANCHORS_FILE_SCHEMA)

    # F-061 (F-050 remainder): anchors_B.json was never schema-checked; it follows the same
    # per-entry anchors schema as anchors.json.
    anchors_b = load_json(evidence / "independent" / "anchors_B.json")
    if anchors_b is None:
        problems.append("SCHEMA ERROR anchors_B.json <root>: not found or not valid JSON")
    else:
        problems += schema_errors("anchors_B.json", anchors_b, ANCHORS_FILE_SCHEMA)

    # F-061 (F-050 remainder): the independent (pre-merge) document-value extractions were never
    # schema-checked either.
    for doc_fname in ("document_values_A.json", "document_values_B.json"):
        dv_independent = load_json(evidence / "independent" / doc_fname)
        if dv_independent is None:
            problems.append(f"SCHEMA ERROR {doc_fname} <root>: not found or not valid JSON")
        else:
            problems += schema_errors(doc_fname, dv_independent, DOCUMENT_VALUES_INDEPENDENT_FILE_SCHEMA)

    if problems:
        for p in problems:
            print(p)
        return 1
    print("CLAIMS SCHEMA PASSED")
    return 0


# ---------------------------------------------------------------------------
# --coverage mode
# ---------------------------------------------------------------------------

FORBIDDEN_RE = re.compile(r"^forbidden:(.+):(\d+)$")
COVERAGE_SOURCES = (
    "WRITING_EXECUTION_PLAN_REVIEWED_20260914.md",
    "CAMPAIGN_PREDECLARATION.md",
    "PLAN_REVIEW_LEDGER_20260914.md",
)


def cmd_coverage(root: Path) -> int:
    reqs = load_json(root / W_REL / "evidence" / "requirements_map.json")
    if reqs is None or not isinstance(reqs, list):
        print("requirements_map.json not found or not valid JSON")
        return 1
    if not reqs:
        print("requirements_map.json has no rows")
        return 1

    claims = load_claims(root) or []
    claims_by_id = {c.get("id"): c for c in claims}

    problems: list[str] = []
    seen_ids: set[str] = set()
    for row in reqs:
        rid = row.get("req_id")
        if not rid:
            problems.append(f"row with no req_id: {row!r}")
            continue
        if rid in seen_ids:
            problems.append(f"{rid}: duplicate req_id")
        seen_ids.add(rid)

        maps_to = row.get("maps_to")
        if not maps_to:
            problems.append(f"{rid}: empty maps_to")
            continue
        m = FORBIDDEN_RE.match(maps_to)
        if m:
            claim_id, idx = m.group(1), int(m.group(2))
            claim = claims_by_id.get(claim_id)
            forbidden = (claim or {}).get("forbidden_wording") or []
            if claim is None or idx >= len(forbidden):
                problems.append(f"{rid}: maps_to {maps_to!r} does not resolve")
            continue
        if maps_to not in claims_by_id:
            problems.append(f"{rid}: maps_to {maps_to!r} does not resolve to an existing claim")

    for fname in COVERAGE_SOURCES:
        if not any(fname in (row.get("source") or "") for row in reqs):
            problems.append(f"no requirements_map row's source mentions {fname}")

    if problems:
        for p in problems:
            print(p)
        return 1
    print(f"REQUIREMENTS COVERED ({len(reqs)} rows)")
    return 0


# ---------------------------------------------------------------------------
# --argument mode (P4)
# ---------------------------------------------------------------------------

def cmd_argument(root: Path) -> int:
    drs = load_drs(root)
    dr = next(
        (d for d in drs if isinstance(d["_data"], dict) and d["_data"].get("q_card") == "Q-ARGUMENT"),
        None,
    )
    if dr is None:
        print("no DR with q_card Q-ARGUMENT found")
        return 1
    outcome = dr["_data"].get("outcome")
    if not isinstance(outcome, str) or not outcome:
        print(f"{dr['_file']}: outcome is not a usable option letter ({outcome!r})")
        return 1

    opt_path = root / W_REL / "positioning" / f"argument_option_{outcome}.json"
    option = load_json(opt_path)
    if option is None:
        print(f"{opt_path} not found or not valid JSON")
        return 1

    problems: list[str] = []
    for field in ("option", "research_question", "spine", "contributions", "displays", "objections"):
        if not option.get(field):
            problems.append(f"argument_option_{outcome}.json: missing or empty field {field!r}")

    claims = load_claims(root) or []
    claims_by_id = {c.get("id"): c for c in claims}

    contributions = option.get("contributions") or []
    if not contributions:
        problems.append(f"argument_option_{outcome}.json: contributions is empty")
    for i, contrib in enumerate(contributions):
        claim_ids = contrib.get("claim_ids") or []
        if not claim_ids:
            problems.append(f"argument_option_{outcome}.json: contribution {i} has no claim_ids")
            continue
        types = []
        for cid in claim_ids:
            claim = claims_by_id.get(cid)
            if claim is None:
                problems.append(f"argument_option_{outcome}.json: contribution {i} claim_ids {cid!r} does not exist")
            else:
                types.append(claim.get("type"))
        if types and all(t in ("interpretation", "recommendation") for t in types):
            problems.append(f"argument_option_{outcome}.json: contribution {i} claim ids are all interpretation/recommendation")

    if problems:
        for p in problems:
            print(p)
        return 1
    print("ARGUMENT TRACE PASSED")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=None)
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--schema", action="store_true")
    group.add_argument("--coverage", action="store_true")
    group.add_argument("--argument", action="store_true")
    args = parser.parse_args(argv)

    root = resolve_root(args.root)
    if not root_confirmed(root):
        marker = root / ROOT_MARKER_REL
        print(f"UNTRACED <root>: {marker} not found (wrong --root?)")
        if not (args.schema or args.coverage or args.argument):
            print("CLAIMS TRACE FAILED (1)")
        return 1

    if args.schema:
        return cmd_schema(root)
    if args.coverage:
        return cmd_coverage(root)
    if args.argument:
        return cmd_argument(root)
    return cmd_trace(root)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
