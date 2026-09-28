"""step3.py の食事・ケア入力画面を Streamlit に移した版。



rabbits.json、foods.json、meal_records.json をこのファイルと同じフォルダに置く。

起動: python -m streamlit run rabbit_streamlit.py

"""

import json

import math

import os

import tempfile

from datetime import date, datetime

from pathlib import Path



import streamlit as st



BASE = Path(__file__).resolve().parent

RABBIT_FILE = BASE / "rabbits.json"

FOOD_FILE = BASE / "foods.json"

MEAL_FILE = BASE / "meal_records.json"



st.set_page_config(page_title="うさぎ管理ソフト", page_icon="🐰", layout="centered")

st.markdown("""<style>

.stApp { background: #fff9f5; color: #514851; }

.block-container { max-width: 1320px; padding-top: 1.6rem; }

h1, h2, h3 { color: #a65670; }

</style>""", unsafe_allow_html=True)





def read_list(path):

    if not path.exists():

        return []

    with path.open(encoding="utf-8") as file:

        value = json.load(file)

    if not isinstance(value, list):

        raise ValueError(f"{path.name} は配列形式で保存してください。")

    return value





def write_records(records):

    """一時ファイル経由で同じフォルダの記録を更新する。"""

    descriptor, name = tempfile.mkstemp(prefix=".meal_records_", suffix=".json", dir=BASE)

    try:

        with os.fdopen(descriptor, "w", encoding="utf-8") as file:

            json.dump(records, file, ensure_ascii=False, indent=4)

            file.flush()

            os.fsync(file.fileno())

        os.replace(name, MEAL_FILE)

    finally:

        if os.path.exists(name):

            os.unlink(name)





def parse_day(value):

    try:

        return datetime.strptime(value, "%Y/%m/%d").date()

    except (TypeError, ValueError):

        return None





def find_record(records, rabbit_id, day, meal_time):

    for record in reversed(records):

        if (record.get("rabbit_id"), record.get("date"), record.get("meal_time")) == (rabbit_id, day, meal_time):

            return record, False

    target = parse_day(day)

    candidates = []

    for record in records:

        past = parse_day(record.get("date"))

        if record.get("rabbit_id") != rabbit_id or past is None:

            continue

        order = 0 if record.get("meal_time") == "あさ" else 1

        target_order = 0 if meal_time == "あさ" else 1

        if (past, order) < (target, target_order):

            candidates.append((past, order, record))

    if candidates:

        return max(candidates, key=lambda entry: (entry[0], entry[1]))[2], True

    return None, False





def load_context(context):

    rabbit_id, day, meal_time = context

    record, copied = find_record(read_list(MEAL_FILE), rabbit_id, day, meal_time)

    care = record.get("care", []) if record else []

    st.session_state.context = context

    st.session_state.rows = [{"item": str(row.get("item", "")), "amount": str(row.get("amount", ""))} for row in care] or [{"item": "", "amount": ""}]

    st.session_state.total = str(record.get("total_amount", "")) if record else ""

    st.session_state.leftover = str(record.get("previous_leftover", "")) if record and not copied else ""

    st.session_state.cage_cleaned = bool(record.get("cage_cleaned", False)) if record and not copied else False

    st.session_state.toilet_cleaned = bool(record.get("toilet_cleaned", False)) if record and not copied else False

    st.session_state.memo = str(record.get("memo", "")) if record else ""

    st.session_state.template = copied

    st.session_state.source = (f"前回（{record['date']} {record['meal_time']}）の内容を表示中" if copied

                               else "この日の保存済み記録を表示中" if record else "このうさぎの記録はまだありません")

    st.session_state.baseline = snapshot()

    st.session_state.epoch = st.session_state.get("epoch", 0) + 1





def snapshot():

    s = st.session_state

    return (tuple((r["item"], r["amount"]) for r in s.rows), s.total, s.leftover, s.cage_cleaned, s.toilet_cleaned, s.memo.strip())





def capture_widgets():

    s = st.session_state

    for index, row in enumerate(s.rows):

        row["item"] = s.get(f"item_{s.epoch}_{index}", row["item"])

        row["amount"] = s.get(f"amount_{s.epoch}_{index}", row["amount"])

    s.total = s.get(f"total_{s.epoch}", s.total)

    s.leftover = s.get(f"leftover_{s.epoch}", s.leftover)

    s.cage_cleaned = s.get(f"cage_cleaned_{s.epoch}", s.cage_cleaned)

    s.toilet_cleaned = s.get(f"toilet_cleaned_{s.epoch}", s.toilet_cleaned)

    s.memo = s.get(f"memo_{s.epoch}", s.memo)





def save_record(rabbits):

    s = st.session_state

    rabbit_id, day, meal_time = s.context

    try:

        number = float(s.total.strip())

        if not math.isfinite(number) or number < 0:

            raise ValueError

    except ValueError:

        s.error = "与えた量の総量を0以上の数字で入力してください。"

        return False

    if s.leftover.strip():

        try:

            leftover_number = float(s.leftover.strip())

            if not math.isfinite(leftover_number) or leftover_number < 0:

                raise ValueError

        except ValueError:

            s.error = "前回のごはんの残りは、0以上の数字で入力してください。"

            return False

    rabbit = next(r for r in rabbits if r["id"] == rabbit_id)

    record = {

        "rabbit_id": rabbit_id, "rabbit_name": rabbit["name"],

        "date": day, "meal_time": meal_time,

        "care": [{"item": r["item"], "amount": r["amount"]} for r in s.rows if r["item"]],

        "total_amount": s.total,

        "previous_leftover": s.leftover.strip(),

        "cage_cleaned": s.cage_cleaned,

        "toilet_cleaned": s.toilet_cleaned,

        "memo": s.memo.strip(),

    }

    try:

        records = read_list(MEAL_FILE)

        for i, old in enumerate(records):

            if (old.get("rabbit_id"), old.get("date"), old.get("meal_time")) == (rabbit_id, day, meal_time):

                records[i] = record

                break

        else:

            records.append(record)

        write_records(records)

    except (OSError, ValueError, json.JSONDecodeError) as exc:

        s.error = f"保存できませんでした：{exc}"

        return False

    s.baseline = snapshot()

    s.template = False

    s.source = "この日の保存済み記録を表示中"

    s.notice = f"保存しました：{rabbit['name']}・{day} {meal_time}"

    return True





def save_if_changed(rabbits):

    capture_widgets()

    s = st.session_state

    if s.template or snapshot() != s.baseline:

        return save_record(rabbits)

    return True





def switch_context(rabbits, new_context):

    s = st.session_state

    if new_context == s.context:

        return

    if save_if_changed(rabbits):

        load_context(new_context)

    else:

        old_id, old_day, old_time = s.context

        s.selected_id = old_id

        s.selected_date = parse_day(old_day)

        s.selected_time = old_time





def change_selection(rabbits):

    s = st.session_state

    switch_context(rabbits, (s.selected_id, s.selected_date.strftime("%Y/%m/%d"), s.selected_time))





def move_rabbit(rabbits, delta):

    s = st.session_state

    current = next(i for i, r in enumerate(rabbits) if r["id"] == s.context[0])

    target = current + delta

    if 0 <= target < len(rabbits):

        switch_context(rabbits, (rabbits[target]["id"], s.context[1], s.context[2]))

        s.selected_id = s.context[0]





def add_row():

    capture_widgets()

    st.session_state.rows.append({"item": "", "amount": ""})





def remove_row(index):

    capture_widgets()

    st.session_state.rows.pop(index)

    if not st.session_state.rows:

        st.session_state.rows.append({"item": "", "amount": ""})

    # 行番号の詰め直しで、前の行の値を使い回さないようにする。

    st.session_state.epoch += 1





def submit(rabbits):

    capture_widgets()

    save_record(rabbits)





try:

    all_rabbits = read_list(RABBIT_FILE)

    foods = read_list(FOOD_FILE)

except (OSError, ValueError, json.JSONDecodeError) as exc:

    st.error(f"マスターファイルを読み込めませんでした：{exc}")

    st.stop()



rabbits = [r for r in all_rabbits if "🌈" not in str(r.get("note") or "") and "販" not in str(r.get("note") or "")]

care_items = list(dict.fromkeys(str(f["name"]) for f in foods if f.get("active", False)))

if not rabbits:

    st.warning("日々の入力対象のうさぎがいません。rabbits.json を確認してください。")

    st.stop()

if "context" not in st.session_state or st.session_state.context[0] not in {r["id"] for r in rabbits}:

    first = (rabbits[0]["id"], date.today().strftime("%Y/%m/%d"), "あさ")

    try:

        load_context(first)

    except (OSError, ValueError, json.JSONDecodeError) as exc:

        st.error(f"記録ファイルを読み込めませんでした：{exc}")

        st.stop()

    st.session_state.selected_id = first[0]

    st.session_state.selected_date = date.today()

    st.session_state.selected_time = "あさ"



s = st.session_state

st.title("🐰 うさぎ管理ソフト")

st.caption("毎日の小さな記録を、ひとつずつ。")

if "error" in s:

    st.error(s.pop("error"))

if "notice" in s:

    st.success(s.pop("notice"))



input_tab, record_tab = st.tabs(["✏️ 毎日の入力", "📖 記録を見る"])

with input_tab:
    left, right = st.columns(2)

    with left:

        st.date_input("日付", key="selected_date", format="YYYY/MM/DD", on_change=change_selection, args=(rabbits,))

    with right:

        st.radio("食事", ["あさ", "よる"], key="selected_time", horizontal=True, on_change=change_selection, args=(rabbits,))

    labels = {r["id"]: f"{r['name']}（{r['id']}）" for r in rabbits}

    st.selectbox("うさぎ", list(labels), format_func=lambda key: labels[key], key="selected_id", on_change=change_selection, args=(rabbits,))

    rabbit = next(r for r in rabbits if r["id"] == s.context[0])

    index = next(i for i, r in enumerate(rabbits) if r["id"] == rabbit["id"])

    st.caption(f"ID：{rabbit['id']}　性別：{rabbit.get('gender', '')}　｜　現在：{index + 1} / {len(rabbits)}羽")



    st.subheader("食事・ケア")

    options = [""] + care_items

    for i, row in enumerate(s.rows):

        columns = st.columns([0.55, 3.5, 1.7, 0.9])

        columns[0].write(f"{i + 1}：")

        choices = options if row["item"] in options else options + [row["item"]]

        columns[1].selectbox(f"項目 {i+1}", choices, index=choices.index(row["item"]), format_func=lambda v: v or "選択してください", label_visibility="collapsed", key=f"item_{s.epoch}_{i}")

        columns[2].text_input(f"量 {i+1}", value=row["amount"], placeholder="量・単位（任意）", label_visibility="collapsed", key=f"amount_{s.epoch}_{i}")

        columns[3].button("削除", key=f"remove_{s.epoch}_{i}", on_click=remove_row, args=(i,))

    st.button("＋ 項目追加", on_click=add_row)

    st.text_input("与えた量の総量（g）＊必須", value=s.total, key=f"total_{s.epoch}")

    st.text_input("前回のごはんの残り（g）", value=s.leftover, key=f"leftover_{s.epoch}", placeholder="合計量・空欄可")

    st.markdown("**お掃除の記録**")

    clean_left, clean_right = st.columns(2)

    with clean_left:

        st.checkbox("ケージ掃除", value=s.cage_cleaned, key=f"cage_cleaned_{s.epoch}")

    with clean_right:

        st.checkbox("トイレ掃除", value=s.toilet_cleaned, key=f"toilet_cleaned_{s.epoch}")

    st.text_area("✎ MEMO", value=s.memo, height=85, key=f"memo_{s.epoch}")

    st.caption(s.source)

    st.progress((index + 1) / len(rabbits), text=f"現在：{index + 1} / {len(rabbits)}羽")

    previous, save, following = st.columns(3)

    previous.button("← 前のうさぎ", disabled=index == 0, on_click=move_rabbit, args=(rabbits, -1), use_container_width=True)

    save.button("保存", type="primary", on_click=submit, args=(rabbits,), use_container_width=True)

    following.button("次のうさぎ →", disabled=index == len(rabbits)-1, on_click=move_rabbit, args=(rabbits, 1), use_container_width=True)


with record_tab:
    st.subheader("保存した記録を見る")
    try:
        saved_records = read_list(MEAL_FILE)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        st.error(f"記録ファイルを読み込めませんでした：{exc}")
        saved_records = []
    if not saved_records:
        st.info("保存済みの記録はまだありません。")
    else:
        name_options = {str(r.get("id", "")): str(r.get("name", "")) for r in all_rabbits}
        for r in saved_records:
            name_options.setdefault(str(r.get("rabbit_id", "")), str(r.get("rabbit_name", "")))
        filter_left, filter_right = st.columns(2)
        with filter_left:
            day_filter = st.selectbox(
                "日付", ["すべて"] + sorted({str(r.get("date", "")) for r in saved_records}, reverse=True)
            )
        with filter_right:
            rabbit_filter = st.selectbox(
                "うさぎ", ["すべて"] + sorted({str(r.get("rabbit_id", "")) for r in saved_records}),
                format_func=lambda rid: "すべて" if rid == "すべて" else f"{name_options.get(rid, rid)}（{rid}）",
            )
        filtered = [
            (i, r) for i, r in enumerate(saved_records)
            if (rabbit_filter == "すべて" or str(r.get("rabbit_id", "")) == rabbit_filter)
            and (day_filter == "すべて" or str(r.get("date", "")) == day_filter)
        ]
        sort_mode = st.radio(
            "並び順", ["日付順（新しい順）", "日付順（古い順）", "うさぎ順"],
            horizontal=True,
        )
        def order_key(pair):
            i, record = pair
            day = str(record.get("date", ""))
            meal = 0 if record.get("meal_time") == "あさ" else 1
            if sort_mode == "うさぎ順":
                return (str(record.get("rabbit_id", "")), day, meal, i)
            return (day, meal, str(record.get("rabbit_id", "")), i)

        filtered.sort(key=order_key, reverse=sort_mode == "日付順（新しい順）")
        st.caption(f"{len(filtered)}件の記録")
        if filtered:
            def care_text(record):
                return "、".join(
                    f"{row.get('item', '')} {row.get('amount', '')}".strip()
                    for row in record.get("care", []) if isinstance(row, dict)
                )

            st.dataframe([{
                "日付": r.get("date", ""), "朝夜": r.get("meal_time", ""),
                "うさぎ": r.get("rabbit_name") or name_options.get(str(r.get("rabbit_id", "")), ""),
                "食事・ケア": care_text(r), "総量g": r.get("total_amount", ""),
                "残りg": r.get("previous_leftover", ""),
                "ケージ": "済" if r.get("cage_cleaned") else "",
                "トイレ": "済" if r.get("toilet_cleaned") else "",
                "MEMO": r.get("memo", ""),
            } for _, r in filtered], hide_index=True, width=1090,
                column_config={
                    "日付": st.column_config.TextColumn(width=108),
                    "朝夜": st.column_config.TextColumn(width=58, help="あさ／よる"),
                    "うさぎ": st.column_config.TextColumn(width=118),
                    "食事・ケア": st.column_config.TextColumn(width=350, help="長い内容は下の詳細で全文を確認できます"),
                    "総量g": st.column_config.TextColumn(width=62),
                    "残りg": st.column_config.TextColumn(width=62),
                    "ケージ": st.column_config.TextColumn(width=64, help="ケージ掃除"),
                    "トイレ": st.column_config.TextColumn(width=64, help="トイレ掃除"),
                    "MEMO": st.column_config.TextColumn(width=180),
                },
            )
            chosen = st.selectbox(
                "詳しく見る記録", range(len(filtered)),
                format_func=lambda n: (
                    f"{filtered[n][1].get('date', '')} {filtered[n][1].get('meal_time', '')} "
                    f"｜{filtered[n][1].get('rabbit_name', '')}（{filtered[n][1].get('rabbit_id', '')}）"
                ),
            )
            selected = filtered[chosen][1]
            st.markdown("**食事・ケア（全文）**")
            if selected.get("care"):
                for row in selected["care"]:
                    if isinstance(row, dict):
                        st.write(f"・{row.get('item', '')}　{row.get('amount', '')}")
            else:
                st.write("記録なし")
            st.write("与えた量の総量：", str(selected.get("total_amount", "")) + " g" if str(selected.get("total_amount", "")) else "未入力")
            st.write("前回のごはんの残り：", str(selected.get("previous_leftover", "")) + " g" if str(selected.get("previous_leftover", "")) else "未入力")
            st.write("ケージ掃除：", "済" if selected.get("cage_cleaned") else "記録なし")
            st.write("トイレ掃除：", "済" if selected.get("toilet_cleaned") else "記録なし")
            st.write("MEMO：", selected.get("memo", "") or "記録なし")
            st.caption("修正するときは「毎日の入力」タブで同じ日付・あさ／よる・うさぎを選び、保存してください。")
        else:
            st.info("この条件に合う記録はありません。")
