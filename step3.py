import json
import os
import tkinter as tk
from tkinter import ttk
from datetime import date
import ctypes


# ==============================
# データファイル
# ==============================

RABBIT_FILE = "rabbits.json"
FOOD_FILE = "foods.json"
MEAL_FILE = "meal_records.json"


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


rabbits = load_rabbits()
foods = load_foods()
meal_records = load_meal_records()

current_index = 0


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

    # 保存用に記録
    care_rows.append({
        "item": care_var,
        "amount": amount_var
    })


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


# ==============================
# 名前を選択したとき
# ==============================

def select_rabbit(event=None):

    global current_index

    selected_name = rabbit_name_var.get()

    for i, rabbit in enumerate(rabbits):

        if rabbit["name"] == selected_name:

            current_index = i

            rabbit_id_var.set(
                rabbit["id"]
            )

            gender_var.set(
                rabbit["gender"]
            )

            progress_var.set(
                f"現在：{current_index + 1} / {len(rabbits)}羽"
            )

            # 前のうさぎボタン
            if current_index == 0:
                previous_button.config(
                    state="disabled"
                )
            else:
                previous_button.config(
                    state="normal"
                )

            # 次のうさぎボタン
            if current_index == len(rabbits) - 1:
                next_button.config(
                    state="disabled"
                )
            else:
                next_button.config(
                    state="normal"
                )

            break


# ==============================
# 次のうさぎ
# ==============================

def next_rabbit():

    global current_index

    if current_index < len(rabbits) - 1:

        current_index += 1

        update_rabbit()


# ==============================
# 前のうさぎ
# ==============================

def previous_rabbit():

    global current_index

    if current_index > 0:

        current_index -= 1

        update_rabbit()


# ==============================
# 保存
# ==============================

def save_record():

    if len(rabbits) == 0:
        return

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
        "date": date_var.get(),
        "meal_time": meal_time_var.get(),
        "care": care_data,
        "total_amount": total_amount_var.get(),
        "memo": memo_text.get("1.0", tk.END).strip()
    }

    # 同じうさぎ・同じ日付・同じ時間帯なら上書き
    updated = False

    for i, old_record in enumerate(meal_records):

        if (
            old_record["rabbit_id"] == rabbit["id"]
            and old_record["date"] == date_var.get()
            and old_record["meal_time"] == meal_time_var.get()
        ):
            meal_records[i] = record
            updated = True
            break

    # 新しい記録なら追加
    if not updated:
        meal_records.append(record)

    # ファイルに保存
    save_meal_records()

    print()
    print("✅ 保存しました！")
    print("うさぎID：", rabbit["id"])
    print("うさぎ：", rabbit["name"])
    print("日付：", date_var.get())
    print("時間帯：", meal_time_var.get())

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
    "🐰 うさぎ管理ソフト"
)

# 画面をコンパクトに
root.geometry(
    "650x580"
)


# ==============================
# タイトル
# ==============================

title_label = tk.Label(
    root,
    text="今日の食事記録",
    font=("Arial", 20, "bold")
)

title_label.pack(
    pady=6
)


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
    width=13
)

date_entry.pack(
    side="left"
)

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
    text="食事・ケア",
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
    text="MEMO",
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

update_rabbit()


# ==============================
# 画面を表示
# ==============================

root.mainloop()