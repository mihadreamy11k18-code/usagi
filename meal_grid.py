"""食事の表入力用。既存の記録形式を維持する。"""
import copy
import math
import re


def grams(value):
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    text = str(value).strip()
    if not text:
        return None
    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?|\.[0-9]+)\s*(?:g|ｇ|グラム)?", text, re.I)
    if not match:
        raise ValueError(f"「{text}」はグラム数として集計できません。例：5、2.5、5g")
    number = float(match[1])
    if not math.isfinite(number):
        raise ValueError("有限の数字を入力してください。")
    return number


def fmt(value):
    return "" if value is None else f"{value:g}"


def latest(records):
    result = {}
    for record in records:
        result[(record.get("rabbit_id"), record.get("date"), record.get("meal_time"))] = record
    return list(result.values())


def upsert(records, updates):
    """同一うさぎ・日付・朝夜は一件に統合。未知のフィールドは呼び出し側で保持。"""
    merged = {(r.get("rabbit_id"), r.get("date"), r.get("meal_time")): r for r in latest(records)}
    for record in updates:
        merged[(record["rabbit_id"], record["date"], record["meal_time"])] = record
    return list(merged.values())


def update_from_grid(base, rabbit, day, meal, quantities, toppings, main_names, topping_names):
    record = copy.deepcopy(base or {})
    old_care = record.get("care", [])
    # 薬、非表示の項目などはそのまま残す。
    care = [copy.deepcopy(r) for r in old_care if r.get("item") not in set(main_names + topping_names)]
    total = 0.0
    for name in main_names:
        amount = grams(quantities.get(name, ""))
        if amount is not None:
            total += amount
            care.append({"item": name, "amount": fmt(amount)})
    for name in topping_names:
        if toppings.get(name, False):
            previous = [r for r in old_care if r.get("item") == name]
            care.extend(copy.deepcopy(previous) if previous else [{"item": name, "amount": ""}])
    record.update(rabbit_id=rabbit["id"], rabbit_name=rabbit["name"], date=day,
                  meal_time=meal, care=care, total_amount=fmt(total))
    record.setdefault("previous_leftover", "")
    record.setdefault("cage_cleaned", False)
    record.setdefault("toilet_cleaned", False)
    record.setdefault("memo", "")
    return record
