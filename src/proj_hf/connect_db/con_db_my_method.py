import mariadb
import os
import subprocess
import sys


def clear():
    _ = subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)    # 清除螢幕的魔法
    return


def connect_mariadb():
    return


class db_:
    def __init__(self, userid, password, database, host="127.0.0.1", port=3306):
        self.config = {
            "user": userid,
            "password": password,
            "database": database,
            "host": host,
            "port": port   
        }
        

    def print_config(self):
        print(self.config)


    """測試連線"""
    def connect_db(self):
        try:
            with mariadb.connect(**self.config) as conn:
                with conn.cursor() as self.cursor:
                    print("✅ MariaDB 原生驅動連線成功！")
                
        except mariadb.Error as e:
            print(f"❌ 連線或查詢失敗：{e}")
            sys.exit(1)


    """處理SELECT"""
    def select(self, sql, *args):
        
        try:
            with mariadb.connect(**self.config) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql, args)
                    return cursor.fetchall()    # fetchall翻譯是拿所有東西，也就是查詢結果，所以需要return
        except mariadb.Error as e:
            print(f"❌ 連線或查詢失敗：{e}")
            sys.exit(1)


    """處理INSERT、UPDATE、DELETE"""
    def execute(self, sql, *args):
            try:
                with mariadb.connect(**self.config) as conn:
                    with conn.cursor() as cursor:
                        if not args:
                            cursor.execute(sql)
                        else:
                            cursor.execute(sql, args)
                        conn.commit()   # 新增、刪除、修改必須存檔才有用，所以要送出指令存檔的動作，存檔這個動作本身不需要return
            except mariadb.Error as e:
                print(f"❌ 連線或查詢失敗：{e}")
                sys.exit(1)



# 只有在滑鼠雙擊或單獨執行 這支程式 時才會跑這裡
if __name__ == "__main__":
    print("--- 正在單獨測試副程式功能 ---")
    clear()
    print("--- 呼叫螢幕清除魔法 ---")


# ---------------------------------------------------------------
# ---------------------------------------------------------------

    print()
    print("=============================")


    # 這是用來登入maria db的帳號密碼
    uu = "root"
    pp = "root"

    # w = db_(uu, pp, "weather", "127.0.0.1", 3306)   # 連接db的基本資訊，帳號、密碼、db名稱、host、prot，完整版
    # w = db_(userid=uu, database="weather", password=pp)   # 連接db的基本資訊，因為host和prot有預設值，所以補上 帳號、密碼、db名稱 就行，順序可以亂擺，要做對應
    w = db_(uu, pp, "weather")   # 連接db的基本資訊，因為host和prot有預設值，所以補上 帳號、密碼、db名稱 就行，順序要正確
    w.connect_db()  # 測試連線


# ---------------------------------------------------------------
# ---------------------------------------------------------------

    print()
    print("=============================")


    # 查詢測試1  
    sql1 = f"SELECT * FROM account"
    queue = w.select(sql1)

    # 印出查詢結果
    for (id, username, password, mail, create_time) in queue:
            print(f"| id:  {id}   | 帳號:  {username}   | 密碼:  {password}   | mail:  {mail}   | 時間:  {create_time}")

    # clear()



# ---------------------------------------------------------------
# ---------------------------------------------------------------

    print()
    print("=============================")

    # 查詢測試2
    id = "user01"
    password = "0000"

    sql2 = "SELECT * FROM account WHERE USERNAME = %s AND PASSWORD = %s"
    queue = w.select(sql2, id, password)
    
    for (id, username, password, mail, create_time) in queue:
        print(f"| id:  {id}   | 帳號:  {username}   | 密碼:  {password}   | mail:  {mail}   | 時間:  {create_time}")
    
    
