#  ********************************************
#  *
#  * with實作：
#  * 一次完成  [連線] - [查詢/執行語法] - [關閉連線]  所有動作
#  * 缺點：寫每個動作，乃至後面每一次查詢，都會重新連線
#  * 網路延遲高的情況下更容易有效能開銷大的問題在
#  * 適合單次查詢，快閃執行
#  *
#  ********************************************

import contextlib  # 👈 引入 contextlib 模組，確保連線關閉
import mariadb
import os
import subprocess
import sys


def clear():
    _ = subprocess.run('cls' if os.name == 'nt' else 'clear', shell=True)    # 清除螢幕的魔法
    print("--- 呼叫螢幕清除魔法 ---\n\n")
    return


class db_:
    """ 連接到 mariadb 的實作。  
        db_("id", "password", "db_name", "127.0.0.1", 3306)  ✅預設順序  
        db_("id", "password", "db_name")  ✅預設順序，host和port有預設值，所以可省略  
        db_(database="db_name", password="password", user="id")  ✅引數和參數有做對應就能無視順序  
    """

    def __init__(self, user, password, database, host="127.0.0.1", port=3306):
        self.config = {
            "user": user,
            "password": password,
            "database": database,
            "host": host,
            "port": port   
        }
        

    def print_config(self):
        print(self.config)


    """測試連線"""
    def connect_db(self):
        print("\n\n=============================")
        print("連線測試...")
        try:
            with contextlib.closing(mariadb.connect(**self.config)) as conn:
                with conn.cursor() as self.cursor:
                    print("✅ MariaDB 原生驅動連線成功！\n")
                    return True
        except mariadb.Error as e:
            print(f"❌ 連線或查詢失敗：{e}")
            # sys.exit(1) 這會強制關閉整個程式，實際上沒必要這麼做
            return False


    """處理SELECT"""
    def select(self, sql, *args):
        print("\n\n=============================")
        print("使用SELECT查詢...")
        try:
            with mariadb.connect(**self.config) as conn:
                with conn.cursor() as cursor:
                    if not args:
                        cursor.execute(sql)
                    else:
                        cursor.execute(sql, args)
                    print("查詢結果如下\n")
                    return cursor.fetchall()    # fetchall翻譯是拿所有東西，也就是查詢結果，所以需要return
        except mariadb.Error as e:
            print(f"❌ 連線或查詢失敗：{e}\n")
            return None


    """處理INSERT、UPDATE、DELETE"""
    def execute(self, sql, *args):
            print("\n\n=============================")
            print("使用INSERT、UPDATE、DELETE語法...")
            try:
                with contextlib.closing(mariadb.connect(**self.config)) as conn:
                    with conn.cursor() as cursor:
                        if not args:
                            cursor.execute(sql)
                        else:
                            cursor.execute(sql, args)
                        conn.commit()   # 新增、刪除、修改必須存檔才有用，所以要送出指令存檔的動作，存檔這個動作本身不需要return
                        print("執行完成")
                        return True
            except mariadb.Error as e:
                print(f"❌ 連線或查詢失敗：{e}\n")
                return False  # 👈 失敗時回傳 False


# ---------------------------------------------------------------
# ---------------------------------------------------------------


# 只有在滑鼠雙擊或單獨執行 這支程式 時才會跑這裡
if __name__ == "__main__":
    clear()
    print("=============================")
    print("--- 正在單獨測試副程式功能 ---")

   
# ---------------------------------------------------------------
# ---------------------------------------------------------------


    # 這是用來登入maria db的帳號密碼
    uu = "root"
    pp = "root"

    # w = db_(uu, pp, "weather", "127.0.0.1", 3306)   # 連接db的基本資訊，帳號、密碼、db名稱、host、prot，完整版
    # w = db_(userid=uu, database="weather", password=pp)   # 連接db的基本資訊，因為host和prot有預設值，所以補上 帳號、密碼、db名稱 就行，順序可以亂擺，要做對應
    w = db_(uu, pp, "weather")   # 連接db的基本資訊，因為host和prot有預設值，所以補上 帳號、密碼、db名稱 就行，順序要正確
    w.connect_db()  # 測試連線


# ---------------------------------------------------------------
# ---------------------------------------------------------------


    # 查詢測試1  
    sql1 = f"SELECT * FROM account"
    queue = w.select(sql1)

    # 印出查詢結果
    for (id, username, password, mail, create_time) in queue:
            print(f"| id:  {id}   | 帳號:  {username}   | 密碼:  {password}   | mail:  {mail}   | 時間:  {create_time}")

    # clear()



# ---------------------------------------------------------------
# ---------------------------------------------------------------


    # 查詢測試2
    id = "user01"
    password = "0000"

    sql2 = "SELECT * FROM account WHERE USERNAME = %s AND PASSWORD = %s"
    queue = w.select(sql2, id, password)
    
    for (id, username, password, mail, create_time) in queue:
        print(f"| id:  {id}   | 帳號:  {username}   | 密碼:  {password}   | mail:  {mail}   | 時間:  {create_time}")
    
    
