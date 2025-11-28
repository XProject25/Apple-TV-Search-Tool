# Apple TV Search Tool

Unofficial command-line tool to search Apple TV content (Movies and TV Shows) using public Apple web endpoints.

Developed by **X Project**  
Original idea and structure inspired by **@sp4rk.y**

---

## Overview

This tool provides a simple CLI interface to search Apple TV for:

- Movies  
- TV shows / series  
- (Optionally) people such as actors or directors

Results are scored and sorted by relevance and can be printed in a human-readable format or as JSON for automation.

---

## Features

- Search by title against Apple TV catalog
- Support for:
  - Storefront IDs (for example: `143441` for US)
  - 2-letter region codes (for example: `US`, `GB`, `DE`)
- Optional result filters:
  - `--type movie`
  - `--type show` / `--type series`
- Optional result limit: `--max-results`
- Optional inclusion of people (actors, directors, etc.): `--include-people`
- JSON output for scripting and integration: `--json`
- Configurable locale (for example: `en-US`, `de-DE`)
- Simple, transparent scoring algorithm:
  - Exact title match
  - Prefix match
  - Partial match
  - Position in list

---

## Requirements

- Python 3.8 or newer
- `requests` library

Install the dependency:

```bash
pip install requests
```

---

## Installation

1. Save the script as:

   ```text
   atv_search.py
   ```

2. (Optional) Make the script executable:

   ```bash
   chmod +x atv_search.py
   ```

3. Run it either directly:

   ```bash
   ./atv_search.py "Foundation"
   ```

   or via Python:

   ```bash
   python atv_search.py "Foundation"
   ```

---

## Usage

Basic syntax:

```bash
python atv_search.py "SEARCH TERM" [options]
```

### Common examples

Search in default US storefront:

```bash
python atv_search.py "Ted Lasso"
```

Search using a region code (for example Canada):

```bash
python atv_search.py "Severance" -sf CA
```

Search using a storefront ID (for example United Kingdom = 143444):

```bash
python atv_search.py "Severance" -sf 143444
```

Limit the number of results:

```bash
python atv_search.py "See" --max-results 5
```

Filter only shows:

```bash
python atv_search.py "See" --type show
```

Filter only movies:

```bash
python atv_search.py "Greyhound" --type movie
```

Output JSON for automation:

```bash
python atv_search.py "Foundation" --json
```

Use a different locale (for example German):

```bash
python atv_search.py "See" -sf DE --locale de-DE
```

Include people (actors, directors, etc.) in results:

```bash
python atv_search.py "Brad Pitt" --include-people
```

Show version information:

```bash
python atv_search.py --version
```

---

## Command-line Options

| Option                | Description                                                                                     |
|-----------------------|-------------------------------------------------------------------------------------------------|
| `query`               | Search term (required; one or more words).                                                     |
| `-sf, --storefront`   | Storefront ID (for example `143441`) or region code (for example `US`, `GB`, `DE`, `CA`).      |
| `-l, --locale`        | Locale string, default `en-US`.                                                                |
| `--max-results`       | Maximum number of results to return (integer).                                                 |
| `--type`              | Filter by type: `movie`, `show`, or `series`.                                                  |
| `--include-people`    | Include people/person results (actors, directors, etc.).                                       |
| `--json`              | Output raw JSON instead of formatted text.                                                     |
| `--timeout`           | HTTP timeout in seconds (default: `10`).                                                       |
| `-v, --version`       | Show version information and exit.                                                             |

---

## Output

### Human-readable mode (default)

Example output:

```text
Storefront ID: 143441
Locale:       en-US
Query:        Ted Lasso
Developed by X Project

Found 3 result(s):

1. Ted Lasso
   Type:   TV Show (series)
   ID:     1234567890
   Score:  1150
   URL:    https://tv.apple.com/us/show/ted-lasso/...
```

### JSON mode (`--json`)

```json
[
  {
    "score": 1150,
    "id": "1234567890",
    "title": "Ted Lasso",
    "type": "TV Show",
    "raw_type": "series",
    "url": "https://tv.apple.com/us/show/ted-lasso/..."
  }
]
```

JSON mode is designed for scripting and can be combined with tools such as `jq`:

```bash
python atv_search.py "Ted Lasso" --json | jq '.[0].url'
```

---

## Storefronts and Regions

The script supports both storefront IDs and 2-letter region codes. Some common storefronts:

- United States: `US` (ID `143441`)
- United Kingdom: `GB` (ID `143444`)
- Canada: `CA` (ID `143455`)
- Australia: `AU` (ID `143460`)
- France: `FR` (ID `143442`)
- Germany: `DE` (ID `143443`)
- Japan: `JP` (ID `143462`)
- India: `IN` (ID `143467`)

You can pass either the storefront ID or the region code to `-sf` / `--storefront`.

If you provide a region code, the script will attempt to resolve the matching storefront ID automatically.  
If resolution fails, it falls back to the US storefront (`143441`).

---

## Implementation Notes

- The tool uses Apple TV web endpoints that are reverse-engineered from the browser network traffic.
- Parameters such as `utscf`, `utsk`, `v`, and `caller` are based on the current implementation of Apple TV web.
- Apple may change these endpoints or parameters at any time, which can break this tool.
- All requests are made without authentication and are limited to public catalog information.

---

## Disclaimer

- This project is not affiliated with, endorsed by, or supported by Apple Inc.
- It is provided for educational and personal use only.
- Use it at your own risk. The author and X Project assume no responsibility for any issues arising from its use.

---

## Credits

- Concept and initial structure: **@sp4rk.y**  
- Enhancements, CLI options, scoring and documentation: **X Project**

Developed by **X Project**
