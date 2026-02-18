"""
Signal Radar - Scheduled runs
Runs the full pipeline (scrape → classify → score → export), then sleeps for
SCHEDULE_INTERVAL_HOURS. Run in the background so data is updated every 6–12 hours.

Usage:
  python3 run_scheduled.py              # use config.SCHEDULE_INTERVAL_HOURS (default 6)
  python3 run_scheduled.py --hours 12  # refresh every 12 hours
  python3 run_scheduled.py --once       # run once (no loop; same as main.py)
"""

import argparse
import time

import config
from main import run_pipeline


def main():
    parser = argparse.ArgumentParser(description="Run Signal Radar on a schedule (e.g. every 6–12 hours)")
    parser.add_argument("--hours", type=float, default=None, help="Hours between runs (default: config.SCHEDULE_INTERVAL_HOURS)")
    parser.add_argument("--once", action="store_true", help="Run once and exit (no schedule)")
    args = parser.parse_args()

    interval_hours = args.hours if args.hours is not None else config.SCHEDULE_INTERVAL_HOURS
    interval_sec = max(1, interval_hours * 3600)

    run_count = 0
    while True:
        run_count += 1
        print(f"\n--- Run #{run_count} at {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
        try:
            run_pipeline(scrape=True)
        except Exception as e:
            print("Pipeline error:", e)
        if args.once:
            break
        print(f"Sleeping {interval_hours} hour(s) until next run...")
        time.sleep(interval_sec)


if __name__ == "__main__":
    main()
