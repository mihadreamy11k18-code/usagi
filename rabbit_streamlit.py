"""step3.py の食事・ケア入力画面を Streamlit に移した版。

ローカルでは3つのJSONファイルを同じフォルダに置く。
Google DriveではStreamlit Secretsの認証情報とファイルIDを使用する。

起動: python -m streamlit run rabbit_streamlit.py

"""

import json

import math
import pandas as pd
from meal_grid import grams, fmt, latest, upsert, update_from_grid



from datetime import date, datetime

from pathlib import Path

import streamlit as st
from drive_storage import read_list, write_records

BASE = Path(__file__).resolve().parent

RABBIT_FILE = BASE / "rabbits.json"

FOOD_FILE = BASE / "foods.json"

MEAL_FILE = BASE / "meal_records.json"

st.set_page_config(page_title="うさぎ管理ソフト", page_icon="🐰", layout="wide")

st.markdown("""<style>

.stApp { background: #fff9f5; color: #514851; }

.block-container { max-width: 1320px; padding: 4rem .8rem 1rem; }
[data-testid="stVerticalBlock"] { gap: .45rem; }
h1 { font-size: 1.6rem !important; }
h2, h3 { font-size: 1.15rem !important; }
@media (max-width: 640px) {
 .block-container { padding: 4rem .4rem 1rem; }
 h1 { font-size: 1.25rem !important; }
 [data-testid="stHorizontalBlock"] { gap: .3rem; }
}


h1, h2, h3 { color: #a65670; }

</style>""", unsafe_allow_html=True)

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

        if record.get("rabbit_id") != rabbit_id or past is None or record.get("meal_time") != meal_time:

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
    st.session_state.topping_selected = {name: any(r.get("item") == name for r in care) for name in topping_names}
    st.session_state.topping_original = [dict(r) for r in care if r.get("item") in topping_names]
    care = [r for r in care if r.get("item") not in topping_names]

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

    return (tuple((r["item"], r["amount"]) for r in s.rows), s.total, s.leftover, s.cage_cleaned, s.toilet_cleaned, s.memo.strip(), tuple(s.topping_selected.items()))

def capture_widgets():

    s = st.session_state

    for index, row in enumerate(s.rows):

        row["item"] = s.get(f"item_{s.epoch}_{index}", row["item"])

        row["amount"] = s.get(f"amount_{s.epoch}_{index}", row["amount"])

    for name in topping_names:
        s.topping_selected[name] = bool(s.get(f"top_{s.epoch}_{name}", s.topping_selected.get(name, False)))
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

        "care": [{"item": r["item"], "amount": r["amount"]} for r in s.rows if r["item"]] + [
            row for name in topping_names if s.topping_selected.get(name)
            for row in ([dict(r) for r in s.topping_original if r["item"] == name] or [{"item": name, "amount": ""}])
        ],

        "total_amount": s.total,

        "previous_leftover": s.leftover.strip(),

        "cage_cleaned": s.cage_cleaned,

        "toilet_cleaned": s.toilet_cleaned,

        "memo": s.memo.strip(),

    }

    try:

        records = read_list(MEAL_FILE)

        old = next((r for r in reversed(records) if (r.get("rabbit_id"), r.get("date"), r.get("meal_time")) == (rabbit_id, day, meal_time)), {})
        records = upsert(records, [{**old, **record}])
        write_records(records, MEAL_FILE)

    except (OSError, ValueError, json.JSONDecodeError) as exc:

        s.error = f"保存できませんでした：{exc}"

        return False

    s.grid_epoch = s.get("grid_epoch", 0) + 1
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

    # 使用中のDriveマスターが旧分類でも、指定された2品はトッピングとして表示。
    foods = [{**f, "category": "トッピング"} if f.get("name") in {"トリーツ", "オートミール"} else f for f in foods]

    # Drive側のマスターが未更新でも「その他」は入力可能にする。
    if not any(f.get("name") == "その他" for f in foods):
        foods = foods + [{"id": "F_OTHER", "name": "その他", "category": "主", "active": True}]

except (OSError, ValueError, json.JSONDecodeError) as exc:

    st.error(f"マスターファイルを読み込めませんでした：{exc}")

    st.stop()

rabbits = [r for r in all_rabbits if "🌈" not in str(r.get("note") or "") and "販" not in str(r.get("note") or "")]

topping_names = list(dict.fromkeys(str(f["name"]) for f in foods if f.get("active", False) and f.get("category") == "トッピング"))

care_items = list(dict.fromkeys(str(f["name"]) for f in foods if f.get("active", False) and f.get("category") != "トッピング"))

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

input_tab, grid_tab, record_tab, master_tab, rabbit_list_tab = st.tabs(["🐰 うさぎごと", "🥣 ごはんごと", "📖 記録を見る", "🐰 うさぎ追加", "📋 うさぎリスト"])

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

    st.markdown("**トッピング（複数選択可）**")
    top_columns = st.columns(3)
    for i, name in enumerate(topping_names):
        top_columns[i % 3].checkbox(name, value=s.topping_selected.get(name, False), key=f"top_{s.epoch}_{name}")

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


with grid_tab:
    def grid_rank(rabbit):
        rank = rabbit.get("food_grid_order")
        return rank if isinstance(rank, int) and not isinstance(rank, bool) else 1000000
    grid_rabbits = sorted(rabbits, key=grid_rank)
    st.caption("ごはんを横に配分入力できます。トッピングはチェック式です。表の変更は「まとめて保存」で確定します。")
    c1, c2 = st.columns(2)
    s.setdefault("grid_drafts", {})
    if "grid_time" not in s and "last_grid_time" in s:
        s.grid_time = s.last_grid_time
    if "grid_date" not in s and "last_grid_date" in s:
        s.grid_date = s.last_grid_date
    grid_date = c1.date_input("表の日付", value=date.today(), format="YYYY/MM/DD", key="grid_date")
    grid_time = c2.radio("表の食事", ["あさ", "よる"], horizontal=True, key="grid_time")
    s.last_grid_date, s.last_grid_time = grid_date, grid_time
    day = grid_date.strftime("%Y/%m/%d")
    draft_key = f"{day}_{grid_time}"
    st.info(f"入力・保存先：{day}　{grid_time}")
    try:
        grid_records = latest(read_list(MEAL_FILE))
    except (OSError, ValueError) as exc:
        st.error(str(exc))
        st.stop()
    grid_key = (day, grid_time, s.get("grid_epoch", 0))
    if s.get("grid_context") != grid_key:
        bases, sources, originals = {}, {}, {}
        for r in grid_rabbits:
            source, copied = find_record(grid_records, r["id"], day, grid_time)
            sources[r["id"]] = source
            originals[r["id"]] = next((x for x in grid_records if (x.get("rabbit_id"), x.get("date"), x.get("meal_time")) == (r["id"], day, grid_time)), None)
            bases[r["id"]] = originals[r["id"]] or {}
        main_names = list(dict.fromkeys(f["name"] for f in foods if f.get("active", False) and f.get("category") == "主"))
        # 過去の主食・未登録の量付き項目も表示し、消さずに修正できるようにする。
        medicine_names = {f["name"] for f in foods if f.get("category") == "薬"}
        for source in sources.values():
            for row in (source or {}).get("care", []):
                name = row.get("item", "")
                if name and name not in main_names + topping_names and name not in medicine_names:
                    main_names.append(name)
        quantity = pd.DataFrame({r["id"]: [
            " / ".join(str(x.get("amount", "")) for x in (sources[r["id"]] or {}).get("care", []) if x.get("item") == name)
            for name in main_names] for r in grid_rabbits}, index=main_names)
        checks = pd.DataFrame({r["id"]: [any(x.get("item") == name for x in (sources[r["id"]] or {}).get("care", []))
            for name in topping_names] for r in grid_rabbits}, index=topping_names)
        s.grid_context, s.grid_bases, s.grid_originals = grid_key, bases, originals
        s.grid_main_names, s.grid_quantity, s.grid_checks = main_names, quantity, checks
        s.grid_leftovers = pd.DataFrame({r["id"]: [str((originals[r["id"]] or {}).get("previous_leftover", "") or "")] for r in grid_rabbits}, index=["前回のごはんの残り（g）"])
        draft = s.grid_drafts.get(draft_key)
        if draft:
            # 日付・朝夜を行き来しても編集中の表と比較元の記録を保持。
            s.grid_quantity = draft["quantity"].reindex(index=main_names, columns=quantity.columns, fill_value="").copy()
            s.grid_checks = draft["checks"].reindex(index=topping_names, columns=checks.columns, fill_value=False).copy()
            s.grid_originals = draft["originals"]
            if "leftovers" in draft:
                s.grid_leftovers = draft["leftovers"].reindex(columns=quantity.columns, fill_value="").copy()
    main_names = s.grid_main_names
    st.caption("保存済みの内容を表示し、未記録のうさぎは同じ朝夜の直近の食事・トッピングを引き継ぎます（朝は前の朝、夜は前の夜）。薬・残り・掃除・メモは引き継ぎ保存しません。")
    columns = {r["id"]: st.column_config.TextColumn(r["name"], width="small", help=f"ID：{r['id']}　グラム数を入力") for r in grid_rabbits}
    with st.container():
        st.markdown("**ごはんの量（g）**")
        edited = st.data_editor(s.grid_quantity, column_config=columns, disabled=["_index"], use_container_width=True, height=min(500, 36 * (len(main_names)+1)), key=f"quantity_{grid_key}")
        edited = edited.fillna("")
        st.markdown("**前回のごはんの残り（g）**")
        st.caption("今回確認した残りの量を入力します。過去の残量は引き継ぎません。")
        leftovers = st.data_editor(s.grid_leftovers, column_config=columns, disabled=["_index"], use_container_width=True, height=75, key=f"leftovers_{grid_key}").fillna("")
        st.markdown("**トッピング（チェックで記録）**")
        check_config = {r["id"]: st.column_config.CheckboxColumn(r["name"], width="small") for r in grid_rabbits}
        checked = st.data_editor(s.grid_checks, column_config=check_config, disabled=["_index"], use_container_width=True, height=36*(len(topping_names)+1), key=f"checks_{grid_key}")
        st.caption("空欄＝そのごはんの記録なし。0＝0gの記録。トッピングのチェックは重量の合計に含みません。")
        a, b = st.columns(2)
        preview = a.button("合計を確認")
        commit = b.button(f"{grid_time}の内容をまとめて保存", type="primary")
    # 各セルの編集がサーバーへ届くたびに、日付・朝夜別の下書きを残す。
    s.grid_drafts[draft_key] = {"quantity": edited.copy(), "leftovers": leftovers.copy(), "checks": checked.copy(), "originals": s.grid_originals.copy()}
    with st.expander("うさぎの並び順を変更・保存"):
        st.caption("移動するうさぎと移動先を選び、変更後の並びを確認して保存してください。保存した順番は、次回も使います。ごはんごとの画面だけに適用し、ほかの端末とも共有します。表の見出しを直接ドラッグした順番は保存されません。")
        order_ids = [r["id"] for r in grid_rabbits]
        order_names = {r["id"]: r["name"] for r in grid_rabbits}
        selected_order = st.selectbox("移動するうさぎ", order_ids, format_func=lambda rid: order_names[rid], key="grid_order_rabbit")
        st.write("現在の並び（左から）：" + " → ".join(f"{n+1}. {order_names[rid]}" for n, rid in enumerate(order_ids)))
        other_ids = [rid for rid in order_ids if rid != selected_order]
        if other_ids:
            anchor = st.selectbox("移動先の目印にするうさぎ", other_ids, format_func=lambda rid: f"{order_ids.index(rid)+1}番：{order_names[rid]}", key=f"grid_order_anchor_{selected_order}")
            placement = st.radio("置く位置", ["このうさぎの前（左）", "このうさぎの後ろ（右）"], horizontal=True, key="grid_order_placement")
            proposed_order = other_ids.copy()
            destination = proposed_order.index(anchor) + (1 if placement == "このうさぎの後ろ（右）" else 0)
            proposed_order.insert(destination, selected_order)
            st.info(f"{order_names[selected_order]}を、{order_names[anchor]}の{'後ろ（右）' if placement == 'このうさぎの後ろ（右）' else '前（左）'}へ移動します。")
            st.write("変更後の並び（左から）：" + " → ".join(f"{n+1}. {order_names[rid]}" for n, rid in enumerate(proposed_order)))
            save_order = st.button("この並び順を保存", disabled=proposed_order == order_ids)
        else:
            save_order = False
        if save_order:
            order_ids = proposed_order
            try:
                master = read_list(RABBIT_FILE)
                ranks = {rid: n for n, rid in enumerate(order_ids)}
                for rabbit in master:
                    if rabbit.get("id") in ranks:
                        rabbit["food_grid_order"] = ranks[rabbit["id"]]
                write_records(master, RABBIT_FILE)
                s.grid_epoch = s.get("grid_epoch", 0) + 1
                s.notice = "ごはんごとのうさぎの並び順を保存しました。"
                st.rerun()
            except (OSError, ValueError) as exc:
                st.error(f"並び順を保存できませんでした：{exc}")
    draft_json = json.dumps({"date": day, "meal_time": grid_time,
        "quantities": edited.to_dict(), "leftovers": leftovers.to_dict(), "toppings": checked.to_dict()}, ensure_ascii=False, indent=2)
    st.download_button("入力中の表を控えとしてダウンロード", data=draft_json,
                       file_name=f"usagi_{grid_date.isoformat()}_{grid_time}.json", mime="application/json")
    st.caption("セルを編集したらEnterまたはセルの外をクリックして確定してください。下書きはこの接続中だけ保持します。画面更新・終了前には保存か控えのダウンロードをしてください。")
    # 右端に食材別合計、最下段にうさぎ別合計を表示。
    totals = edited.copy()
    problems = []
    numeric = pd.DataFrame(0.0, index=main_names, columns=[r["id"] for r in grid_rabbits])
    for r in grid_rabbits:
        for name in main_names:
            try:
                numeric.loc[name, r["id"]] = grams(edited.loc[name, r["id"]]) or 0
            except ValueError as exc:
                problems.append(f"{r['name']}／{name}：{exc}")
                numeric.loc[name, r["id"]] = float("nan")
    totals["合計g"] = [fmt(numeric.loc[name].sum()) if not numeric.loc[name].isna().any() else "要確認" for name in main_names]
    totals.loc["今回合計g"] = [fmt(numeric[r["id"]].sum()) if not numeric[r["id"]].isna().any() else "要確認" for r in grid_rabbits] + [fmt(numeric.sum().sum()) if not numeric.isna().any().any() else "要確認"]
    st.markdown(f"**{day} {grid_time}：入力中の合計（保存前も含む）**")
    st.dataframe(totals.rename(columns={r["id"]: f"{r['name']}（{r['id']}）" for r in grid_rabbits}), use_container_width=True)
    for r in grid_rabbits:
        try:
            grams(leftovers.iloc[0][r["id"]])
        except ValueError as exc:
            problems.append(f"{r['name']}／前回のごはんの残り：{exc}")
    for problem in problems:
        st.warning(problem)
    if commit and problems:
        st.error("保存は行っていません。上の黄色いメッセージの欄を修正してください。入力内容は下書きに残っています。")
    if commit and not problems:
        try:
            capture_widgets()
            if snapshot() != s.baseline:
                raise ValueError("うさぎごとの画面に未保存の変更があります。先にそちらを保存してから、表を再読み込みしてください。")
            current = read_list(MEAL_FILE)
            updates = []
            for r in grid_rabbits:
                rid = r["id"]
                now = next((x for x in reversed(current) if (x.get("rabbit_id"), x.get("date"), x.get("meal_time")) == (rid, day, grid_time)), None)
                if now != s.grid_originals[rid]:
                    raise ValueError(f"{r['name']}の記録が別の画面で更新されています。表を再読み込みしてから入力してください。")
                quantities = edited[rid].to_dict()
                toppings = checked[rid].to_dict()
                leftover = grams(leftovers.iloc[0][rid])
                if now is None and not any(grams(v) is not None for v in quantities.values()) and not any(toppings.values()) and leftover is None:
                    continue
                updated = update_from_grid(now, r, day, grid_time, quantities, toppings, main_names, topping_names)
                updated["previous_leftover"] = fmt(leftover)
                updates.append(updated)
            if updates:
                write_records(upsert(current, updates), MEAL_FILE)
                s.grid_drafts.pop(draft_key, None)
                s.grid_epoch = s.get("grid_epoch", 0) + 1
                load_context(s.context)
                s.notice = f"{day} {grid_time}：{len(updates)}羽分を保存しました。"
                st.rerun()
            else:
                st.info("入力された内容がありません。")
        except (OSError, ValueError) as exc:
            st.error(f"保存できませんでした：{exc}")
    discard_draft = st.checkbox("この日時の下書きを破棄して読み直す", key="discard_grid_draft")
    if st.button("表を再読み込み", disabled=not discard_draft, help="控えを保存してから操作してください。"):
        s.grid_drafts.pop(draft_key, None)
        s.grid_epoch = s.get("grid_epoch", 0) + 1
        st.rerun()
    st.markdown("**保存済み：ごはん別の朝・夜合計**")
    summary = []
    for name in main_names:
        item = {"ごはん": name}
        for meal, label in [("あさ", "朝の合計g"), ("よる", "夜の合計g")]:
            numbers, bad, count = [], False, 0
            for record in grid_records:
                if record.get("date") == day and record.get("meal_time") == meal:
                    for row in record.get("care", []):
                        if row.get("item") == name:
                            count += 1
                            try:
                                amount = grams(row.get("amount", ""))
                                if amount is None:
                                    bad = True
                                else:
                                    numbers.append(amount)
                            except ValueError:
                                bad = True
            item[label] = "量の記録を確認" if bad else fmt(sum(numbers)) if count else "未記録"
        summary.append(item)
    st.dataframe(summary, hide_index=True, use_container_width=True)
    with st.expander("全体を縮小して見る（入力中の表）"):
        import html
        import streamlit.components.v1 as components
        overview = totals.rename(columns={r["id"]: r["name"] for r in grid_rabbits}).to_html(escape=True)
        components.html("""<style>body{margin:0;font-family:sans-serif}table{border-collapse:collapse;font-size:12px;white-space:nowrap}th,td{border:1px solid #dbcbd2;padding:5px;text-align:center}th{background:#faedf2}#wrap{transform-origin:top left}</style><div id="wrap">""" + overview + """</div><script>function fit(){let w=document.getElementById('wrap'),t=w.querySelector('table');w.style.transform='scale('+Math.min(1,document.documentElement.clientWidth/t.scrollWidth)+')';}window.addEventListener('resize',fit);fit();</script>""", height=400, scrolling=False)

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

            } for _, r in filtered], hide_index=True, use_container_width=True,

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

with master_tab:
    st.subheader("うさぎを追加する")
    st.caption("現在使用している rabbits.json に追加します。Google Drive設定中はDrive側へ保存します。")
    default_id = f"{max([int(r['id']) for r in all_rabbits if str(r.get('id', '')).isdigit()] or [0]) + 1:04d}"
    registration_epoch = st.session_state.get("registration_epoch", 0)
    with st.form(f"new_rabbit_{registration_epoch}"):
        new_id = st.text_input("ID＊必須", value=default_id, key=f"new_rabbit_id_{registration_epoch}",
                               help="登録済みの最大ID＋1を表示します。手動で変更できます。例：0029")
        new_name = st.text_input("名前＊必須")
        new_gender = st.radio("性別", ["不明", "♂", "♀"], horizontal=True)
        new_birthday = st.text_input("誕生日", placeholder="例：2026.9.1（不明なら空欄）")
        new_breed = st.text_input("品種")
        new_note = st.text_input("メモ", help="メモに🌈または販が含まれると、毎日の入力対象から外れます。")
        add_rabbit = st.form_submit_button("このうさぎを登録", type="primary")
    if add_rabbit:
        if not new_name.strip():
            st.error("名前を入力してください。")
        else:
            try:
                master = read_list(RABBIT_FILE)
                if any(r.get("name") == new_name.strip() for r in master):
                    raise ValueError("同じ名前が登録されています。区別できる名前で登録してください。")
                entered_id = new_id.strip()
                if not entered_id or not entered_id.isascii() or not entered_id.isdigit() or int(entered_id) < 1:
                    raise ValueError("IDは1以上の半角数字で入力してください。例：0029")
                saved_id = f"{int(entered_id):04d}"
                if any(str(r.get("id", "")) == saved_id or
                       (str(r.get("id", "")).isdigit() and int(r["id"]) == int(entered_id)) for r in master):
                    raise ValueError(f"ID：{saved_id} はすでに登録されています。別のIDを入力してください。")
                master.append({"id": saved_id, "name": new_name.strip(),
                               "gender": "" if new_gender == "不明" else new_gender,
                               "birthday": new_birthday.strip(), "breed": new_breed.strip(), "note": new_note.strip()})
                write_records(master, RABBIT_FILE)
                s.grid_epoch = s.get("grid_epoch", 0) + 1
                s.registration_epoch = registration_epoch + 1
                s.notice = f"{new_name.strip()}を登録しました。ID：{saved_id}"
                st.rerun()
            except (OSError, ValueError) as exc:
                st.error(f"登録できませんでした：{exc}")


with rabbit_list_tab:
    st.subheader("うさぎリスト")
    try:
        rabbit_master = read_list(RABBIT_FILE)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        st.error(f"名簿を読み込めませんでした：{exc}")
    else:
        st.caption(f"登録されているうさぎ：{len(rabbit_master)}羽（毎日の入力対象外のうさぎも含みます）")
        list_rows = [{
            "ID": str(r.get("id", "")),
            "名前": str(r.get("name") or ""),
            "性別": str(r.get("gender") or ""),
            "誕生日": str(r.get("birthday") or ""),
            "品種": str(r.get("breed") or ""),
            "メモ": str(r.get("note") or ""),
        } for r in rabbit_master]
        if list_rows:
            st.dataframe(list_rows, hide_index=True, use_container_width=True,
                         height=min(650, 36 * (len(list_rows) + 1)),
                         column_config={
                             "ID": st.column_config.TextColumn(width="small"),
                             "名前": st.column_config.TextColumn(width="small"),
                             "性別": st.column_config.TextColumn(width="small"),
                             "誕生日": st.column_config.TextColumn(width="small"),
                             "品種": st.column_config.TextColumn(width="medium"),
                             "メモ": st.column_config.TextColumn(width="large"),
                         })
            chosen_rabbit = st.selectbox("詳しく見るうさぎ", range(len(rabbit_master)),
                format_func=lambda i: f"{rabbit_master[i].get('id', '')}：{rabbit_master[i].get('name', '')}",
                key="rabbit_list_detail")
            detail = rabbit_master[chosen_rabbit]
            for label, field in [("ID", "id"), ("名前", "name"), ("性別", "gender"),
                                 ("誕生日", "birthday"), ("品種", "breed"), ("メモ", "note")]:
                st.write(f"{label}：{detail.get(field) or '未登録'}")
        else:
            st.info("登録されているうさぎはいません。")
