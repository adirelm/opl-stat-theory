#!/usr/bin/env python3
"""
Download the OpenPowerlifting bulk CSV into data/openpowerlifting.csv.

Source: https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip
License: the competition DATA is released into the public domain (CC0-style waiver).
NOTE: the 'latest' archive updates ~weekly. Record the download date below for
exact reproducibility of the reported numbers.
"""
import io, urllib.request, zipfile
from pathlib import Path

URL = "https://openpowerlifting.gitlab.io/opl-csv/files/openpowerlifting-latest.zip"
ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = DATA / "openpowerlifting.csv"


def main():
    DATA.mkdir(exist_ok=True)
    print(f"Downloading {URL} ...")
    raw = urllib.request.urlopen(URL).read()
    print(f"  {len(raw)/1e6:.0f} MB downloaded; extracting CSV ...")
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        name = next(n for n in z.namelist() if n.endswith(".csv"))
        with z.open(name) as f, open(OUT, "wb") as g:
            g.write(f.read())
    print(f"  wrote {OUT} ({OUT.stat().st_size/1e6:.0f} MB)")


if __name__ == "__main__":
    main()
