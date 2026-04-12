# pgdrift

A lightweight CLI tool for detecting and summarizing schema drift between PostgreSQL environments.

---

## Installation

```bash
pip install pgdrift
```

Or install from source:

```bash
git clone https://github.com/yourname/pgdrift.git && cd pgdrift && pip install .
```

---

## Usage

Compare the schema of two PostgreSQL databases and get a clear summary of any drift:

```bash
pgdrift compare \
  --source "postgresql://user:pass@localhost:5432/production" \
  --target "postgresql://user:pass@staging-host:5432/staging"
```

**Example output:**

```
[+] tables added in target:    user_sessions
[-] tables missing in target:  legacy_tokens
[~] columns changed:           orders.status (varchar(50) → varchar(100))

3 differences detected.
```

### Options

| Flag | Description |
|------|-------------|
| `--source` | Connection string for the source database |
| `--target` | Connection string for the target database |
| `--format` | Output format: `text` (default), `json`, or `markdown` |
| `--ignore-tables` | Comma-separated list of tables to exclude |

---

## Requirements

- Python 3.8+
- PostgreSQL 12+

---

## License

MIT © 2024 [yourname](https://github.com/yourname)