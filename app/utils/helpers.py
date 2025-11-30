import re

def parse_number(v):
    try:
        s = str(v).replace(",", "")
        m = re.search(r"(\d+(\.\d+)?)", s)
        return float(m.group(1)) if m else None
    except:
        return None
