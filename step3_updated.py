import json
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date, datetime
import ctypes
import math
import calendar


# ==============================
# データファイル
# ==============================

RABBIT_FILE = "rabbits.json"
FOOD_FILE = "foods.json"
MEAL_FILE = "meal_records.json"

# 画面の色と文字。日本語が読みやすいメイリオを使う。
BG = "#fff9f5"
INK = "#514851"
MUTED = "#786f78"
PINK = "#e8a6b7"
ROSE = "#a65670"
SAGE = "#dcebdc"
WHITE = "#ffffff"
FONT = "メイリオ"


def paint_widget(widget):
    """後から増やした入力行にも同じ色と文字を適用する。"""
    if isinstance(widget, tk.Frame):
        widget.configure(bg=BG)
    elif isinstance(widget, tk.Label):
        widget.configure(bg=BG, fg=INK, font=(FONT, 10))
    elif isinstance(widget, tk.Radiobutton):
        widget.configure(bg=BG, fg=INK, selectcolor=WHITE,
                         activebackground=BG, font=(FONT, 10))
    # ttk.Combobox は tk.Entry の派生クラス。先に判定しないと
    # ttk が受け付けない -bg を渡してしまう。
    elif isinstance(widget, ttk.Combobox):
        widget.configure(font=(FONT, 10))
    elif isinstance(widget, tk.Entry):
        widget.configure(bg=WHITE, fg=INK, font=(FONT, 10),
                         readonlybackground=WHITE, relief="solid", bd=1,
                         highlightbackground="#e8dcd9", highlightthickness=1)
    elif isinstance(widget, tk.Text):
        widget.configure(bg=WHITE, fg=INK, font=(FONT, 10),
                         relief="solid", bd=1, padx=8, pady=5)
    elif isinstance(widget, tk.Button):
        widget.configure(bg=SAGE, fg=INK, activebackground="#c6dfcb",
                         activeforeground=INK, font=(FONT, 9), relief="flat",
                         bd=0, padx=9, pady=4, cursor="hand2")
    for child in widget.winfo_children():
        paint_widget(child)


# ==============================
# うさぎデータを読み込む
# ==============================

def load_rabbits():
    if os.path.exists(RABBIT_FILE):
        with open(RABBIT_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


# ==============================
# 食事・ケアデータを読み込む
# ==============================

def load_foods():
    if os.path.exists(FOOD_FILE):
        with open(FOOD_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


# ==============================
# 食事記録を読み込む
# ==============================

def load_meal_records():
    if os.path.exists(MEAL_FILE):
        with open(MEAL_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    return []


# ==============================
# 食事記録を保存する
# ==============================

def save_meal_records():
    with open(MEAL_FILE, "w", encoding="utf-8") as file:
        json.dump(
            meal_records,
            file,
            ensure_ascii=False,
            indent=4
        )


def rabbits_for_daily_entry(all_rabbits):
    """マスターには残し、毎日の入力だけから対象外のうさぎを除く。"""
    return [
        rabbit for rabbit in all_rabbits
        if "🌈" not in str(rabbit.get("note") or "")
        and "販" not in str(rabbit.get("note") or "")
    ]


rabbits = rabbits_for_daily_entry(load_rabbits())
foods = load_foods()
meal_records = load_meal_records()

current_index = 0
displayed_context = None
displayed_values = None
displayed_is_template = False


# ==============================
# 食事・ケアの一覧を作る
# ==============================

care_items = []

for food in foods:
    if food["active"]:
        care_items.append(food["name"])


# ==============================
# 食事・ケア入力欄
# ==============================

care_rows_frame = None
care_count = 0
care_rows = []


def add_care_item():

    global care_count

    care_count += 1

    row_frame = tk.Frame(care_rows_frame)

    row_frame.pack(
        pady=2
    )

    # 項目番号
    number_label = tk.Label(
        row_frame,
        text=f"{care_count}：",
        font=("Arial", 11),
        width=4,
        anchor="w"
    )

    number_label.pack(
        side="left"
    )

    # 食事・ケア選択
    care_var = tk.StringVar()
    care_var.set("選択してください")

    care_combo = ttk.Combobox(
        row_frame,
        textvariable=care_var,
        values=care_items,
        state="readonly",
        font=("Arial", 11),
        width=22
    )

    care_combo.pack(
        side="left",
        padx=4
    )

    # 量・単位
    amount_var = tk.StringVar()

    amount_entry = tk.Entry(
        row_frame,
        textvariable=amount_var,
        font=("Arial", 11),
        width=11
    )

    amount_entry.pack(
        side="left",
        padx=4
    )

    remove_button = tk.Button(
        row_frame,
        text="削除",
        font=("Arial", 9),
        command=lambda frame=row_frame: remove_care_item(frame)
    )
    remove_button.pack(side="left", padx=2)

    # 保存用に記録
    care_rows.append({
        "item": care_var,
        "amount": amount_var,
        "frame": row_frame,
        "number_label": number_label
    })
    paint_widget(row_frame)


def remove_care_item(frame):
    """このうさぎの入力欄から選んだ項目だけを削除する。"""
    global care_count
    for row in care_rows:
        if row["frame"] == frame:
            care_rows.remove(row)
            frame.destroy()
            break
    care_count = len(care_rows)
    for number, row in enumerate(care_rows, 1):
        row["number_label"].config(text=f"{number}：")
    if not care_rows:
        add_care_item()


def current_values():
    return (
        tuple((row["item"].get(), row["amount"].get()) for row in care_rows),
        total_amount_var.get(),
        memo_text.get("1.0", tk.END).strip()
    )


def parse_record_date(value):
    try:
        return datetime.strptime(value, "%Y/%m/%d").date()
    except (ValueError, TypeError):
        return None


def find_record(rabbit_id, day, meal_time):
    """同じ日の記録があればそれを、なければそのうさぎの直前の記録を返す。"""
    for record in reversed(meal_records):
        if (record.get("rabbit_id") == rabbit_id
                and record.get("date") == day
                and record.get("meal_time") == meal_time):
            return record, False

    target = parse_record_date(day)
    if target is None:
        return None, False
    candidates = []
    for record in meal_records:
        recorded = parse_record_date(record.get("date"))
        if record.get("rabbit_id") != rabbit_id or recorded is None:
            continue
        # 同じ日の「あさ」を入力した後の「よる」も前回として利用する。
        order = 0 if record.get("meal_time") == "あさ" else 1
        target_order = 0 if meal_time == "あさ" else 1
        if (recorded, order) < (target, target_order):
            candidates.append((recorded, order, record))
    if not candidates:
        return None, False
    return max(candidates, key=lambda item: (item[0], item[1]))[2], True


def show_record():
    """前のうさぎの欄を消してから、選択中のうさぎの記録を表示する。"""
    global care_count, displayed_context, displayed_values, displayed_is_template
    for row in care_rows:
        row["frame"].destroy()
    care_rows.clear()
    care_count = 0

    total_amount_var.set("")
    memo_text.delete("1.0", tk.END)
    record = None
    copied = False
    if rabbits:
        rabbit = rabbits[current_index]
        record, copied = find_record(rabbit["id"], date_var.get(), meal_time_var.get())
        displayed_context = (rabbit["id"], date_var.get(), meal_time_var.get())
    else:
        displayed_context = None

    if record:
        for care in record.get("care", []):
            add_care_item()
            care_rows[-1]["item"].set(care.get("item", ""))
            care_rows[-1]["amount"].set(care.get("amount", ""))
        total_amount_var.set(record.get("total_amount", ""))
        memo_text.insert("1.0", record.get("memo", ""))
    if not care_rows:
        add_care_item()
    displayed_values = current_values()
    displayed_is_template = copied
    if copied:
        source_label_var.set(f"前回（{record['date']} {record['meal_time']}）の内容を表示中")
    elif record:
        source_label_var.set("この日の保存済み記録を表示中")
    else:
        source_label_var.set("このうさぎの記録はまだありません")


def save_if_changed():
    # 前回分をコピーした日は、変更がなくても今日の記録として保存する。
    if displayed_context and (displayed_is_template or current_values() != displayed_values):
        return save_record(use_displayed_context=True)
    return True


def change_day_or_meal_time(event=None):
    if displayed_context is None:
        return
    if (date_var.get(), meal_time_var.get()) == displayed_context[1:]:
        return
    if not save_if_changed():
        date_var.set(displayed_context[1])
        meal_time_var.set(displayed_context[2])
        return
    show_record()


def open_calendar():
    """標準ライブラリだけで使える日付選択用のカレンダー。"""
    selected = parse_record_date(date_var.get()) or date.today()
    picker = tk.Toplevel(root)
    picker.title("日付を選択")
    picker.resizable(False, False)
    picker.configure(bg=BG)
    picker.transient(root)
    picker.grab_set()

    month = [selected.year, selected.month]
    body = tk.Frame(picker, padx=12, pady=10)
    body.pack()

    def choose(day):
        date_var.set(day.strftime("%Y/%m/%d"))
        picker.destroy()
        change_day_or_meal_time()

    def move_month(offset):
        year, number = month
        number += offset
        if number == 0:
            year, number = year - 1, 12
        elif number == 13:
            year, number = year + 1, 1
        month[:] = [year, number]
        draw()

    def draw():
        for widget in body.winfo_children():
            widget.destroy()
        header = tk.Frame(body)
        header.pack(fill="x")
        tk.Button(header, text="◀", command=lambda: move_month(-1)).pack(side="left")
        tk.Label(header, text=f"{month[0]}年 {month[1]}月", width=16,
                 font=("Arial", 12, "bold")).pack(side="left")
        tk.Button(header, text="▶", command=lambda: move_month(1)).pack(side="left")
        grid = tk.Frame(body)
        grid.pack(pady=6)
        for column, label in enumerate(("月", "火", "水", "木", "金", "土", "日")):
            tk.Label(grid, text=label, width=4).grid(row=0, column=column)
        for row, week in enumerate(calendar.monthcalendar(*month), 1):
            for column, number in enumerate(week):
                if number:
                    day = date(month[0], month[1], number)
                    tk.Button(grid, text=str(number), width=3,
                              command=lambda value=day: choose(value)).grid(row=row, column=column)
        tk.Button(body, text="今日", command=lambda: choose(date.today())).pack(pady=2)
        paint_widget(body)

    draw()


# ==============================
# うさぎを表示
# ==============================

def update_rabbit():

    global current_index

    if len(rabbits) == 0:

        rabbit_name_var.set(
            "うさぎが登録されていません"
        )

        rabbit_id_var.set("")
        gender_var.set("")

        progress_var.set(
            "現在：0 / 0羽"
        )
        show_record()
        return

    rabbit = rabbits[current_index]

    rabbit_name_var.set(
        rabbit["name"]
    )

    rabbit_id_var.set(
        rabbit["id"]
    )

    gender_var.set(
        rabbit["gender"]
    )

    progress_var.set(
        f"現在：{current_index + 1} / {len(rabbits)}羽"
    )

    # 最初のうさぎ
    if current_index == 0:
        previous_button.config(
            state="disabled"
        )
    else:
        previous_button.config(
            state="normal"
        )

    # 最後のうさぎ
    if current_index == len(rabbits) - 1:
        next_button.config(
            state="disabled"
        )
    else:
        next_button.config(
            state="normal"
        )
    show_record()


# ==============================
# 名前を選択したとき
# ==============================

def select_rabbit(event=None):

    global current_index

    selected = rabbit_combo.current()
    if selected < 0 or selected == current_index:
        return
    if not save_if_changed():
        rabbit_name_var.set(rabbits[current_index]["name"])
        return
    current_index = selected
    update_rabbit()


# ==============================
# 次のうさぎ
# ==============================

def next_rabbit():

    global current_index

    if current_index < len(rabbits) - 1:
        if not save_if_changed():
            return
        current_index += 1

        update_rabbit()


# ==============================
# 前のうさぎ
# ==============================

def previous_rabbit():

    global current_index

    if current_index > 0:
        if not save_if_changed():
            return
        current_index -= 1

        update_rabbit()


# ==============================
# 保存
# ==============================

def save_record(use_displayed_context=False):

    if len(rabbits) == 0:
        return False

    day = displayed_context[1] if use_displayed_context else date_var.get()
    meal_time = displayed_context[2] if use_displayed_context else meal_time_var.get()
    try:
        datetime.strptime(day, "%Y/%m/%d")
    except ValueError:
        messagebox.showerror("入力を確認", "日付は 2026/09/24 の形式で入力してください。")
        return False
    total = total_amount_var.get().strip()
    try:
        if not total or not math.isfinite(float(total)) or float(total) < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("入力を確認", "与えた量の総量を0以上の数字で入力してください。")
        return False

    rabbit = rabbits[current_index]

    # 食事・ケアの入力内容を集める
    care_data = []

    for row in care_rows:

        item = row["item"].get()
        amount = row["amount"].get()

        if item != "選択してください" and item != "":
            care_data.append({
                "item": item,
                "amount": amount
            })

    # 1件の記録を作る
    record = {
        "rabbit_id": rabbit["id"],
        "rabbit_name": rabbit["name"],
        "date": day,
        "meal_time": meal_time,
        "care": care_data,
        "total_amount": total_amount_var.get(),
        "memo": memo_text.get("1.0", tk.END).strip()
    }

    # 同じうさぎ・同じ日付・同じ時間帯なら上書き
    updated = False

    for i, old_record in enumerate(meal_records):

        if (
            old_record["rabbit_id"] == rabbit["id"]
            and old_record["date"] == day
            and old_record["meal_time"] == meal_time
        ):
            meal_records[i] = record
            updated = True
            break

    # 新しい記録なら追加
    if not updated:
        meal_records.append(record)

    # ファイルに保存できなかった場合は画面を切り替えない。
    try:
        save_meal_records()
    except OSError as exc:
        messagebox.showerror("保存エラー", str(exc))
        return False
    global displayed_values, displayed_is_template
    displayed_values = current_values()
    displayed_is_template = False
    source_label_var.set("この日の保存済み記録を表示中")
    save_status_var.set(f"保存しました：{rabbit['name']}・{day} {meal_time}")

    print()
    print("✅ 保存しました！")
    print("うさぎID：", rabbit["id"])
    print("うさぎ：", rabbit["name"])
    print("日付：", day)
    print("時間帯：", meal_time)

    print("食事・ケア：")

    for item in care_data:
        print(
            "  ",
            item["item"],
            "：",
            item["amount"]
        )

    print(
        "与えた量の総量：",
        total_amount_var.get(),
        "g"
    )

    print(
        "MEMO：",
        memo_text.get("1.0", tk.END).strip()
    )

    print("💾 meal_records.json に保存しました")
    print()
    return True


# ==============================
# MEMOを日本語入力にする
# ==============================

def enable_japanese_input(event=None):

    try:

        hwnd = memo_text.winfo_id()

        imm32 = ctypes.windll.imm32

        h_imc = imm32.ImmGetContext(hwnd)

        if h_imc:
            imm32.ImmSetOpenStatus(h_imc, True)
            imm32.ImmReleaseContext(hwnd, h_imc)

    except Exception:
        pass


# ==============================
# 画面作成
# ==============================

root = tk.Tk()

root.title(
    "🐰 うさぎのごはん日記"
)

# 画面をコンパクトに
root.geometry(
    "680x620"
)
root.configure(bg=BG)

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TCombobox", font=(FONT, 10), padding=4,
                fieldbackground=WHITE, background="#f3dee3", foreground=INK)
style.map("TCombobox", fieldbackground=[("readonly", WHITE)],
          selectbackground=[("readonly", WHITE)],
          selectforeground=[("readonly", INK)])
root.option_add("*TCombobox*Listbox.font", (FONT, 10))


# ==============================
# タイトル
# ==============================

title_label = tk.Label(
    root,
    text="🐰 今日のごはん日記",
    font=("Arial", 20, "bold")
)

title_label.pack(
    pady=(10, 1)
)

subtitle_label = tk.Label(root, text="毎日の小さな記録を、ひとつずつ。")
subtitle_label.pack(pady=(0, 7))


# ==============================
# 日付
# ==============================

date_frame = tk.Frame(root)

date_frame.pack(
    pady=2
)

date_label = tk.Label(
    date_frame,
    text="日付：",
    font=("Arial", 12)
)

date_label.pack(
    side="left"
)

date_var = tk.StringVar()

date_entry = tk.Entry(
    date_frame,
    textvariable=date_var,
    font=("Arial", 12),
    width=13,
    state="readonly",
    readonlybackground="white"
)

date_entry.pack(
    side="left"
)

tk.Button(date_frame, text="📅 選ぶ", command=open_calendar).pack(side="left", padx=5)

date_var.set(
    date.today().strftime("%Y/%m/%d")
)


# ==============================
# あさ・よる
# ==============================

meal_time_frame = tk.Frame(root)

meal_time_frame.pack(
    pady=2
)

meal_time_label = tk.Label(
    meal_time_frame,
    text="食事：",
    font=("Arial", 12)
)

meal_time_label.pack(
    side="left"
)

meal_time_var = tk.StringVar()

meal_time_var.set("あさ")


morning_radio = tk.Radiobutton(
    meal_time_frame,
    text="あさ",
    variable=meal_time_var,
    value="あさ",
    font=("Arial", 12)
)

morning_radio.pack(
    side="left",
    padx=4
)


night_radio = tk.Radiobutton(
    meal_time_frame,
    text="よる",
    variable=meal_time_var,
    value="よる",
    font=("Arial", 12)
)

night_radio.pack(
    side="left",
    padx=4
)


# ==============================
# うさぎ
# ==============================

rabbit_frame = tk.Frame(root)

rabbit_frame.pack(
    pady=3
)

rabbit_label = tk.Label(
    rabbit_frame,
    text="うさぎ：",
    font=("Arial", 12)
)

rabbit_label.pack(
    side="left"
)

rabbit_name_var = tk.StringVar()

rabbit_combo = ttk.Combobox(
    rabbit_frame,
    textvariable=rabbit_name_var,
    font=("Arial", 12),
    state="readonly",
    width=16
)

rabbit_combo.pack(
    side="left",
    padx=4
)

rabbit_combo["values"] = [
    rabbit["name"]
    for rabbit in rabbits
]

rabbit_combo.bind(
    "<<ComboboxSelected>>",
    select_rabbit
)


# ==============================
# ID・性別
# ==============================

info_frame = tk.Frame(root)

info_frame.pack(
    pady=2
)


# ID
rabbit_id_label = tk.Label(
    info_frame,
    text="ID：",
    font=("Arial", 12)
)

rabbit_id_label.pack(
    side="left"
)

rabbit_id_var = tk.StringVar()

rabbit_id_display = tk.Label(
    info_frame,
    textvariable=rabbit_id_var,
    font=("Arial", 12)
)

rabbit_id_display.pack(
    side="left",
    padx=(0, 25)
)


# 性別
gender_label = tk.Label(
    info_frame,
    text="性別：",
    font=("Arial", 12)
)

gender_label.pack(
    side="left"
)

gender_var = tk.StringVar()

gender_display = tk.Label(
    info_frame,
    textvariable=gender_var,
    font=("Arial", 12)
)

gender_display.pack(
    side="left"
)


# ==============================
# 食事・ケア
# ==============================

care_title = tk.Label(
    root,
    text="✿ 食事・ケア",
    font=("Arial", 16, "bold")
)

care_title.pack(
    pady=(6, 3)
)


# 食事・ケア入力欄
care_rows_frame = tk.Frame(root)

care_rows_frame.pack(
    pady=1,
    anchor="center"
)


# 最初の入力欄
add_care_item()


# ==============================
# 項目追加ボタン
# ==============================

add_care_button = tk.Button(
    root,
    text="＋ 項目を追加",
    font=("Arial", 10),
    command=add_care_item
)

add_care_button.pack(
    pady=4
)


# ==============================
# 与えた量の総量
# ==============================

total_amount_frame = tk.Frame(root)

total_amount_frame.pack(
    pady=2
)

total_amount_label = tk.Label(
    total_amount_frame,
    text="与えた量の総量：",
    font=("Arial", 12)
)

total_amount_label.pack(
    side="left"
)


total_amount_var = tk.StringVar()

total_amount_entry = tk.Entry(
    total_amount_frame,
    textvariable=total_amount_var,
    font=("Arial", 12),
    width=8
)

total_amount_entry.pack(
    side="left",
    padx=3
)


total_unit_label = tk.Label(
    total_amount_frame,
    text="g",
    font=("Arial", 12)
)

total_unit_label.pack(
    side="left"
)


# ==============================
# MEMO
# ==============================

memo_title = tk.Label(
    root,
    text="✎ MEMO",
    font=("Arial", 16, "bold")
)

memo_title.pack(
    pady=(5, 2)
)


memo_text = tk.Text(
    root,
    font=("Arial", 12),
    width=55,
    height=2
)

memo_text.pack(
    padx=30,
    pady=2
)

memo_text.bind(
    "<FocusIn>",
    enable_japanese_input
)

source_label_var = tk.StringVar()
source_label = tk.Label(root, textvariable=source_label_var)
source_label.pack()

save_status_var = tk.StringVar()
save_status_label = tk.Label(root, textvariable=save_status_var)
save_status_label.pack()


# ==============================
# 進捗表示
# ==============================

progress_var = tk.StringVar()

progress_label = tk.Label(
    root,
    textvariable=progress_var,
    font=("Arial", 12)
)

progress_label.pack(
    pady=5
)


# ==============================
# 下のボタン
# ==============================

button_frame = tk.Frame(root)

button_frame.pack(
    pady=3
)


previous_button = tk.Button(
    button_frame,
    text="← 前のうさぎ",
    font=("Arial", 10),
    width=13,
    command=previous_rabbit
)

previous_button.pack(
    side="left",
    padx=3
)


save_button = tk.Button(
    button_frame,
    text="保存",
    font=("Arial", 10),
    width=10,
    command=save_record
)

save_button.pack(
    side="left",
    padx=3
)


next_button = tk.Button(
    button_frame,
    text="次のうさぎ →",
    font=("Arial", 10),
    width=13,
    command=next_rabbit
)

next_button.pack(
    side="left",
    padx=3
)


# ==============================
# 最初のうさぎを表示
# ==============================

paint_widget(root)
title_label.configure(font=(FONT, 18, "bold"), fg=ROSE)
subtitle_label.configure(font=(FONT, 9), fg=MUTED)
care_title.configure(font=(FONT, 13, "bold"), fg=ROSE)
memo_title.configure(font=(FONT, 13, "bold"), fg=ROSE)
rabbit_name_var.set("")
progress_label.configure(font=(FONT, 10, "bold"), fg=ROSE)
source_label.configure(font=(FONT, 9), fg=MUTED)
save_status_label.configure(font=(FONT, 9, "bold"), fg="#4b8061")
save_button.configure(bg=PINK, activebackground="#d98da3",
                      font=(FONT, 10, "bold"), pady=6)
previous_button.configure(pady=6)
next_button.configure(pady=6)
add_care_button.configure(bg="#f4dfdf", activebackground="#edc9d0")

update_rabbit()
morning_radio.config(command=change_day_or_meal_time)
night_radio.config(command=change_day_or_meal_time)


# ==============================
# 画面を表示
# ==============================

root.mainloop()
