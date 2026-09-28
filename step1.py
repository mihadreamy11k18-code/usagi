from datetime import date

print("🐰 うさぎ管理ソフト")
print("--------------------")

# うさぎの名前
name = input("うさぎの名前：")

# 日付
today = date.today()

# ごはん
food_plan = float(input("今日のごはん予定量（g）："))
food_eaten = float(input("実際に食べた量（g）："))

# 体調
condition = input("今日の体調（良好・普通・悪い）：")

# メモ
memo = input("気になったこと：")

print()
print("===== 今日の記録 =====")
print("日付：", today)
print("名前：", name)
print("ごはん予定量：", food_plan, "g")
print("実際に食べた量：", food_eaten, "g")
print("体調：", condition)
print("メモ：", memo)
print("====================")