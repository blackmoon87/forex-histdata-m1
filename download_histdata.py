#!/usr/bin/env python3
"""
Download all ASCII 1-minute bar zip files from histdata.com.
"""

import concurrent.futures
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------
OUTPUT_DIR = Path("histdata_zips")          # change if you like
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "http://www.histdata.com/download-free-forex-data/"
REQUEST_TIMEOUT = 30
SCRAPE_WORKERS = 10
DOWNLOAD_WORKERS = 10


# ---------------------------------------------------------------------------
# STEP 1 — Scrape main page for pairs & start years
# ---------------------------------------------------------------------------
def fetch_main_page():
    url = f"{BASE_URL}?/ascii/1-minute-bar-quotes"
    resp = requests.get(url, timeout=REQUEST_TIMEOUT)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    pairs = []
    for td in soup.find_all("td"):
        a = td.find("a", href=True)
        if a and "/ascii/1-minute-bar-quotes/" in a.get("href", ""):
            pair = a["href"].rstrip("/").split("/")[-1]
            text = td.get_text(strip=True)
            m = re.search(r"\((\d{4})/[A-Za-z]+\)", text)
            if m:
                pairs.append((pair, int(m.group(1))))
    return pairs


# ---------------------------------------------------------------------------
# STEP 2 — Generate every year/month URL for a pair
# ---------------------------------------------------------------------------
def generate_urls(pair, start_year):
    urls = []
    # Yearly archives: start_year … 2025
    for year in range(start_year, 2026):
        urls.append(f"{BASE_URL}?/ascii/1-minute-bar-quotes/{pair.lower()}/{year}")
    # Monthly archives for 2026 (up to May to be safe)
    for month in range(1, 6):
        urls.append(f"{BASE_URL}?/ascii/1-minute-bar-quotes/{pair.lower()}/2026/{month}")
    return urls


# ---------------------------------------------------------------------------
# STEP 3 — Scrape the hidden tk token from each download page
# ---------------------------------------------------------------------------
def scrape_record(url):
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        form = soup.find("form", id="file_down")
        if not form:
            return None

        record = {"url": url}
        for inp in form.find_all("input", type="hidden"):
            record[inp.get("id")] = inp.get("value")

        return record if record.get("tk") else None
    except Exception:
        return None


# ---------------------------------------------------------------------------
# STEP 4 — POST to get.php and save the zip
# ---------------------------------------------------------------------------
def download_zip(record):
    url = record["url"]
    try:
        headers = {
            "Host": "www.histdata.com",
            "Connection": "keep-alive",
            "Origin": "http://www.histdata.com",
            "Upgrade-Insecure-Requests": "1",
            "DNT": "1",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer": url,
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
        }

        post_resp = requests.post(
            "http://www.histdata.com/get.php",
            data={
                "tk": record["tk"],
                "date": record["date"],
                "datemonth": record["datemonth"],
                "platform": record["platform"],
                "timeframe": record["timeframe"],
                "fxpair": record["fxpair"],
            },
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        post_resp.raise_for_status()

        # Derive filename from Content-Disposition
        cd = post_resp.headers.get("Content-Disposition", "")
        m = re.search(r'filename=([^;]+)', cd)
        filename = m.group(1).strip().strip('"') if m else \
            f"HISTDATA_COM_ASCII_{record['fxpair']}_M1_{record['datemonth']}.zip"

        filepath = OUTPUT_DIR / filename
        filepath.write_bytes(post_resp.content)
        return {"status": "ok", "file": str(filepath), "size": len(post_resp.content)}
    except Exception as e:
        return {"status": "error", "url": url, "error": str(e)}


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    print("Step 1: Fetching pairs from main page...")
    pairs = fetch_main_page()
    print(f"Found {len(pairs)} pairs.")
    (OUTPUT_DIR / "_pairs_metadata.json").write_text(json.dumps(pairs, indent=2))

    print("Step 2: Generating all URLs...")
    all_urls = []
    for pair, start_year in pairs:
        all_urls.extend(generate_urls(pair, start_year))
    print(f"Total URLs to scrape: {len(all_urls)}")

    print("Step 3: Scraping tokens (this may take a few minutes)...")
    valid_records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=SCRAPE_WORKERS) as ex:
        future_to_url = {ex.submit(scrape_record, u): u for u in all_urls}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            result = future.result()
            if result:
                valid_records.append(result)
            if (i + 1) % 100 == 0:
                print(f"  Scraped {i+1}/{len(all_urls)} pages, {len(valid_records)} valid so far...")
    print(f"Scraping complete: {len(valid_records)} valid download records.")

    (OUTPUT_DIR / "_download_records.json").write_text(json.dumps(valid_records, indent=2))

    print("Step 4: Downloading zip files...")
    downloaded = failed = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=DOWNLOAD_WORKERS) as ex:
        future_to_rec = {ex.submit(download_zip, r): r for r in valid_records}
        for i, future in enumerate(concurrent.futures.as_completed(future_to_rec)):
            result = future.result()
            if result["status"] == "ok":
                downloaded += 1
            else:
                failed += 1
                print(f"  FAIL: {result['url']} -> {result['error']}")
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(valid_records)} processed ({downloaded} ok, {failed} fail)")

    print(f"\nDone! Downloaded {downloaded} files, {failed} failures.")
    print(f"Files saved to: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
