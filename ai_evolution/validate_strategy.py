#!/usr/bin/env python3
"""AI 전략 후보 JSON 정적 검증기.

외부 패키지 없이 전략 규격/허용지표/위험관리 범위를 검사한다.
실전 주문 코드는 다루지 않는다.
"""

from __future__ import annotations

import json
import pathlib
import sys

ALLOWED_INDICATORS = {
    "momentum_pct",
    "volume_ratio",
    "rsi",
    "breakout_pct",
    "pullback_pct",
    "ma_spread_pct",
    "ma_slope_pct",
    "atr_pct",
    "volatility_pct",
    "bollinger_width_pct",
    "range_position_pct",
    "close_change_pct",
}
ALLOWED_OPS = {"gte", "lte", "between"}


def fail(message: str) -> None:
    raise ValueError(message)


def validate(path: pathlib.Path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    strategy = data.get("strategy", data)
    if not isinstance(strategy, dict):
        fail("strategy object missing")
    if strategy.get("family") != "llm_rule":
        # 기존 로컬 전략 형식은 이 검증기의 대상이 아니다.
        return
    params = strategy.get("params")
    if not isinstance(params, dict):
        fail("params missing")
    rules = params.get("rules")
    if not isinstance(rules, list) or not 2 <= len(rules) <= 8:
        fail("rules must contain 2..8 items")
    for i, rule in enumerate(rules):
        if not isinstance(rule, dict):
            fail(f"rule {i} is not an object")
        if rule.get("indicator") not in ALLOWED_INDICATORS:
            fail(f"rule {i} indicator not allowed")
        if rule.get("op") not in ALLOWED_OPS:
            fail(f"rule {i} op not allowed")
        period = int(rule.get("period", 0))
        period2 = int(rule.get("period2", max(3, period + 1)))
        if not 2 <= period <= 240:
            fail(f"rule {i} period out of range")
        if not 3 <= period2 <= 300:
            fail(f"rule {i} period2 out of range")
        if rule.get("op") == "between":
            low = float(rule.get("low"))
            high = float(rule.get("high"))
            if low > high:
                fail(f"rule {i} between low > high")
        else:
            float(rule.get("value"))
    stop = float(params.get("atr_stop", 0))
    target1 = float(params.get("atr_target1", 0))
    target2 = float(params.get("atr_target2", 0))
    hold_days = int(params.get("hold_days", 0))
    if not 0.7 <= stop <= 4.0:
        fail("atr_stop out of range")
    if not 1.0 <= target1 <= 8.0:
        fail("atr_target1 out of range")
    if not 1.5 <= target2 <= 12.0 or target2 < target1:
        fail("atr_target2 invalid")
    if not 2 <= hold_days <= 90:
        fail("hold_days out of range")


def main() -> int:
    root = pathlib.Path("ai_evolution/candidates")
    if not root.exists():
        print("No candidates yet")
        return 0
    files = sorted(root.glob("strategy_*.json"))
    for path in files:
        validate(path)
        print(f"PASS {path}")
    print(f"Validated {len(files)} candidate(s)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1)
