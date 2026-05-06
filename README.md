# forex-histdata-m1

> **Complete HistData.com ASCII 1-minute bar dataset — all forex pairs, auto-downloaded.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Data Source](https://img.shields.io/badge/source-histdata.com-green)](http://www.histdata.com)

## 🌐 Project Page
[**View Live Page →**](https://blackmoon87.github.io/forex-histdata-m1)

## 📦 What's Inside

| Item | Description |
|---|---|
| `download_histdata.py` | Scrapes & downloads all zip files from HistData.com |
| `histdata_zips/` | Downloaded zip files (OHLCV, ASCII, M1) |
| `index.html` | Project landing page |

## 🚀 Quick Start

```bash
git clone https://github.com/blackmoon87/forex-histdata-m1.git
cd forex-histdata-m1
pip install requests beautifulsoup4
python download_histdata.py
```

Files are saved to `histdata_zips/`. Each zip contains a CSV with columns:
```
DateTime, Open, High, Low, Close, Volume
```

## 📊 Coverage

- **80+ pairs** — majors, minors, exotics, metals, crypto
- **20+ years** of history (pair-dependent start year)
- **M1 timeframe** — 1-minute OHLCV bars
- **ASCII format** — universally compatible

## ☕ Support

If this saved you time, consider buying me a coffee:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-ffdd00?style=for-the-badge&logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/black.moon)

## 📜 License

MIT — data copyright belongs to [HistData.com](http://www.histdata.com).
