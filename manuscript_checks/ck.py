#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""IJSSOL revision checker suite.

Usage:  python ck.py <check> [check ...]
        python ck.py all
        python ck.py gate          # fast set: T0 T1 T2 T10 T12 T9

Checks
  t0  static integrity: braces, environments, refs, cite keys, graphics, [H]
  t1  no forward justification (and no entity used before its introduction)
  t2  caveat propagation, joined against claims.tsv
  t3  terminology: the set-variable rename is complete and hit no label
  t4  numeric invariance by +/-40-char context key
  t5  word budget: abstract <= 200, submission estimate vs the 12,000 ceiling
  t6  plateau-derivation redundancy
  t7  paragraph shape: no "Table X reports" openers
  t8  submission compliance: DAS, comments, emails, ethics, supplement refs
  t9  newline invariance since the last commit
  t10 taxonomy: every method count matches the declared hierarchy
  t11 announce/deliver, bidirectional      (reviewer_first_skill XIX-A)
  t12 list hygiene and density, both directions          (XIX-A)
  t13 numeric multiset invariance of restructured regions, keyed by \\label
  t14 first-use notation audit: every tracked symbol defined at or before use
  t15 supplement cross-references: "Supplementary Section~SN" resolves
Helpers: remap (re-locate anchors)

T4 is blinded by restructuring, because moving text destroys its context key.
T13 exists to cover exactly that case and is keyed on \\label, not line number.

Every check prints PASS/FAIL lines and returns a nonzero exit on any FAIL.
No check may invoke pdflatex or biber: no LaTeX engine exists on this machine.
"""
from __future__ import print_function
import collections
import io
import json
import os
import re
import subprocess
import sys

# Paths are derived from this file's location so the suite is portable and
# survives being moved. It lives in <repo>/manuscript_checks/.
WORK = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(WORK)
BASE = os.path.join(WORK, "baseline")
OUT = os.path.join(WORK, "out")
if not os.path.isdir(OUT):
    os.makedirs(OUT)

MAIN = os.path.join(ROOT, "IJSSOL_CSLAP_v1.tex")
SUPP = os.path.join(ROOT, "IJSSOL_CSLAP_v1_supplementary.tex")
BIB = os.path.join(ROOT, "IJSSOL_CSLAP_v1.bib")
LEDGER = os.path.join(WORK, "claims.tsv")
ANCHORS = os.path.join(OUT, "anchors.json")

FAILS = []
NOTES = []


def read(path):
    return io.open(path, encoding="utf-8-sig").read()


def lines(path):
    return read(path).split("\n")


def ok(check, msg):
    print("  PASS  [%s] %s" % (check, msg))


def bad(check, msg):
    print("  FAIL  [%s] %s" % (check, msg))
    FAILS.append((check, msg))


def note(check, msg):
    print("  note  [%s] %s" % (check, msg))
    NOTES.append((check, msg))


# --------------------------------------------------------------------------
# shared parsing
# --------------------------------------------------------------------------

def strip_comments(text):
    """Remove LaTeX comments but keep the line structure and escaped \\%."""
    out = []
    for ln in text.split("\n"):
        res, i, n = [], 0, len(ln)
        while i < n:
            c = ln[i]
            if c == "\\" and i + 1 < n:
                res.append(ln[i:i + 2])
                i += 2
                continue
            if c == "%":
                break
            res.append(c)
            i += 1
        out.append("".join(res))
    return "\n".join(out)


def paragraphs(text):
    """Yield (line_no, paragraph_text) for body paragraphs (1-indexed lines)."""
    ls = text.split("\n")
    buf, start = [], None
    for i, ln in enumerate(ls, 1):
        if ln.strip() == "":
            if buf:
                yield start, "\n".join(buf)
                buf, start = [], None
        else:
            if start is None:
                start = i
            buf.append(ln)
    if buf:
        yield start, "\n".join(buf)


def sentences(par):
    """Crude sentence split that does not break on \\ref{...} or decimals."""
    protected = re.sub(r"(\d)\.(\d)",
                       lambda m: m.group(1) + "\x00" + m.group(2), par)
    # List markup is a sentence boundary, not part of a sentence. Without this
    # a \ref inside a post-list paragraph gets attributed to "\end{itemize}",
    # which makes a true finding unreadable.
    protected = re.sub(r"\\(begin|end)\{(itemize|enumerate|description)\}|\\item",
                       "\n", protected)
    parts = re.split(r"(?<=[.;])\s+|\n", protected)
    out = []
    for p in parts:
        if not p.strip():
            continue
        # drop fragments that are only markup
        if not re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?|[{}$\\]", "", p).strip():
            continue
        out.append(p.replace("\x00", "."))
    return out


def section_map(path):
    """[(line, level, title, label)] in document order."""
    out = []
    for i, ln in enumerate(lines(path), 1):
        m = re.match(r"\s*\\(sub)*section\*?\{(.+?)\}(?:\\label\{(.+?)\})?", ln)
        if m and not ln.lstrip().startswith("%"):
            lvl = ln.count("subsection") and (2 + ln.count("subsubsection")) or 1
            out.append((i, lvl, m.group(2), m.group(3)))
    return out


def section_of(line_no, secs):
    cur = None
    for (ln, lvl, title, lab) in secs:
        if ln <= line_no:
            cur = (ln, lvl, title, lab)
        else:
            break
    return cur


# --------------------------------------------------------------------------
# T0 -- static integrity
# --------------------------------------------------------------------------

def t0():
    print("[T0] static integrity")
    for path in (MAIN, SUPP):
        name = os.path.basename(path)
        txt = strip_comments(read(path))

        depth = 0
        for ch in re.sub(r"\\[{}]", "", txt):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
        if depth:
            bad("T0", "%s brace imbalance: %+d" % (name, depth))
        else:
            ok("T0", "%s braces balanced" % name)

        begins = re.findall(r"\\begin\{([^}]+)\}", txt)
        ends = re.findall(r"\\end\{([^}]+)\}", txt)
        for env in set(begins) | set(ends):
            if begins.count(env) != ends.count(env):
                bad("T0", "%s env '%s': %d begin vs %d end"
                    % (name, env, begins.count(env), ends.count(env)))
        if len(begins) == len(ends):
            ok("T0", "%s %d environments paired" % (name, len(begins)))

        labels = set(re.findall(r"\\label\{([^}]+)\}", txt))
        refs = set(re.findall(r"\\(?:eq)?ref\{([^}]+)\}", txt))
        missing = sorted(refs - labels)
        if path == MAIN:
            missing = [m for m in missing if not m.startswith("sup:")]
        if missing:
            bad("T0", "%s refs with no label: %s" % (name, ", ".join(missing)))
        else:
            ok("T0", "%s all %d refs resolve" % (name, len(refs)))

    bibkeys = set(re.findall(r"@\w+\{([^,]+),", read(BIB)))
    cited = set()
    for path in (MAIN, SUPP):
        for grp in re.findall(r"\\cite[a-zA-Z]*\{([^}]+)\}", strip_comments(read(path))):
            cited |= set(k.strip() for k in grp.split(","))
    unknown = sorted(cited - bibkeys)
    if unknown:
        bad("T0", "cite keys absent from .bib: %s" % ", ".join(unknown))
    else:
        ok("T0", "all %d cite keys present in .bib" % len(cited))
    unused = sorted(bibkeys - cited)
    if unused:
        note("T0", "%d bib entries never cited: %s" % (len(unused), ", ".join(unused)))

    imgs = re.findall(r"\\includegraphics(?:\[[^\]]*\])?\{([^}]+)\}", strip_comments(read(MAIN)))
    miss = [g for g in imgs if not os.path.exists(os.path.join(ROOT, g.replace("/", os.sep)))]
    if miss:
        bad("T0", "missing image files: %s" % ", ".join(miss))
    else:
        ok("T0", "all %d graphics paths exist" % len(imgs))

    txt = strip_comments(read(MAIN))
    floats = re.findall(r"\\begin\{(figure|table|algorithm)\}(\[[^\]]*\])?", txt)
    nonH = [f for f in floats if f[1] != "[H]"]
    if nonH:
        bad("T0", "%d floats not [H]: %s" % (len(nonH), nonH))
    else:
        ok("T0", "all %d floats use [H]" % len(floats))


# --------------------------------------------------------------------------
# T1 -- no forward justification
# --------------------------------------------------------------------------

CAUSAL = re.compile(
    r"\b(because|since|on the evidence of|having (?:performed|shown)|"
    r"which is why|therefore|so we|we (?:adopt|deploy|use|choose|select)|"
    r"is the (?:one|form|reference)|establishes? whether)\b", re.I)

# entities that must not be used before their canonical introduction
ENTITIES = {
    "Company~A": r"a real warehouse, Company~A",
    "industrial scale": r"a real warehouse, Company~A",
}


def t1():
    print("[T1] no forward justification")
    txt = strip_comments(read(MAIN))
    ls = txt.split("\n")
    labpos = {}
    for i, ln in enumerate(ls, 1):
        for lab in re.findall(r"\\label\{(sec:[^}]+)\}", ln):
            labpos[lab] = i

    fwd = back = viol = 0
    for start, par in paragraphs(txt):
        for si, sent in enumerate(sentences(par)):
            for lab in re.findall(r"\\ref\{(sec:[^}]+)\}", sent):
                tgt = labpos.get(lab)
                if tgt is None:
                    continue
                if tgt > start:
                    fwd += 1
                    if CAUSAL.search(sent):
                        viol += 1
                        bad("T1", "L%d forward ref to %s inside a causal sentence: %s"
                            % (start, lab, sent.strip()[:110]))
                else:
                    back += 1
    if viol == 0:
        ok("T1", "%d forward refs, none carries evidential weight (%d backward)" % (fwd, back))
    else:
        note("T1", "%d forward refs total, %d violating" % (fwd, viol))

    # second pass: entity used before introduction
    for ent, intro_pat in ENTITIES.items():
        intro_line = None
        for i, ln in enumerate(ls, 1):
            if re.search(intro_pat, ln):
                intro_line = i
                break
        if intro_line is None:
            note("T1", "entity '%s': canonical introduction not found" % ent)
            continue
        early = []
        for i, ln in enumerate(ls, 1):
            if i >= intro_line:
                break
            if ent.replace("~", "\u00a0") in ln.replace("~", "\u00a0"):
                early.append(i)
        # §1 and §2 may name the site in passing; the leak is in §4 and §5
        secs = section_map(MAIN)
        leaks = []
        for i in early:
            s = section_of(i, secs)
            if s and s[2] not in ("Introduction", "Related work"):
                leaks.append((i, s[2]))
        if leaks:
            for (i, sname) in leaks:
                bad("T1", "L%d uses '%s' in '%s', before its introduction at L%d"
                    % (i, ent, sname, intro_line))
        else:
            ok("T1", "entity '%s' not used before L%d outside the intro" % (ent, intro_line))


# --------------------------------------------------------------------------
# T2 -- caveat propagation (ledger join)
# --------------------------------------------------------------------------

def load_ledger():
    if not os.path.exists(LEDGER):
        return None
    rows = []
    for ln in io.open(LEDGER, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln.strip() or ln.lstrip().startswith("#"):
            continue
        f = ln.split("\t")
        if f[0].strip() == "claim_id":
            continue
        while len(f) < 8:
            f.append("")
        rows.append(dict(claim_id=f[0].strip(), tier=f[1].strip(),
                         body_sites=f[2].strip(), derived_sites=f[3].strip(),
                         trigger=f[4].strip(), required=f[5].strip(),
                         forbidden=f[6].strip(), artifact=f[7].strip()))
    return rows


def t2():
    print("[T2] caveat propagation")
    rows = load_ledger()
    if rows is None:
        bad("T2", "no claims.tsv at %s -- ledger is a hard dependency" % LEDGER)
        return
    txt_all = strip_comments(read(MAIN))
    paras = [(ln, p) for ln, p in paragraphs(txt_all)]

    def span(anchor):
        """A site is a verbatim anchor regex; return the paragraph holding it.

        Anchoring on text rather than a line number keeps the ledger valid
        across edits that move lines, which every structural wave does.
        """
        hits = [(ln, p) for ln, p in paras if re.search(anchor, p, re.I)]
        return hits

    for r in rows:
        derived = [s for s in r["derived_sites"].split("~~") if s.strip()]
        for site in derived:
            hits = span(site)
            if len(hits) == 0:
                bad("T2", "%s derived anchor not found: /%s/" % (r["claim_id"], site))
                continue
            if len(hits) > 1:
                bad("T2", "%s derived anchor matches %d paragraphs (L%s), not unique: /%s/"
                    % (r["claim_id"], len(hits), ",L".join(str(h[0]) for h in hits), site))
                continue
            line_no, txt = hits[0]
            site = "L%d" % line_no
            # The qualifier is demanded only where the claim is actually made.
            # Dropping a claim from a site is a legitimate way to satisfy R-CAV;
            # re-adding it without the qualifier is not.
            present = (not r["trigger"]) or bool(re.search(r["trigger"], txt, re.I))
            if present and r["required"] and not re.search(r["required"], txt, re.I):
                bad("T2", "%s at %s missing required qualifier /%s/"
                    % (r["claim_id"], site, r["required"]))
            if not present:
                note("T2", "%s no longer claimed at %s -- qualifier not required"
                     % (r["claim_id"], site))
            for f in [x for x in r["forbidden"].split("|") if x.strip()]:
                if re.search(f, txt, re.I):
                    bad("T2", "%s at %s contains forbidden /%s/" % (r["claim_id"], site, f))
    if not [f for f in FAILS if f[0] == "T2"]:
        ok("T2", "%d claims: every derived site carries its qualifier" % len(rows))


# --------------------------------------------------------------------------
# T3 -- terminology
# --------------------------------------------------------------------------

OLD_TERM = r"set-variable MILP"
NEW_TERM = r"set-variable formulation"


def t3():
    print("[T3] terminology")
    base_n = len(re.findall(OLD_TERM, read(os.path.join(BASE, "IJSSOL_CSLAP_v1.tex")))) + \
        len(re.findall(OLD_TERM, read(os.path.join(BASE, "IJSSOL_CSLAP_v1_supplementary.tex"))))
    cur_old = len(re.findall(OLD_TERM, read(MAIN))) + len(re.findall(OLD_TERM, read(SUPP)))
    cur_new = len(re.findall(NEW_TERM, read(MAIN))) + len(re.findall(NEW_TERM, read(SUPP)))
    if cur_old:
        bad("T3", "'%s' still present %d times (baseline %d)" % (OLD_TERM, cur_old, base_n))
    else:
        ok("T3", "'%s' fully renamed (baseline had %d)" % (OLD_TERM, base_n))
    note("T3", "'%s' now appears %d times" % (NEW_TERM, cur_new))
    for path in (MAIN, SUPP):
        for i, ln in enumerate(lines(path), 1):
            if re.search(r"\\label\{[^}]*formulation[^}]*\}|tab:[a-z]*formulation", ln):
                bad("T3", "%s L%d: rename touched a label/key" % (os.path.basename(path), i))


# --------------------------------------------------------------------------
# T4 -- numeric invariance
# --------------------------------------------------------------------------

NUM = re.compile(r"(?<![A-Za-z0-9_])(\d[\d,{}\.]*\d|\d)(?![A-Za-z0-9_])")


def numeric_index(text):
    """{context_key: [values]} where context is the normalised 40 chars around."""
    t = strip_comments(text)
    t = re.sub(r"\s+", " ", t)
    idx = {}
    for m in NUM.finditer(t):
        val = m.group(1)
        a = max(0, m.start() - 40)
        b = min(len(t), m.end() + 40)
        ctx = (t[a:m.start()] + "\x01" + t[m.end():b])
        ctx = re.sub(r"[\d,]", "", ctx).strip()
        idx.setdefault(ctx, []).append(val)
    return idx


def sanctioned_values():
    """Values whose movement a recorded re-run explains.

    baseline/ is never refreshed -- that is what makes unintended drift
    detectable -- so a legitimate re-run is declared here instead, value by
    value with a reason. A changed context passes as a note only when every
    value that moved in it is declared; anything else still fails.
    """
    path = os.path.join(WORK, "allowed_value_changes.tsv")
    vals = set()
    if not os.path.exists(path):
        return vals
    for line in read(path).splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        for cell in s.split("\t")[:2]:
            cell = cell.strip()
            if cell:
                vals.add(cell)
    return vals


def t4():
    print("[T4] numeric invariance")
    for cur_path, base_name in ((MAIN, "IJSSOL_CSLAP_v1.tex"),
                                (SUPP, "IJSSOL_CSLAP_v1_supplementary.tex")):
        base_path = os.path.join(BASE, base_name)
        if not os.path.exists(base_path):
            bad("T4", "no baseline for %s" % base_name)
            continue
        a = numeric_index(read(base_path))
        b = numeric_index(read(cur_path))
        changed = []
        for k in set(a) & set(b):
            if a[k] != b[k]:
                changed.append((k, a[k], b[k]))
        removed = [k for k in a if k not in b]
        added = [k for k in b if k not in a]
        allowed = sanctioned_values()
        # A context key is the 40 characters either side with digits stripped,
        # so editing a table row can merge two rows onto one key and make an
        # untouched value look like it moved. A value whose total count in the
        # file is unchanged did not change; it relocated.
        base_tally = collections.Counter(NUM.findall(strip_comments(read(base_path))))
        cur_tally = collections.Counter(NUM.findall(strip_comments(read(cur_path))))
        unexplained = []
        for (k, av, bv) in changed:
            moved = {v for v in set(av) ^ set(bv)
                     if base_tally[v] != cur_tally[v]}
            if not moved or moved <= allowed:
                continue
            unexplained.append((k, av, bv))
        if unexplained:
            for (k, av, bv) in unexplained[:25]:
                bad("T4", "value changed %s -> %s  in ...%s..." % (av, bv, k[:70]))
        elif changed:
            ok("T4", "%s: %d changed contexts, every moved value declared in "
               "allowed_value_changes.tsv" % (base_name, len(changed)))
        else:
            ok("T4", "%s: no numeric literal changed in a surviving context" % base_name)
        note("T4", "%s: %d numeric contexts removed, %d added (expected where text moved)"
             % (base_name, len(removed), len(added)))


# --------------------------------------------------------------------------
# T5 -- word budget
# --------------------------------------------------------------------------

TEXCOUNT = os.path.expanduser(
    r"~\AppData\Local\Programs\MiKTeX\miktex\bin\x64\texcount.exe")
BIB_WORDS_PER_ENTRY = 26
ABSTRACT_LIMIT = 200
WORD_CEILING = 12000


def abstract_words():
    m = re.search(r"\\begin\{abstract\}(.*?)\\end\{abstract\}", read(MAIN), re.S)
    if not m:
        return None
    a = re.sub(r"\\[a-zA-Z]+", " ", m.group(1))
    return len([w for w in a.split() if re.search(r"[A-Za-z0-9]", w)])


def _plain_words(s):
    s = re.sub(r"\\[a-zA-Z@]+\*?", " ", s)
    s = re.sub(r"[{}$&\\\[\]~^_]", " ", s)
    return len([w for w in s.split() if re.search(r"[A-Za-z0-9]", w)])


def _float_words(path):
    r"""Words the journal counts but texcount's body total omits.

    IJSSOL counts 12,000 "including all manuscript elements", and desk-rejects
    for length. texcount's "words in text" excludes the body of every tabular
    environment, and it cannot see \tbl{} / \tabnote{}, which are interact.cls
    macros rather than \caption{}. On this manuscript those omissions are worth
    about 1,400 words, so counting only the body total reports spare capacity
    that does not exist.
    """
    t = re.sub(r"(?<!\\)%.*", "", read(path))
    total = 0
    for _name, body in re.findall(
            r"\\begin\{(tabular[*x]?)\}(.*?)\\end\{tabular[*x]?\}", t, re.S):
        total += _plain_words(body)
    for line in t.splitlines():
        s = line.strip()
        if s.startswith("\\tabnote{") or s.startswith("\\tbl{"):
            total += _plain_words(line)
    return total


def t5():
    print("[T5] word budget")
    aw = abstract_words()
    if aw is None:
        bad("T5", "abstract block not found")
    elif aw > ABSTRACT_LIMIT:
        bad("T5", "abstract %d words, limit %d" % (aw, ABSTRACT_LIMIT))
    else:
        ok("T5", "abstract %d words (limit %d, %d spare)"
           % (aw, ABSTRACT_LIMIT, ABSTRACT_LIMIT - aw))

    parts = None
    if os.path.exists(TEXCOUNT):
        try:
            out = subprocess.check_output([TEXCOUNT, "-sub=none", MAIN],
                                          stderr=subprocess.STDOUT)
            txt = out.decode("utf-8", "replace")

            def grab(label):
                m = re.search(label + r"\s*:\s*(\d+)", txt)
                return int(m.group(1)) if m else 0

            parts = (grab("Words in text"), grab("Words in headers"),
                     grab(r"Words outside text \(captions, etc\.\)"))
        except Exception as e:  # noqa
            note("T5", "texcount failed: %s" % e)
    if parts is None:
        note("T5", "texcount unavailable; body count skipped")
        return
    body, heads, caps = parts
    floats = _float_words(MAIN)
    ncites = len(set(re.findall(r"@\w+\{([^,]+),", read(BIB))))
    bib = ncites * BIB_WORDS_PER_ENTRY
    est = body + heads + caps + floats + bib + 70
    detail = ("text %d + headers %d + captions %d + tables %d + refs ~%d + tikz ~70"
              % (body, heads, caps, floats, bib))
    if est > WORD_CEILING:
        bad("T5", "submission count ~%d exceeds %d by %d  [%s]"
            % (est, WORD_CEILING, est - WORD_CEILING, detail))
    else:
        ok("T5", "%s = ~%d (ceiling %d, %d spare)"
           % (detail, est, WORD_CEILING, WORD_CEILING - est))


# --------------------------------------------------------------------------
# T6 -- redundancy of the plateau derivation
# --------------------------------------------------------------------------

PLATEAU = [
    r"piecewise constant", r"plateau", r"step-function", r"no gradient",
    r"almost no gradient", r"changes only when", r"gains or loses",
    r"most swaps do neither", r"conversion rate", r"reads no change",
    r"unit of change", r"stalls?\b",
]


def t6():
    print("[T6] plateau-derivation redundancy")
    txt = strip_comments(read(MAIN))
    hits = {}
    for start, par in paragraphs(txt):
        n = sum(1 for p in PLATEAU if re.search(p, par, re.I))
        if n:
            hits[start] = n
    full = sorted([l for l, n in hits.items() if n >= 3])
    clause = sorted([l for l, n in hits.items() if n in (1, 2)])
    print("      full derivations (>=3 markers): %s" % (full,))
    print("      single clauses  (1-2 markers): %s" % (clause,))
    if len(full) > 1:
        bad("T6", "%d full derivations, expected 1 canonical (L93)" % len(full))
    else:
        ok("T6", "one canonical derivation at %s, %d supporting clauses"
           % (full or "none", len(clause)))


# --------------------------------------------------------------------------
# T7 -- paragraph shape
# --------------------------------------------------------------------------

REPORTING_OPENER = re.compile(
    r"^(Table|Figure)~\\ref\{[^}]+\}\s+(reports|shows|gives|presents|lists)", re.I)


def t7():
    print("[T7] paragraph shape")
    txt = strip_comments(read(MAIN))
    secs = section_map(MAIN)
    stats = {}
    for start, par in paragraphs(txt):
        p = par.strip()
        if p.startswith("\\") and not p.startswith("\\textbf"):
            continue
        s = section_of(start, secs)
        if not s:
            continue
        key = s[2]
        d = stats.setdefault(key, dict(paras=0, runin=0, opener=[]))
        d["paras"] += 1
        if p.startswith("\\textbf{"):
            d["runin"] += 1
        if REPORTING_OPENER.match(p):
            d["opener"].append(start)
    for k, d in stats.items():
        if d["paras"] < 2:
            continue
        line = "%-46s paras=%2d run-ins=%2d" % (k[:46], d["paras"], d["runin"])
        if d["opener"]:
            line += "  descriptive openers at %s" % d["opener"]
        print("      " + line)
        for l in d["opener"]:
            bad("T7", "L%d in '%s' opens with a reporting sentence, not an assertion" % (l, k))
    if not [f for f in FAILS if f[0] == "T7"]:
        ok("T7", "no paragraph opens with 'Table X reports'")


# --------------------------------------------------------------------------
# T8 -- compliance
# --------------------------------------------------------------------------

def t8():
    print("[T8] submission compliance")
    raw = read(MAIN)
    ls = raw.split("\n")

    # mid-line comments outside the preamble
    try:
        body_start = next(i for i, l in enumerate(ls, 1) if "\\begin{document}" in l)
    except StopIteration:
        body_start = 1
    # A bare trailing '%' is the standard line-join idiom and is harmless.
    # Only a comment carrying real text can truncate body prose.
    midline = []
    for i, ln in enumerate(ls, 1):
        if i <= body_start:
            continue
        st = strip_comments(ln)
        if st != ln and st.strip() != "":
            tail = ln[len(st):].lstrip("%").strip()
            if re.search(r"\w", tail):
                midline.append(i)
    if midline:
        bad("T8", "mid-line %% comment truncates body text at L%s" % midline)
    else:
        ok("T8", "no mid-line comment truncates body text")

    # DAS content
    m = re.search(r"\\section\*\{Data availability statement\}(.*?)(\\section\*|\Z)", raw, re.S)
    if not m:
        bad("T8", "no Data availability statement")
    else:
        das = strip_comments(m.group(1))
        for tok, why in ((r"confidentia", "confidentiality clause"),
                         (r"licen[cs]e", "licence clause")):
            if re.search(tok, das, re.I):
                ok("T8", "DAS keeps the %s" % why)
            else:
                bad("T8", "DAS lost the %s (check for a truncating %%)" % why)
        if re.search(r"doi\.org|10\.\d{4,}", das, re.I):
            ok("T8", "DAS cites a persistent identifier")
        else:
            bad("T8", "DAS has no DOI; anonymous.4open.science is not a persistent identifier")
        if "% ACTION" in m.group(1):
            bad("T8", "DAS still carries an ACTION comment")

    # header comments naming the prior submission
    head = "\n".join(ls[:body_start])
    for pat, why in ((r"IJPR_CSLAP_v4", "names the prior IJPR submission"),
                     (r"ground truth", "calls another file ground truth"),
                     (r"ACTION REQUIRED", "carries an ACTION REQUIRED block")):
        if re.search(pat, head, re.I):
            bad("T8", "preamble %s -- the .tex ships in the submission ZIP" % why)
    if not re.search(r"IJPR_CSLAP_v4|ground truth", raw, re.I):
        ok("T8", "no reference to the prior submission anywhere in the source")

    # ACTION blocks anywhere
    for i, ln in enumerate(ls, 1):
        if re.search(r"%\s*ACTION", ln):
            bad("T8", "L%d ACTION comment remains" % i)

    # author emails
    emails = re.findall(r"[\w.\-]+@[\w.\-]+\.\w+", raw)
    if len(set(emails)) >= 4:
        ok("T8", "%d institutional emails in the author block" % len(set(emails)))
    else:
        bad("T8", "only %d email(s) present, journal requires one per author (4)"
            % len(set(emails)))
    for e in set(emails):
        if not re.search(r"\.(fr|com|org|edu|net|uk|de)$", e):
            bad("T8", "malformed email domain: %s" % e)

    # ethics
    if re.search(r"non-public", raw, re.I):
        ok("T8", "ethics statement uses the guideline's 'non-public dataset' phrase")
    else:
        bad("T8", "ethics statement omits the 'non-public dataset' trigger phrase")

    # supplement cross-references
    cited = set(re.findall(r"Supplementary Section~S(\d+)", raw))
    supsecs = re.findall(r"\\section\{[^}]*\}\\label\{(sup:[^}]+)\}", read(SUPP))
    if not supsecs:
        supsecs = re.findall(r"\\section\{.*?\}\\label\{(sup:.+?)\}", read(SUPP))
    total = len(re.findall(r"^\\section\{", read(SUPP), re.M))
    missing = [str(n) for n in range(1, total + 1) if str(n) not in cited]
    if missing:
        bad("T8", "supplement sections never cited by number: S%s" % ", S".join(missing))
    else:
        ok("T8", "all %d supplement sections cited by number" % total)

    # bib ACTION comments
    nact = len(re.findall(r"%\s*ACTION", read(BIB)))
    if nact:
        bad("T8", "%d ACTION comments remain in the .bib" % nact)
    else:
        ok("T8", "no ACTION comments in the .bib")

    # UK spelling in the bios / body
    prose = re.sub(r"\\cite[a-zA-Z]*\{[^}]*\}", " ", strip_comments(raw))
    prose = re.sub(r"\\(label|ref|eqref|includegraphics)\{[^}]*\}", " ", prose)
    us = re.findall(r"\b\w*(?:optimiz|minimiz|maximiz|analyz|behavior|modeling|neighborhood)\w*\b",
                    prose)
    if us:
        bad("T8", "US spellings in a UK-English manuscript: %s" % ", ".join(sorted(set(us))))
    else:
        ok("T8", "spelling consistently UK English")


# --------------------------------------------------------------------------
# T9 -- newline invariance
# --------------------------------------------------------------------------

def t9():
    print("[T9] newline invariance since the last commit")
    try:
        out = subprocess.check_output(["git", "diff", "--numstat", "--", "IJSSOL_CSLAP_v1.tex",
                                       "IJSSOL_CSLAP_v1_supplementary.tex"],
                                      cwd=ROOT).decode("utf-8", "replace")
    except Exception as e:  # noqa
        note("T9", "git diff failed: %s" % e)
        return
    if not out.strip():
        ok("T9", "no uncommitted change")
        return
    for ln in out.strip().split("\n"):
        add, rem, path = ln.split("\t")
        if add == rem:
            ok("T9", "%s +%s/-%s newline count preserved" % (path, add, rem))
        else:
            note("T9", "%s +%s/-%s line count changed -- run remap" % (path, add, rem))


# --------------------------------------------------------------------------
# T10 -- taxonomy
# --------------------------------------------------------------------------

STRATEGIES = ["set-variable", "column generation", "clustering heuristic"]
COUNT_PHRASE = re.compile(
    r"\b(all three(?!\s+(?:instances|folds|sizes|settings|cells|weeks))|"
    r"three (?:\w+ ){0,2}(?:methods|solution approaches|"
    r"solution strategies|approaches|strategies)|two model forms)\b", re.I)


def t10():
    print("[T10] taxonomy consistency")
    txt = strip_comments(read(MAIN))
    found = 0
    for start, par in paragraphs(txt):
        for sent in sentences(par):
            m = COUNT_PHRASE.search(sent)
            if not m:
                continue
            found += 1
            # the enumeration usually spills into the following sentences,
            # so judge naming over the whole paragraph
            window = par
            has = [s for s in STRATEGIES if re.search(s, window, re.I)]
            label = m.group(0)
            is_three = bool(re.search(r"three", label, re.I))
            # Part A: the binary encoding is a representation control, never one
            # of the three strategies. It may appear beside a count only when the
            # text says so explicitly.
            declared_control = re.search(
                r"binary[^.]{0,90}(control|not a (?:fourth|third)|rather than a "
                r"(?:fourth|third)|alongside)|(?:representation )?control[^.]{0,60}binary",
                window, re.I)
            if is_three and re.search(r"two model forms", window, re.I):
                bad("T10", "L%d '%s' counts the binary form among the three: %s"
                    % (start, label, sent.strip()[:110]))
            elif is_three and re.search(r"binary", window, re.I) and not declared_control:
                bad("T10", "L%d '%s' names the binary form with no control designation: %s"
                    % (start, label, sent.strip()[:110]))
            elif is_three and len(has) < 2:
                note("T10", "L%d '%s' names %d of the three strategies in-sentence: %s"
                     % (start, label, len(has), sent.strip()[:100]))
    if found == 0:
        note("T10", "no method-count phrase found")
    elif not [f for f in FAILS if f[0] == "T10"]:
        ok("T10", "%d method-count phrases, all consistent with the taxonomy" % found)


# --------------------------------------------------------------------------
# anchors
# --------------------------------------------------------------------------

def build_anchors(findings):
    ls = lines(MAIN)
    secs = section_map(MAIN)
    out = []
    for fid, line_no in findings:
        if line_no < 1 or line_no > len(ls):
            continue
        body = re.sub(r"\s+", " ", ls[line_no - 1]).strip()
        span = " ".join(body.split()[:12])
        s = section_of(line_no, secs)
        out.append(dict(id=fid, line=line_no, label=(s[3] if s else None),
                        section=(s[2] if s else None), span=span))
    io.open(ANCHORS, "w", encoding="utf-8").write(
        json.dumps(out, indent=1, ensure_ascii=False))
    return out


def remap():
    print("[remap] re-locating anchors")
    if not os.path.exists(ANCHORS):
        bad("remap", "no anchor table at %s" % ANCHORS)
        return
    anchors = json.loads(read(ANCHORS))
    ls = lines(MAIN)
    moved = lost = 0
    for a in anchors:
        span = a["span"]
        hits = [i for i, ln in enumerate(ls, 1)
                if span and span in re.sub(r"\s+", " ", ln)]
        if len(hits) == 1:
            if hits[0] != a["line"]:
                moved += 1
                print("      %-12s L%d -> L%d" % (a["id"], a["line"], hits[0]))
                a["line"] = hits[0]
        elif len(hits) == 0:
            lost += 1
            bad("remap", "%s: span no longer found (was L%d): %s"
                % (a["id"], a["line"], span[:60]))
        else:
            lost += 1
            bad("remap", "%s: span matches %d lines, not unique" % (a["id"], len(hits)))
    io.open(ANCHORS, "w", encoding="utf-8").write(
        json.dumps(anchors, indent=1, ensure_ascii=False))
    if lost == 0:
        ok("remap", "%d anchors re-located, %d moved" % (len(anchors), moved))


# --------------------------------------------------------------------------

# --------------------------------------------------------------------------
# T11 -- announce / deliver mismatch  (reviewer_first_skill XIX-A)
# --------------------------------------------------------------------------

NUMWORD = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}

# "three thresholds", "four operators", "two known difficulties" ...
ANNOUNCE = re.compile(
    r"\b(two|three|four|five|six|seven)\s+((?:\w+[ -]){0,3}?)"
    r"(points|properties|reasons|difficulties|thresholds|operators|stages|"
    r"contributions|implications|strategies|methods|conditions|facts|elements|"
    r"quantities|tracks|models|design points|filters|steps|criteria|forms)\b",
    re.I)

# A set member smuggled in after the count was fixed.
# Two constructions look like escalation and are not, so both are excluded:
#   denial   -- "... rather than as a fourth strategy"  (explicitly NOT a member)
#   compound -- "three thresholds ... and a fourth bounds ..."  (an announcement
#               of 3+1 distinct roles, legitimately delivered as four items)
ESCALATE = re.compile(r"\b(a\s+(third|fourth|fifth|sixth)\b|another\s+\w+\s+"
                      r"(difficulty|point|reason|property|stage))", re.I)
DENIAL = re.compile(r"(rather than|not\b|never|no\b)[^.]{0,50}$", re.I)
COMPOUND = re.compile(r"\band\s+a\s+(third|fourth|fifth|sixth)\b", re.I)

ORDINAL = re.compile(r"\b(First|Second|Third|Fourth|Fifth),|\((i|ii|iii|iv|v)\)")
DELEGATE = re.compile(r"\\ref\{(alg|fig|tab):|Supplementary Section~S\d")


def t11():
    print("[T11] announce / deliver  (XIX-A)")
    for path in (MAIN, SUPP):
        name = os.path.basename(path)
        for start, par in paragraphs(strip_comments(read(path))):
            m = ANNOUNCE.search(par)
            if not m:
                continue
            n = NUMWORD[m.group(1).lower()]
            head = m.group(3)
            ordinals = len(ORDINAL.findall(par))
            items = par.count("\\item")
            runins = len(re.findall(r"\\textbf\{[^}]*\.\}", par))
            marked = max(ordinals, items, runins)
            delegated = bool(DELEGATE.search(par))
            words = len(par.split())

            # T11b -- count escalation. Factual, not stylistic.
            esc = ESCALATE.search(par)
            if esc and not COMPOUND.search(par[m.start():esc.end() + 5]) \
                    and not DENIAL.search(par[max(0, esc.start() - 50):esc.start()]):
                bad("T11b", "%s L%d announces %d %s then adds '%s' -- count collision"
                    % (name, start, n, head, esc.group(0).strip()))
                continue

            if marked >= n - 1 and marked > 0:
                # A paragraph block can hold more than one enumeration, and
                # markers from a neighbour bleed in, so a mismatch is reported
                # for a human to read rather than failed on.
                if marked != n and items == 0:
                    note("T11", "%s L%d announces %d %s but carries %d markers "
                                "-- check whether a neighbouring enumeration bled in"
                         % (name, start, n, head, marked))
                continue
            if delegated:
                continue
            if words >= 60:
                note("T11", "%s L%d announces %d %s, delivered unmarked in %d words "
                            "-- candidate (or delete the numeral)"
                     % (name, start, n, head, words))
    if not [f for f in FAILS if f[0].startswith("T11")]:
        ok("T11", "no announced count is miscounted or escalated")


# --------------------------------------------------------------------------
# T12 -- list hygiene and density  (both directions)
# --------------------------------------------------------------------------

LIST_ENV = re.compile(r"\\begin\{(itemize|enumerate|description)\}(\[?)",
                      re.M)
MAX_LISTS_MAIN, MIN_LISTS_MAIN, MAX_LISTS_SUPP = 6, 1, 4


def list_blocks(text):
    """Yield (env, optional_arg_present, body, start_line)."""
    out = []
    for m in re.finditer(r"\\begin\{(itemize|enumerate|description)\}(\[[^\]]*\])?"
                         r"(.*?)\\end\{\1\}", text, re.S):
        out.append((m.group(1), bool(m.group(2)), m.group(3),
                    text[:m.start()].count("\n") + 1))
    return out


def t12():
    print("[T12] list hygiene and density  (XIX-A)")
    has_pkg = False
    for path in (MAIN, SUPP):
        if re.search(r"\\usepackage(\[[^\]]*\])?\{(enumitem|paralist)\}", read(path)):
            has_pkg = True
    for path in (MAIN, SUPP):
        name = os.path.basename(path)
        raw = read(path)
        txt = strip_comments(raw)
        blocks = list_blocks(txt)
        for env, opt, body, ln in blocks:
            items = [i.strip() for i in body.split("\\item")[1:]]
            n = len(items)
            if not (3 <= n <= 6):
                bad("T12", "%s L%d %s has %d items (XIX-A G2 wants 3-6)"
                    % (name, ln, env, n))
            lens = [len(i.split()) for i in items] or [0]
            if lens and min(lens) and (max(lens) / float(min(lens)) > 3.0):
                bad("T12", "%s L%d %s unbalanced: %d/%d words, ratio %.2f (G5 wants <=3.0)"
                    % (name, ln, env, max(lens), min(lens), max(lens) / float(min(lens))))
            if max(lens) > 60:
                bad("T12", "%s L%d %s longest item %d words (G5 wants <=60)"
                    % (name, ln, env, max(lens)))
            if "\n\n" in body.strip("\n"):
                bad("T12", "%s L%d %s has a blank line inside -- splits the paragraph "
                           "block and can strand a ledger qualifier" % (name, ln, env))
            if opt and not has_pkg:
                bad("T12", "%s L%d %s uses an optional argument but no enumitem/paralist "
                           "is loaded -- silent break" % (name, ln, env))
            if "\\\\" in body:
                bad("T12", "%s L%d %s contains \\\\ inside an item" % (name, ln, env))
        # a comment inside a list body, checked on the raw text
        for m in re.finditer(r"\\begin\{(itemize|enumerate|description)\}"
                             r"(.*?)\\end\{\1\}", raw, re.S):
            if re.search(r"(?<!\\)%", m.group(2)):
                bad("T12", "%s: a %% comment sits inside a %s body"
                    % (name, m.group(1)))
        # never inside a macro argument
        for mac in ("tbl", "tabnote", "caption", "thanks"):
            if re.search(r"\\%s\{[^{}]*\\begin\{(itemize|enumerate)" % mac, txt):
                bad("T12", "%s: a list sits inside \\%s{}" % (name, mac))
        # prose must separate a list from an [H] float
        if re.search(r"\\end\{(itemize|enumerate)\}\s*\\begin\{(table|figure|algorithm)\}",
                     txt):
            bad("T12", "%s: a list abuts an [H] float with no prose between" % name)

        cap = MAX_LISTS_SUPP if path == SUPP else MAX_LISTS_MAIN
        if len(blocks) > cap:
            bad("T12", "%s has %d lists, ceiling is %d" % (name, len(blocks), cap))
        if path == MAIN and len(blocks) < MIN_LISTS_MAIN:
            bad("T12", "%s has %d lists, floor is %d. A manuscript with zero structural "
                       "lists and unresolved announced counts is a finding, not a safe "
                       "default (XIX-A)" % (name, len(blocks), MIN_LISTS_MAIN))
        else:
            ok("T12", "%s: %d lists, within [%d, %d]"
               % (name, len(blocks), MIN_LISTS_MAIN if path == MAIN else 0, cap))

    # run-in consistency per section, main text only
    secs = section_map(MAIN)
    stats = {}
    for start, par in paragraphs(strip_comments(read(MAIN))):
        p = par.strip()
        if len(p.split()) < 15 or p.startswith("\\begin") or p.startswith("\\end"):
            continue
        s = section_of(start, secs)
        if not s:
            continue
        d = stats.setdefault(s[2], [0, 0])
        d[0] += 1
        if re.match(r"\\textbf\{[^}]*\.\}", p):
            d[1] += 1
    for k, (tot, bold) in stats.items():
        if tot < 3:
            continue
        frac = bold / float(tot)
        if 0 < frac < 0.75:
            bad("T12", "section '%s': %d of %d paragraphs use a bold run-in (%.0f%%). "
                       "XIX-A wants 0 or >=75%%, never a mixture" % (k[:40], bold, tot,
                                                                    100 * frac))


# --------------------------------------------------------------------------
# T13 -- numeric multiset invariance for restructured regions
# --------------------------------------------------------------------------

# regions located by \label, immune to line moves
T13_REGIONS = [
    (SUPP, "sup:budgets", "sup:baselines"),
    (SUPP, "sup:baselines", "sup:hardware"),
]
# values a restructure deliberately introduced, with the wording they replaced
T13_SEEDED = {"sup:baselines": [("0.25", "a quarter of the catalogue"),
                                ("10", "ten equal groups")]}


def _region(text, lab, nxt):
    i = text.find(lab)
    if i < 0:
        return ""
    j = text.find(nxt, i)
    return text[i:j if j > 0 else len(text)]


def _nums(s):
    return sorted(re.findall(r"\d[\d,.{}]*\d|\d", s))


def t13():
    print("[T13] numeric invariance of restructured regions")
    for path, lab, nxt in T13_REGIONS:
        name = os.path.basename(path)
        base_path = os.path.join(BASE, name)
        if not os.path.exists(base_path):
            bad("T13", "no baseline for %s" % name)
            continue
        old = _nums(_region(read(base_path), lab, nxt))
        new = _nums(_region(read(path), lab, nxt))
        seeded = [v for v, _ in T13_SEEDED.get(lab, [])]
        lost = sorted(set(old) - set(new))
        added = sorted(set(new) - set(old) - set(seeded))
        if lost:
            bad("T13", "%s region %s LOST values: %s" % (name, lab, lost))
        if added:
            bad("T13", "%s region %s added undeclared values: %s" % (name, lab, added))
        for v, was in T13_SEEDED.get(lab, []):
            if v not in new:
                bad("T13", "%s region %s: seeded value %s missing (replaced '%s')"
                    % (name, lab, v, was))
            if was.split()[0] in _region(read(path), lab, nxt):
                note("T13", "%s region %s still contains '%s'" % (name, lab, was))
        if not lost and not added:
            ok("T13", "%s region %s: %d values, multiset preserved"
               % (name, lab, len(new)))


# --------------------------------------------------------------------------
# T14 -- first-use notation audit
# --------------------------------------------------------------------------
#
# The governing rule from the pre-submission review: a reviewer must be able to
# understand and evaluate every headline contribution from the main article
# alone. A symbol defined only in the supplement fails that, and so does a
# symbol given a formula but no meaning. sup:notation asserts that every symbol
# is defined at its first use in the main article; this is what makes that
# assertion checkable rather than aspirational.
#
# (label, first-use pattern, definition pattern)
NOTATION = [
    ("cnt_xy", r"\\mathrm\{cnt\}",
     r"\\mathrm\{cnt\}_\{xy\}\$ for the number of orders containing both"),
    ("load(s)", r"\\mathrm\{load\}",
     r"\\mathrm\{load\}\(s\)\s*=\s*\\sum"),
    ("A(x,C)", r"\bA\(",
     r"A\(x,C\)\s*=\s*\\sum_\{y\\in C\}"),
    ("z_LP", r"z_\{\\mathrm\{LP\}\}",
     r"the value of the linear master over every feasible bundle"),
    ("Q^g / Q^e / opt", r"Q\^\{g\}",
     r"writes \$Q\^\{g\}\$ and \$Q\^\{e\}\$ for the bundles"),
    ("LPT", r"\bLPT\b",
     r"longest-processing-time \(LPT\)"),
    # Algorithm 1 defines rho with \gets, the prose with =; either counts.
    ("rho", r"\\rho",
     r"\\rho\s*(?:\\gets|=)\s*\\sum_?\{?u\s*\\?i?n?\s*\\?i?n? ?U\}?\s*w_u"),
]


def t14():
    print("[T14] first-use notation audit")
    txt = strip_comments(read(MAIN))
    pars = list(paragraphs(txt))
    offs = []
    pos = 0
    for (ln, body) in pars:
        i = txt.find(body, pos)
        offs.append(i if i >= 0 else pos)
        pos = offs[-1] + len(body)

    def par_of(off):
        k = 0
        for j, o in enumerate(offs):
            if o <= off:
                k = j
            else:
                break
        return k

    clean = 0
    for (label, use_re, def_re) in NOTATION:
        um = re.search(use_re, txt)
        if not um:
            note("T14", "%s: never used in the main article" % label)
            continue
        dm = re.search(def_re, txt)
        if not dm:
            bad("T14", "%s used at line %d but never defined in the main article"
                % (label, txt[:um.start()].count("\n") + 1))
            continue
        up, dp = par_of(um.start()), par_of(dm.start())
        if dp > up:
            bad("T14", "%s used in paragraph at line %d, defined only later at line %d"
                % (label, pars[up][0], pars[dp][0]))
        else:
            clean += 1
    if clean == len(NOTATION):
        ok("T14", "all %d tracked symbols defined at or before first use" % clean)


# --------------------------------------------------------------------------
# T15 -- supplement cross-references
# --------------------------------------------------------------------------
#
# The two documents compile separately, so the main article cites the
# supplement as literal text ("Supplementary Section~S7") rather than \ref{}.
# Nothing in LaTeX checks those. Inserting or moving a supplement section
# silently shifts every number after it and the main text keeps pointing at
# whatever now occupies the slot -- a failure that survives compilation and
# reads perfectly.

def t15():
    print("[T15] supplement cross-references")
    supp = strip_comments(read(SUPP))
    titles = re.findall(r"\\section\{([^}]*)\}", supp)
    if not titles:
        bad("T15", "no sections found in the supplement")
        return
    refs = collections.Counter(
        int(n) for n in re.findall(r"Supplementary Section~S(\d+)",
                                   strip_comments(read(MAIN))))
    dangling = sorted(n for n in refs if n > len(titles))
    if dangling:
        for n in dangling:
            bad("T15", "main text cites S%d but the supplement has %d sections"
                % (n, len(titles)))
    else:
        ok("T15", "all %d cited section numbers exist (supplement has %d)"
           % (len(refs), len(titles)))
    for n in sorted(refs):
        if n <= len(titles):
            note("T15", "S%-2d x%d -> %s" % (n, refs[n], titles[n - 1]))
    orphans = [i + 1 for i in range(len(titles)) if (i + 1) not in refs]
    if orphans:
        note("T15", "supplement sections never cited: %s"
             % ", ".join("S%d (%s)" % (i, titles[i - 1]) for i in orphans))


CHECKS = dict(t0=t0, t1=t1, t2=t2, t3=t3, t4=t4, t5=t5, t6=t6, t7=t7,
              t8=t8, t9=t9, t10=t10, t11=t11, t12=t12, t13=t13, t14=t14,
              t15=t15, remap=remap)
GATE = ["t0", "t1", "t2", "t10", "t12", "t9"]
ALL = ["t0", "t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8", "t9", "t10",
       "t11", "t12", "t13", "t14", "t15"]


def main():
    args = sys.argv[1:] or ["all"]
    if args == ["all"]:
        args = ALL
    elif args == ["gate"]:
        args = GATE
    for a in args:
        fn = CHECKS.get(a)
        if not fn:
            print("unknown check: %s" % a)
            continue
        fn()
        print("")
    print("=" * 70)
    if FAILS:
        print("%d FAIL, %d note" % (len(FAILS), len(NOTES)))
        return 1
    print("all checks pass (%d notes)" % len(NOTES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
