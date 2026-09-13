"""Refuse any internal industrial station code in a published table or figure.

Company site codes such as ``01.E4`` must never leave the analysis pipeline;
publication figures and tables carry the ``S_n`` aliases instead.

What this check actually establishes, no more:

1. Every generated CSV/Markdown table is scanned as text for a site-code pattern.
2. The industrial station table, which is the ONLY input the industrial figure
   draws its labels from, must contain nothing but ``S_<n>`` labels in its
   station column. This is the real guarantee for rendered figure text, because
   the figure code reads labels from that table and nowhere else.
3. Figure files are additionally scanned as raw bytes. That is a weak check: PNG
   text is compressed, so a hit is meaningful but a miss proves little. It is
   kept as belt-and-braces, not as the guarantee.

The detector is verified against a positive control before every scan so an
empty result cannot pass by accident.
"""

from __future__ import annotations

from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "reports" / "horizon_robustness_results"
SCANNED = ("tables", "figures")

# Internal codes look like 01.E4 / 01.30 / 01.GED / 01.Z8.
SITE_CODE = re.compile(r"\b0\d\.[A-Z0-9]{1,4}\b")


def scan_text(text):
    return sorted(set(SITE_CODE.findall(text)))


def scan_file(path):
    if path.suffix.lower() in (".png", ".pdf", ".svg"):
        # Rendered text is embedded; read bytes and look for the pattern anyway.
        data = path.read_bytes().decode("latin-1", errors="ignore")
        return scan_text(data)
    return scan_text(path.read_text(encoding="utf-8", errors="replace"))


def main():
    # Positive control: the detector must actually fire on a known site code.
    control = scan_text("station 01.E4 and 01.GED appear here")
    if control != ["01.E4", "01.GED"]:
        print(f"DETECTOR BROKEN: positive control returned {control}", file=sys.stderr)
        return 2

    findings, scanned = [], 0
    # (2) The figure label source: only alias labels may appear.
    table = RESULTS / "tables" / "station_profile_industrial.csv"
    if table.exists():
        import csv
        bad = sorted({r["station"] for r in csv.DictReader(table.open(encoding="utf-8"))
                      if not re.fullmatch(r"S_\d+", r["station"] or "")})
        if bad:
            print(f"NON-ALIAS STATION LABEL in industrial table: {bad}", file=sys.stderr)
            return 1
        scanned += 1
    for folder in SCANNED:
        base = RESULTS / folder
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file():
                continue
            scanned += 1
            hits = scan_file(path)
            if hits:
                findings.append((path.relative_to(RESULTS).as_posix(), hits))

    if findings:
        for name, hits in findings:
            print(f"SITE CODE LEAKED in {name}: {', '.join(hits)}", file=sys.stderr)
        return 1
    if scanned == 0:
        print("NOTHING SCANNED: no tables or figures exist yet", file=sys.stderr)
        return 1
    print(f"NO SITE CODE LEAKED ({scanned} published file(s) scanned; industrial figure labels are "
          f"alias-only; detector positive control passed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
