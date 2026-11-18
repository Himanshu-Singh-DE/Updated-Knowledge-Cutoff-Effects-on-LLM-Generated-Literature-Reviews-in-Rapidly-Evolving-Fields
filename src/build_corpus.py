"""Build the dated document corpus from the official ACL Anthology XML metadata.

Input : a checkout of github.com/acl-org/acl-anthology (data/xml)
Output: data/documents.csv with columns
        paper_id,title,abstract,publication_date,date_precision,venue,year
Rules (frozen before any retrieval run, see configs/experiment.json):
  * keep papers whose volume year is in [min_year, max_year]
  * keep only papers with a non-empty abstract (BM25 indexes title+abstract)
  * drop frontmatter (no <paper> element) and papers whose title is missing
  * publication_date = first day of the volume month; if the month is missing
    or unparseable the date is set to YYYY-07-01 and date_precision='year'
"""
import argparse, csv, glob, os, re, sys
import xml.etree.ElementTree as ET

MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august",
     "september", "october", "november", "december"], start=1)}


def text_of(el):
    return " ".join("".join(el.itertext()).split()) if el is not None else ""


def parse_month(s):
    s = (s or "").lower()
    for name, num in MONTHS.items():
        if name in s or re.search(r"\b" + name[:3] + r"\b", s):
            return num
    m = re.match(r"^\s*(\d{1,2})\s*$", s)
    if m and 1 <= int(m.group(1)) <= 12:
        return int(m.group(1))
    return None


def paper_id(coll, vol, pid):
    if re.fullmatch(r"[A-Z]\d\d", coll):          # old-style e.g. P18-1001
        return f"{coll}-{vol}{int(pid):03d}"
    return f"{coll}-{vol}.{pid}"                  # new-style e.g. 2023.acl-long.1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--xml_dir", required=True)
    ap.add_argument("--out", default="data/documents.csv")
    ap.add_argument("--min_year", type=int, default=2018)
    ap.add_argument("--max_year", type=int, default=2025)
    a = ap.parse_args()
    rows, stats = [], {"files": 0, "papers_seen": 0, "no_abstract": 0, "year_only": 0}
    for f in sorted(glob.glob(os.path.join(a.xml_dir, "*.xml"))):
        stats["files"] += 1
        root = ET.parse(f).getroot()
        coll = root.get("id")
        for vol in root.findall("volume"):
            meta = vol.find("meta")
            try:
                year = int(text_of(meta.find("year")))
            except Exception:
                continue
            if not (a.min_year <= year <= a.max_year):
                continue
            month = parse_month(text_of(meta.find("month")))
            venue = ",".join(text_of(v) for v in meta.findall("venue"))
            for p in vol.findall("paper"):
                stats["papers_seen"] += 1
                title, abstract = text_of(p.find("title")), text_of(p.find("abstract"))
                if not title:
                    continue
                if not abstract:
                    stats["no_abstract"] += 1
                    continue
                if month is None:
                    stats["year_only"] += 1
                rows.append({
                    "paper_id": paper_id(coll, vol.get("id"), p.get("id")),
                    "title": title, "abstract": abstract,
                    "publication_date": f"{year:04d}-{(month or 7):02d}-01",
                    "date_precision": "month" if month else "year",
                    "venue": venue, "year": year})
    ids = [r["paper_id"] for r in rows]
    assert len(ids) == len(set(ids)), "duplicate paper_id"
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)
    stats["kept"] = len(rows)
    print(stats)


if __name__ == "__main__":
    main()
