"""contextforge_cli.utils.duration_str"""
# Copyright 2022 Cisco Systems, Inc. and/or its affiliates.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Adapted from durationpy
# https://github.com/icholy/durationpy/
from __future__ import annotations

import re
from datetime import timedelta

_nanosecond_size = 1
_microsecond_size = 1000 * _nanosecond_size
_millisecond_size = 1000 * _microsecond_size
_second_size = 1000 * _millisecond_size
_minute_size = 60 * _second_size
_hour_size = 60 * _minute_size
_day_size = 24 * _hour_size
_week_size = 7 * _day_size
_month_size = 30 * _day_size
_year_size = 365 * _day_size

units = {
    "ns": _nanosecond_size,
    "us": _microsecond_size,
    "µs": _microsecond_size,
    "μs": _microsecond_size,
    "ms": _millisecond_size,
    "s": _second_size,
    "m": _minute_size,
    "h": _hour_size,
    "d": _day_size,
    "w": _week_size,
    "mm": _month_size,
    "y": _year_size,
}


def microseconds_from_duration_str(duration: str) -> float:
    """Parse a duration string into a microseconds float value."""
    if duration in {"0", "+0", "-0"}:
        return 0

    pattern = re.compile(r"([\d\.]+)([a-zµμ]+)")
    matches = pattern.findall(duration)
    if not len(matches):
        raise ValueError(f"Invalid duration '{duration}'")

    total: float = 0
    sign = -1 if duration[0] == "-" else 1

    for value, unit in matches:
        if unit not in units:
            raise ValueError(f"Unknown unit '{unit}' in duration '{duration}'")
        try:
            total += float(value) * units[unit]
        except Exception as e:
            raise ValueError(f"Invalid value '{value}' in duration '{duration}'") from e

    return sign * (total / _microsecond_size)


def timedelta_from_duration_str(duration: str) -> timedelta:
    """
    Parse a Golang duration string into a Python timedelta value.

    Raises a ValueError if the string cannot be parsed.

    A duration string is a possibly signed sequence of decimal numbers,
    each with optional fraction and a unit suffix, such as "300ms", "-1.5h" or "2h45m".

    Valid units are :
        ns - nanoseconds
        us - microseconds
        ms - millisecond
        s  - second
        m  - minute
        h  - hour
        w  - week
        mm - month
        y  - year
    """
    return timedelta(microseconds=microseconds_from_duration_str(duration))


def timedelta_to_duration_str(delta: timedelta, extended: bool = False) -> str:
    """
    Return a Golang duration string representation of a timedelta value.

    A duration string is a possibly signed sequence of decimal numbers,
    each with optional fraction and a unit suffix, such as "300ms", "-1.5h" or "2h45m".

    Components of the returned string are:
        ns - nanoseconds
        us - microseconds
        ms - millisecond
        s  - second
        m  - minute
        h  - hour
        w  - week
        mm - month
        y  - year
    """
    total_seconds = delta.total_seconds()
    sign = "-" if total_seconds < 0 else ""
    nanoseconds = abs(total_seconds * _second_size)

    if total_seconds < 1:
        result_str = _to_str_small(nanoseconds, extended)
    else:
        result_str = _to_str_large(nanoseconds, extended)

    return f"{sign}{result_str}"


def _to_str_small(nanoseconds: float | None, extended: bool = False) -> str:
    result_str = ""

    if not nanoseconds:
        return "0"

    if milliseconds := int(nanoseconds / _millisecond_size):
        nanoseconds -= _millisecond_size * milliseconds
        result_str += f"{milliseconds:g}ms"

    if microseconds := int(nanoseconds / _microsecond_size):
        nanoseconds -= _microsecond_size * microseconds
        result_str += f"{microseconds:g}us"

    if nanoseconds:
        result_str += f"{nanoseconds:g}ns"

    return result_str


def _to_str_large(nanoseconds: float, extended: bool = False) -> str:
    result_str = ""

    if extended:
        if years := int(nanoseconds / _year_size):
            nanoseconds -= _year_size * years
            result_str += f"{years:g}y"

        if months := int(nanoseconds / _month_size):
            nanoseconds -= _month_size * months
            result_str += f"{months:g}mm"

        if days := int(nanoseconds / _day_size):
            nanoseconds -= _day_size * days
            result_str += f"{days:g}d"

    if hours := int(nanoseconds / _hour_size):
        nanoseconds -= _hour_size * hours
        result_str += f"{hours:g}h"

    if minutes := int(nanoseconds / _minute_size):
        nanoseconds -= _minute_size * minutes
        result_str += f"{minutes:g}m"

    if seconds := nanoseconds / float(_second_size):
        nanoseconds -= _second_size * seconds
        result_str += f"{seconds:g}s"

    return result_str
