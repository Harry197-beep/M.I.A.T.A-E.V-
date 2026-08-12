from datetime import datetime
from zoneinfo import ZoneInfo


def get_current_time(timezone_str="Asia/Jakarta"):
    """Get the current date and time in a given timezone (default WIB)."""
    try:
        tz = ZoneInfo(timezone_str)
    except Exception:
        return f"Unknown timezone: {timezone_str}"

    now = datetime.now(tz)
    return now.strftime(f"%A, %B %d, %Y at %H:%M ({timezone_str})")


if __name__ == "__main__":
    print(get_current_time())
