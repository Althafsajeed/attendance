import re
from decimal import Decimal, InvalidOperation
from math import asin, cos, radians, sin, sqrt

from django.utils import timezone


def distance_meters(lat1, lon1, lat2, lon2):
    radius = 6371000
    lat1, lon1, lat2, lon2 = map(float, (lat1, lon1, lat2, lon2))
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    return 2 * radius * asin(sqrt(a))


def current_time_in_window(start, end):
    current = timezone.localtime().time()
    return start <= current <= end


def parse_coordinate(value):
    text = str(value).strip().upper()
    if not text:
        raise ValueError("Coordinate is required.")

    try:
        return Decimal(text)
    except InvalidOperation:
        pass

    pattern = re.compile(
        r"""^\s*
        (?P<degrees>\d+(?:\.\d+)?)\s*(?:°|D)?\s*
        (?P<minutes>\d+(?:\.\d+)?)?\s*(?:'|M)?\s*
        (?P<seconds>\d+(?:\.\d+)?)?\s*(?:"|S)?\s*
        (?P<direction>[NSEW])?
        \s*$""",
        re.VERBOSE,
    )
    match = pattern.match(text)
    if not match:
        raise ValueError("Use decimal format or DMS format like 9°24'06.3\"N.")

    degrees = Decimal(match.group("degrees"))
    minutes = Decimal(match.group("minutes") or "0")
    seconds = Decimal(match.group("seconds") or "0")
    direction = match.group("direction")

    if minutes >= 60 or seconds >= 60:
        raise ValueError("Minutes and seconds must be less than 60.")

    coordinate = degrees + (minutes / Decimal("60")) + (seconds / Decimal("3600"))
    if direction in {"S", "W"}:
        coordinate = -coordinate
    return coordinate.quantize(Decimal("0.000001"))
