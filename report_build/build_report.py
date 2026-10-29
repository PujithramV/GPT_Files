"""Build the complete minor-project report (.docx and .pdf).

Usage:  python3 build_report.py [output_dir]
Page numbers in the Table of Contents / List of Tables / List of Figures are resolved by
building the document, converting it to PDF, locating every heading and caption, and
rebuilding until the numbers are stable.
"""
import json
import os
import re
import subprocess
import sys
import warnings

warnings.filterwarnings("ignore")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import pymupdf  # noqa: E402

from build_lib import Report  # noqa: E402
from refs import REFS  # noqa: E402
import content_a as A  # noqa: E402
import content_b as B  # noqa: E402
import content_c as C  # noqa: E402
import content_d as D  # noqa: E402

BASENAME = "Minor_Project_Report_Vemana_Venkata_Pujithram_230907016"


def build(pages, reg, out):
    R = Report()
    R.refdb = REFS
    A.title_page(R)
    A.acknowledgments(R)
    A.abstract(R)
    A.contents(R, pages)
    A.list_of_tables(R, reg, pages)
    A.list_of_figures(R, reg, pages)
    A.abbreviations(R)
    A.chapter1(R)
    A.chapter2(R)
    B.chapter3a(R)
    C.chapter3b(R)
    D.chapter4(R)
    D.chapter5(R)
    D.chapter6(R)
    missing = D.back_matter(R)
    D.project_details(R)
    R.save(out)
    return R, missing


def to_pdf(docx, outdir):
    subprocess.run(["soffice", "--headless", "--convert-to", "pdf", "--outdir", outdir, docx],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=600)
    return os.path.splitext(docx)[0] + ".pdf"


def roman(n):
    vals = [(10, "x"), (9, "ix"), (5, "v"), (4, "iv"), (1, "i")]
    s = ""
    for v, r in vals:
        while n >= v:
            s += r
            n -= v
    return s


def norm(t):
    return re.sub(r"\s+", " ", t).strip()


def strip_tags(t):
    t = re.sub(r"</?(?:b|i|sub|sup|c)>", "", t)
    return re.sub(r"\[@[^\]]*\]", "", t)


def resolve_pages(pdf, reg):
    doc = pymupdf.open(pdf)
    texts = [norm(p.get_text()) for p in doc]
    n = len(texts)

    def find(s, start=0):
        for i in range(start, n):
            if s in texts[i]:
                return i
        return None

    ch1 = find("CHAPTER 1 INTRODUCTION")
    pages = {}

    def disp(idx):
        if idx is None:
            return "–"
        return roman(idx) if idx < ch1 else str(idx - ch1 + 1)

    heads = {"Acknowledgments": "ACKNOWLEDGMENTS", "Abstract": "ABSTRACT",
             "List of tables": "LIST OF TABLES", "List of figures": "LIST OF FIGURES",
             "List of abbreviations": "LIST OF ABBREVIATIONS", "Visible outcome": "VISIBLE OUTCOME",
             "References": "REFERENCES",
             "Minor specialization project details": "MINOR SPECIALIZATION PROJECT DETAILS"}
    for k, h in heads.items():
        pages[k] = disp(find(h))
    for c in range(1, 7):
        pages[f"CHAPTER {c}"] = disp(find(f"CHAPTER {c} ", ch1))
    for num, title in reg["tables"]:
        pages["T:" + num] = disp(find(f"Table {num} " + norm(strip_tags(title))[:25], ch1))
    for num, title in reg["figures"]:
        pages["F:" + num] = disp(find(f"Figure {num} " + norm(strip_tags(title))[:25], ch1))
    return pages, n, ch1


def main():
    outdir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(HERE)
    os.makedirs(outdir, exist_ok=True)
    work = os.path.join(HERE, "_work")
    os.makedirs(work, exist_ok=True)
    tmp_docx = os.path.join(work, BASENAME + ".docx")
    pages, reg = {}, {"tables": [], "figures": []}
    for it in range(6):
        R, missing = build(pages, reg, tmp_docx)
        new_reg = {"tables": R.tables, "figures": R.figures}
        pdf = to_pdf(tmp_docx, work)
        new_pages, n, ch1 = resolve_pages(pdf, new_reg)
        print(f"pass {it}: {n} pages, front matter {ch1} pages, tables {len(R.tables)}, "
              f"figures {len(R.figures)}, uncited refs {missing}")
        stable = (new_pages == pages and [list(x) for x in new_reg["tables"]] == [list(x) for x in reg["tables"]]
                  and [list(x) for x in new_reg["figures"]] == [list(x) for x in reg["figures"]])
        pages, reg = new_pages, {"tables": [tuple(x) for x in new_reg["tables"]],
                                 "figures": [tuple(x) for x in new_reg["figures"]]}
        if stable:
            break
    final_docx = os.path.join(outdir, BASENAME + ".docx")
    R, _ = build(pages, reg, final_docx)
    pdf = to_pdf(final_docx, outdir)
    chk, n, ch1 = resolve_pages(pdf, {"tables": R.tables, "figures": R.figures})
    print("final pages:", n, "| page-number map stable:", chk == pages)
    json.dump({"pages": pages}, open(os.path.join(work, "pages.json"), "w"), indent=1)
    print(final_docx)
    print(pdf)


if __name__ == "__main__":
    main()
