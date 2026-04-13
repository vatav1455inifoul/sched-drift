# sched-drift

> A CLI tool that detects and reports cron job drift across multiple servers by comparing scheduled vs actual execution times.

---

## Installation

```bash
pip install sched-drift
```

Or install from source:

```bash
git clone https://github.com/youruser/sched-drift.git && cd sched-drift && pip install .
```

---

## Usage

Point `sched-drift` at your servers and let it compare cron schedules against real execution logs:

```bash
sched-drift analyze --hosts web1,web2,web3 --log-path /var/log/cron.log
```

Generate a drift report in JSON format:

```bash
sched-drift report --hosts web1,web2 --output report.json --format json
```

Check a single server interactively:

```bash
sched-drift check --host web1 --job "backup.sh" --threshold 60s
```

**Example output:**

```
Host       Job           Scheduled    Actual       Drift
---------- ------------- ------------ ------------ ------
web1       backup.sh     02:00:00     02:01:43     +103s  ⚠
web2       backup.sh     02:00:00     02:00:04     +4s    ✓
web3       cleanup.sh    03:00:00     03:04:21     +261s  ✗
```

---

## Options

| Flag | Description |
|------|-------------|
| `--hosts` | Comma-separated list of target servers |
| `--log-path` | Path to cron log file on remote hosts |
| `--threshold` | Acceptable drift window (default: `30s`) |
| `--format` | Output format: `table`, `json`, `csv` |

---

## License

[MIT](LICENSE)