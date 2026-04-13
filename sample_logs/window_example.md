# Window Filter Example

The `window` sub-command lets you narrow drift analysis to a specific time
range so you can focus on, e.g., a deployment window or an incident period.

## Basic usage

```bash
# Report drift only for entries between two timestamps
python -m sched_drift window sample_logs/example.log \
    --start 2024-01-10T08:00:00 \
    --end   2024-01-10T18:00:00
```

## Open-ended windows

```bash
# Everything from a certain point onward
python -m sched_drift window sample_logs/example.log \
    --start 2024-03-01T00:00:00

# Everything up to a certain point
python -m sched_drift window sample_logs/example.log \
    --end 2024-03-31T23:59:59
```

## Combined with server filter

```bash
python -m sched_drift window sample_logs/example.log \
    --start 2024-01-10T08:00:00 \
    --end   2024-01-10T18:00:00 \
    --server web-01
```

## Sample output

```
Window [2024-01-10T08:00:00+00:00 → 2024-01-10T18:00:00+00:00]: 2 job(s), 5 entry(ies)

server    job          entries  avg_drift  max_drift  late  early
--------  -----------  -------  ---------  ---------  ----  -----
web-01    backup.sh          3      +12.3s     +28.0s     3      0
web-02    cleanup.sh         2       -4.5s      -9.0s     0      2
```

## Notes

- Timestamps are parsed as ISO-8601. If no timezone is given, UTC is assumed.
- The filter is applied to `actual_time` recorded in the log.
- Entries outside the window are silently dropped before building the report.
