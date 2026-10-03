"""Integrate piecewise constant observations over exact lookback windows and report coverage and price bounds."""

from .common import (
    number,
    integer,
    identity,
    records,
    chronology,
    allocate,
    result,
    validate_document,
)
from decimal import Decimal


def _analyze(d):
    now = integer(d["now"])
    window = integer(d["window"], 1)
    start = now - window
    if start < 0:
        raise ValueError("lookback starts before zero")
    obs = chronology(d["observations"])
    prices = [number(o["price"], minimum="0.000000000000000001") for o in obs]
    if not obs or obs[0]["timestamp"] > start or obs[-1]["timestamp"] > now:
        raise ValueError("missing history or future observation")
    if len(set(o["timestamp"] for o in obs)) != len(obs):
        raise ValueError("duplicate observation time")
    segments = []
    area = number(0)
    for i, o in enumerate(obs):
        end = obs[i + 1]["timestamp"] if i + 1 < len(obs) else now
        left = max(start, o["timestamp"])
        right = min(now, end)
        if right > left:
            area += prices[i] * (right - left)
            segments.append(
                {
                    "start": left,
                    "end": right,
                    "price": prices[i],
                    "duration": right - left,
                }
            )
    return result(
        {
            "twap": area / window,
            "covered_seconds": sum(s["duration"] for s in segments),
            "segments": segments,
            "minimum": min(s["price"] for s in segments),
            "maximum": max(s["price"] for s in segments),
        }
    )


def analyze(document):
    validate_document(document)
    try:
        return result(_analyze(document))
    except (KeyError, TypeError, ArithmeticError, RecursionError) as error:
        raise ValueError("invalid domain input: " + str(error)) from error
