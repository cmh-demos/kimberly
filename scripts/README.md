Append log helper -----------------

This simple helper `scripts/append_log.py` writes high-precision (microsecond)
timestamps to `misc/copilot_tracking.json`, computes `processing_time_microseconds`,
validates the entry against `misc/copilot_tracking.schema.json`, and verifies file hash
before writing (pre-append check).

Example usage:

```bash
python3 scripts/append_log.py --note "fix schema" --tokens-estimate 10 --tokens-used 2 --tool-calls 1 --files-accessed 1
```

Use `--start` and `--end` to supply explicit ISO timestamps (with fractional seconds),
or let the script record both as "now".

Installing jsonschema (optional):

```bash
pip install jsonschema
```

If jsonschema isn't installed, validation will be skipped but the script will still
attempt a safe append.
