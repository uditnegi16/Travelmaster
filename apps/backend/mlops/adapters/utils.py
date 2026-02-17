def parse_duration_to_minutes(duration_str: str) -> int:
    if not duration_str:
        return 0

    duration_str = duration_str.lower()
    hours = 0
    minutes = 0

    try:
        if "h" in duration_str:
            hours = int(duration_str.split("h")[0].strip())

        if "m" in duration_str:
            minutes = int(duration_str.split("m")[0].split()[-1].strip())
    except Exception:
        return 0

    return hours * 60 + minutes


def safe_float(v, default=0.0):
    try:
        return float(v)
    except Exception:
        return default


def safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default
