import json
from typing import Dict, List

METRIC_UNITS = ["g", "kg", "ml", "L", "units", "packs"]
IMPERIAL_UNITS = ["oz", "lb", "fl oz", "cup", "units", "packs"]

UNIT_CONVERSION = {
    ("g", "oz"): 0.035274,
    ("kg", "lb"): 2.20462,
    ("ml", "fl oz"): 0.033814,
    ("L", "cup"): 4.22675,
}


def convert_quantity(amount: float, from_unit: str, to_unit: str) -> float:
    if from_unit == to_unit:
        return amount
    key = (from_unit, to_unit)
    if key in UNIT_CONVERSION:
        return amount * UNIT_CONVERSION[key]
    # simplistic reverse lookup
    reverse_key = (to_unit, from_unit)
    if reverse_key in UNIT_CONVERSION:
        return amount / UNIT_CONVERSION[reverse_key]
    return amount


def serialize_json(data) -> str:
    return json.dumps(data, ensure_ascii=False)


def parse_json(text: str, default):
    try:
        return json.loads(text)
    except Exception:
        return default
