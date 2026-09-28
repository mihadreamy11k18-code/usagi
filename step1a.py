import json
import os


# ==============================
# 🐰 うさぎ管理ソフト
# STEP 1　うさぎマスター
# ==============================


# うさぎのデータを保存するファイル名
FILE_NAME = "rabbits.json"


# --------------------------------
# 保存されているデータを読み込む
# --------------------------------
def load_rabbits():

    # 保存ファイルが存在するか確認
    if os.path.exists(FILE_NAME):

        # ファイルを開く
        with open(FILE_NAME, "r", encoding="utf-8") as file:

            # 保存されているデータを読み込む
            return json.load(file)

    # ファイルがまだ存在しない場合
    return []


# --------------------------------
# うさぎのデータを保存する
# --------------------------------
def save_rabbits():

    with open(FILE_NAME, "w", encoding="utf-8") as file:

        # うさぎのデータを書き込む
        json.dump(
            rabbits,
            file,
            ensure_ascii=False,
            indent=4
        )


# --------------------------------
# うさぎを登録する
# --------------------------------
def add_rabbit():

    print()
    print("🐰 うさぎを登録します")
    print("--------------------")

    rabbit_id = input("うさぎID：")
    name = input("名前：")
    gender = input("性別（オス・メス）：")
    birthday = input("誕生日（例：2022/05/10）：")
    breed = input("品種：")
    note = input("備考：")

    # 1羽分のデータを作る
    rabbit = {
        "id": rabbit_id,
        "name": name,
        "gender": gender,
        "birthday": birthday,
        "breed": breed,
        "note": note
    }

    # リストに追加
    rabbits.append(rabbit)

    # ★登録したらすぐ保存
    save_rabbits()

    print()
    print("✅ 登録しました！")
    print("💾 データを保存しました！")
    print()


# --------------------------------
# うさぎ一覧を表示
# --------------------------------
def show_rabbits():

    print()
    print("🐰 うさぎ一覧")
    print("--------------------")

    if len(rabbits) == 0:
        print("まだ登録されていません。")
        return

    for rabbit in rabbits:

        print(
            rabbit["id"],
            rabbit["name"],
            rabbit["gender"],
            rabbit["breed"]
        )

    print()


# --------------------------------
# IDからうさぎを検索
# --------------------------------
def search_rabbit():

    print()
    print("🔍 うさぎを検索します")
    print("--------------------")

    search_id = input("うさぎID：")

    for rabbit in rabbits:

        if rabbit["id"] == search_id:

            print()
            print("===== うさぎ情報 =====")
            print("ID：", rabbit["id"])
            print("名前：", rabbit["name"])
            print("性別：", rabbit["gender"])
            print("誕生日：", rabbit["birthday"])
            print("品種：", rabbit["breed"])
            print("備考：", rabbit["note"])
            print("====================")
            print()

            return

    print("そのIDのうさぎは登録されていません。")
    print()


# ==================================
# プログラム開始時にデータを読み込む
# ==================================

rabbits = load_rabbits()


# ==================================
# メインメニュー
# ==================================

while True:

    print("🐰 うさぎ管理ソフト")
    print("====================")
    print("1：うさぎを登録")
    print("2：うさぎ一覧を見る")
    print("3：うさぎを検索")
    print("4：終了")

    menu = input("番号を入力してください：")

    if menu == "1":
        add_rabbit()

    elif menu == "2":
        show_rabbits()

    elif menu == "3":
        search_rabbit()

    elif menu == "4":
        print("うさぎ管理ソフトを終了します。")
        break

    else:
        print("⚠️ 1～4の番号を入力してください。")
        print()
