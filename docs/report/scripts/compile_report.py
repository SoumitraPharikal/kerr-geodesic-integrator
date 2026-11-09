"""Compile the LaTeX technical report to Kerr_Geodesic_Integrator_Report.pdf.

Portable across Windows, Linux, and macOS:
- Dynamically discovers pdflatex and bibtex on PATH.
- Falls back to common platform installation paths if not on standard PATH.
- Runs:
    1. pdflatex main.tex
    2. bibtex main
    3. pdflatex main.tex
    4. pdflatex main.tex
    5. Copies main.pdf to Kerr_Geodesic_Integrator_Report.pdf
- Inspects final PDF with pypdf to verify page count and integrity.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import Optional

try:
    import pypdf
except ImportError:
    pypdf = None

REPORT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def find_executable(name: str) -> str:
    """Find executable dynamically on PATH or via common platform fallbacks."""
    # 1. Check system PATH
    found = shutil.which(name)
    if found:
        return found

    # 2. Platform fallbacks
    fallbacks = []
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        fallbacks.extend([
            os.path.join(local_app_data, "Programs", "MiKTeX", "miktex", "bin", "x64", f"{name}.exe"),
            rf"C:\Program Files\MiKTeX\miktex\bin\x64\{name}.exe",
            rf"C:\texlive\2025\bin\windows\{name}.exe",
            rf"C:\texlive\2024\bin\windows\{name}.exe",
        ])
    else:
        fallbacks.extend([
            f"/usr/bin/{name}",
            f"/usr/local/bin/{name}",
            f"/Library/TeX/texbin/{name}",
        ])

    for p in fallbacks:
        if os.path.isfile(p) and os.access(p, os.X_OK):
            return p

    raise FileNotFoundError(
        f"Could not locate '{name}' on PATH or in standard installation directories. "
        f"Please ensure TeX Live or MiKTeX is installed."
    )


def run_cmd(cmd: list[str], desc: str) -> None:
    print(f"--> {desc}...")
    res = subprocess.run(cmd, cwd=REPORT_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if res.returncode != 0:
        print(f"Error in {desc} (code {res.returncode}):")
        print(res.stdout[-1500:])
        print(res.stderr[-1500:])
        raise RuntimeError(f"{desc} failed with exit code {res.returncode}")
    print("    Completed successfully.")


def main():
    pdflatex_path = find_executable("pdflatex")
    bibtex_path = find_executable("bibtex")

    print(f"Working directory: {REPORT_DIR}")
    print(f"Using pdflatex:    {pdflatex_path}")
    print(f"Using bibtex:      {bibtex_path}")

    # Pass 1: pdflatex
    run_cmd([pdflatex_path, "-interaction=nonstopmode", "main.tex"], "Pass 1: pdflatex")

    # Pass 2: bibtex
    run_cmd([bibtex_path, "main"], "Pass 2: bibtex")

    # Pass 3: pdflatex
    run_cmd([pdflatex_path, "-interaction=nonstopmode", "main.tex"], "Pass 3: pdflatex")

    # Pass 4: pdflatex (resolves cross references and citations)
    run_cmd([pdflatex_path, "-interaction=nonstopmode", "main.tex"], "Pass 4: pdflatex")

    main_pdf = os.path.join(REPORT_DIR, "main.pdf")
    dest_pdf = os.path.join(REPORT_DIR, "Kerr_Geodesic_Integrator_Report.pdf")

    shutil.copyfile(main_pdf, dest_pdf)
    print(f"Copied final PDF to: {dest_pdf}")

    # Remove duplicate main.pdf to ensure single canonical PDF deliverable
    if os.path.isfile(main_pdf) and os.path.abspath(main_pdf) != os.path.abspath(dest_pdf):
        os.remove(main_pdf)
        print("Removed duplicate intermediate main.pdf.")

    # Clean up stale auxiliary files from legacy naming
    for ext in [".aux", ".bbl", ".blg", ".log", ".out", ".toc"]:
        stale_file = os.path.join(REPORT_DIR, f"Kerr_Geodesic_Integrator_Report{ext}")
        if os.path.isfile(stale_file):
            os.remove(stale_file)

    if pypdf is not None:
        reader = pypdf.PdfReader(dest_pdf)
        num_pages = len(reader.pages)
        file_size_kb = os.path.getsize(dest_pdf) / 1024.0

        print("=" * 60)
        print("REPORT VERIFICATION SUMMARY:")
        print(f"  Final PDF Path:   {dest_pdf}")
        print(f"  Exact Page Count: {num_pages} pages")
        print(f"  File Size:        {file_size_kb:.1f} KB")
        print("=" * 60)


if __name__ == "__main__":
    main()
