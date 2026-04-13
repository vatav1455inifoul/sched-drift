# Snapshot Feature — Usage Examples

The `snapshot` subcommand lets you capture the current drift state and later
compare it against a new observation to see whether things have improved or
worsened.

## Capture a snapshot

```bash
python -m sched_drift snapshot capture sample_logs/example.log --out baseline.json
```

This reads the log file(s), builds drift reports, and writes a timestamped
JSON snapshot to `baseline.json`.

## Capture a second snapshot later

```bash
python -m sched_drift snapshot capture sample_logs/example.log --out current.json
```

## Diff two snapshots

```bash
python -m sched_drift snapshot diff baseline.json current.json
```

Sample output:

```
Snapshot diff:

  [web1] backup: +10.0s → +20.0s  (↑ +10.0s, worsened)
  [web1] cleanup: +30.0s → +5.0s  (↓ -25.0s, improved)
  [db1]  nightly: +2.0s → +2.3s   (= +0.3s, unchanged)
```

## JSON snapshot format

```json
{
  "captured_at": "2024-06-01T12:00:00+00:00",
  "entries": [
    {
      "server": "web1",
      "job": "backup",
      "avg_drift": 10.0,
      "max_drift": 25.0,
      "sample_count": 8
    }
  ]
}
```
