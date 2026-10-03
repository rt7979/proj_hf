from connect_db_with import clear, db_

# 只有在滑鼠雙擊或單獨執行 這支程式 時才會跑這裡
if __name__ == "__main__":
    clear()
    print("=============================")
    print("--- 正在單獨測試程式功能 ---")


# ---------------------------------------------------------------
# ---------------------------------------------------------------


    # 這是用來登入maria db的帳號密碼
    uu = "root"
    pp = "root"

    w = db_(uu, pp, "weather")
    w.connect_db()  # 測試/開啟連線


# ---------------------------------------------------------------
# ---------------------------------------------------------------


    # 查詢測試1  
    sql1 = f"SELECT * FROM account"
    queue = w.select(sql1)

    # 印出查詢結果
    for (id, username, password, mail, create_time) in queue:
            print(f"| id:  {id}   | 帳號:  {username}   | 密碼:  {password}   | mail:  {mail}   | 時間:  {create_time}")


# ---------------------------------------------------------------
# ---------------------------------------------------------------


    # 查詢測試2
    id = "user01"
    password = "0000"

    sql2 = "SELECT * FROM account WHERE USERNAME = %s AND PASSWORD = %s"
    queue = w.select(sql2, id, password)
    
    for (id, username, password, mail, create_time) in queue:
        print(f"| id:  {id}   | 帳號:  {username}   | 密碼:  {password}   | mail:  {mail}   | 時間:  {create_time}")
