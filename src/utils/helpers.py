from datetime import datetime
def trim_string(text):
    return text[:50] + "..." if len(text) > 50 else text

def parse_timestamp(timestamp: str):
    date_time = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f")
    return date_time.strftime("%Y-%m-%d %H:%M:%S")

def try_convert_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

def try_convert_int(value):
    try:
        int(value)
        return True
    except ValueError:
        return False