import json
import os

# ==============================
# 🐰 うさぎ管理ソフト
# STEP 2　食事・ケアマスター
# ==============================

FILE_NAME = "foods.json"


# ------------------------------
# データを読み込む
# ------------------------------
def load_foods():
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            return json.load(file)

    return []


# ------------------------------
# データを保存する
# ------------------------------
def save_foods():
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(
            foods,
            file,
            ensure_ascii=False,
            indent=4
        )


# ------------------------------
# 食事・ケアを登録する
# ------------------------------
def add_food():
    print()
    print("🍚 食事・ケアを登録します")
    print("--------------------")

    food_id = input("食事・ケアID：")
    name = input("名前：")
    category = input("分類（主・トッピング・薬）：")

    food = {
        "id": food_id,
        "name": name,
        "category": category,
        "active": True
    }

    foods.append(food)
    save_foods()

    print()
    print("✅ 登録しました！")
    print("💾 データを保存しました！")
    print()


# ------------------------------
# 食事・ケア一覧を見る
# ------------------------------
def show_foods():
    print()
    print("🍚 食事・ケア一覧")
    print("--------------------")

    if len(foods) == 0:
        print("まだ登録されていません。")
        print()
        return

    for food in foods:
        if food["active"]:
            print(
                food["id"],
                food["name"],
                "【" + food["category"] + "】"
            )

    print()


# ------------------------------
# 食事・ケアを検索する
# ------------------------------
def search_food():
    print()
    print("🔍 食事・ケアを検索します")
    print("--------------------")

    search_id = input("食事・ケアID：")

    for food in foods:
        if food["id"] == search_id:
            print()
            print("===== 食事・ケア情報 =====")
            print("ID：", food["id"])
            print("名前：", food["name"])
            print("分類：", food["category"])

            if food["active"]:
                print("状態：使用中")
            else:
                print("状態：使用していません")

            print("========================")
            print()
            return

    print("そのIDの食事・ケアは登録されていません。")
    print()


# ------------------------------
# 食事・ケアを変更する
# ------------------------------
def edit_food():
    print()
    print("✏️ 食事・ケアを変更します")
    print("--------------------")

    search_id = input("変更する食事・ケアID：")

    for food in foods:
        if food["id"] == search_id:

            print()
            print("現在の情報")
            print("名前：", food["name"])
            print("分類：", food["category"])
            print()

            new_name = input(
                "新しい名前（変更しない場合はEnter）："
            )

            new_category = input(
                "新しい分類（変更しない場合はEnter）："
            )

            if new_name != "":
                food["name"] = new_name

            if new_category != "":
                food["category"] = new_category

            save_foods()

            print()
            print("✅ 変更しました！")
            print("💾 データを保存しました！")
            print()

            return

    print("そのIDの食事・ケアは登録されていません。")
    print()


# ------------------------------
# 食事・ケアを使用しない状態にする
# ------------------------------
def delete_food():
    print()
    print("🗑️ 食事・ケアを使用しない状態にします")
    print("--------------------")

    search_id = input("使用しない食事・ケアID：")

    for food in foods:
        if food["id"] == search_id:

            food["active"] = False

            save_foods()

            print()
            print("✅ 使用しない状態にしました。")
            print("💾 データを保存しました！")
            print()

            return

    print("そのIDの食事・ケアは登録されていません。")
    print()


# ------------------------------
# メイン処理
# ------------------------------

foods = load_foods()

while True:

    print("🐰 食事・ケアマスター")
    print("====================")
    print("1：食事・ケアを登録")
    print("2：食事・ケア一覧を見る")
    print("3：食事・ケアを検索")
    print("4：食事・ケアを変更")
    print("5：食事・ケアを使用しない")
    print("6：終了")

    menu = input("番号を入力してください：")

    if menu == "1":
        add_food()

    elif menu == "2":
        show_foods()

    elif menu == "3":
        search_food()

    elif menu == "4":
        edit_food()

    elif menu == "5":
        delete_food()

    elif menu == "6":
        print("食事・ケアマスターを終了します。")
        break

    else:
        print("⚠️ 1～6の番号を入力してください。")
        print()