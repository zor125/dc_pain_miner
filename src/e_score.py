# src/e_score.py
import re
from .rules_v1 import PLATFORMS, PAIN_SIGNALS, REPEAT, QUESTION, NOISE, COMBO_RULES

NUM_PATTERN = re.compile(r"(\d+)(\s?원|%|만|천|백)")

def _contains_any(text: str, words: list[str]) -> bool:
    return any(w in text for w in words)

def _group_hit(text: str, group_name: str) -> bool:
    # 플랫폼 그룹
    if group_name in PLATFORMS:
        return _contains_any(text, PLATFORMS[group_name])
    # 문제 신호 그룹
    if group_name in PAIN_SIGNALS:
        return _contains_any(text, PAIN_SIGNALS[group_name])
    return False

def e_score(title: str, body: str) -> tuple[int, list[str]]:
    t = (title + " " + body)
    score = 0
    reasons: list[str] = []

    # 기본 가점
    if _contains_any(t, REPEAT):
        score += 2
        reasons.append("repeat")

    if _contains_any(t, QUESTION):
        score += 2
        reasons.append("question/help")

    if NUM_PATTERN.search(t):
        score += 2
        reasons.append("number(money/percent)")

    # 조합 규칙 가점
    for name, groups, bonus in COMBO_RULES:
        if all(_group_hit(t, g) for g in groups):
            score += bonus
            reasons.append(name)

    # 노이즈 감점
    if _contains_any(t, NOISE):
        score -= 2
        reasons.append("noise")

    return score, reasons
