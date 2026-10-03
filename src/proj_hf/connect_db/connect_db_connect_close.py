#  ********************************************
#  *
#  * connect/close實作：
#  * 要另外寫connect/close的動作，並執行connect/close來開啟/關閉連線
#  * 連線會一直維持打開狀態，最後再關就行
#  * 還要另外寫__enter__ 與 __exit__ 做資源管理，確保斷線後釋放所有資源
#  * 缺點：會一直占用資源
#  * 適合後端「常駐」服務、網頁 API 後端服務
#  *
#  ********************************************


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
        
        使用時配合 with 底下一併做縮排  
        with db_(uu, pp, "weather", "127.0.0.1", 3306) as w:
    """

    def __init__(self, user, password, database, host="127.0.0.1", port=3306):
        self.config = {
            "user": user,
            "password": password,
            "database": database,
            "host": host,
            "port": port   
        }
        self.conn = None    # 使用self，把連線變成其他def也能接過來用的長期連線
        self.cursor = None # 使用self，把游標變成其他def也能接過來用的長期游標
        

    def print_config(self):
        print(self.config)


    """測試&啟用長期連線"""
    def connect_db(self):
        print("\n\n=============================")
        print("開啟連線...")
        try:
            self.conn = mariadb.connect(**self.config)
            self.cursor = self.conn.cursor()
            print("✅ MariaDB 原生驅動連線成功！")
                
        except mariadb.Error as e:
            print(f"❌ 連線或查詢失敗：{e}")
            sys.exit(1)


    """手動關閉連線"""
    def close(self):
        if self.cursor:
            self.cursor.close()
            self.cursor = None   # 清空
        if self.conn:
            self.conn.close()
            self.conn = None    # 清空

        print("\n\n=============================")
        print("🔒 連線已安全關閉。")


    """進入with環境"""
    def __enter__(self):
        print("➡️ 進入 with 環境，自動開啟資料庫連線...")
        self.connect_db()  # 呼叫你原本寫好的開啟連線方法
        return self  # 👈 務必回傳 self，這樣外部才能用 'as w' 接收物件


    """離開with環境"""
    def __exit__(self, exc_type, exc_val, exc_tb):
        print("⬅️ 準備離開 with 環境，正在執行清理善後...")

        # 檢查是否有錯誤發生
        if exc_type is not None:
            print(f"⚠️ 注意：with 內部執行 SQL 時發生了錯誤！")
            print(f"錯誤類型: {exc_type}, 錯誤內容: {exc_val}")
            # 如果是資料庫操作出錯，可在這裡強制 rollback
            if self.conn:
                self.conn.rollback()

        # 無論有沒有錯，都一定要關閉連線
        self.close()  # 呼叫close方法

        # 回傳 False：讓 with 內部的錯誤照常拋出，方便主程式除錯
        # 若想吞掉錯誤改寫 return True
        return False

    
    """處理SELECT"""
    def select(self, sql, *args):
        print("\n\n=============================")
        print("使用SELECT查詢...")

        if not self.conn:
            print("❌ 錯誤：尚未建立連線，請先呼叫 connect_db()")
            return False
        
        with self.conn.cursor() as cursor:
            try:
                if not args:
                    cursor.execute(sql)
                else:
                    cursor.execute(sql, args)
                print("查詢結果如下\n")
                return cursor.fetchall()    # fetchall翻譯是拿所有東西，也就是查詢結果，所以需要return
            except mariadb.Error as e:
                print(f"❌ 查詢失敗：{e}")
                return None


    """處理INSERT、UPDATE、DELETE"""
    def execute(self, sql, *args):
            print("\n\n=============================")
            print("使用INSERT、UPDATE、DELETE語法...")

            if not self.conn:
                print("❌ 錯誤：尚未建立連線，請先呼叫 connect_db()")
                return False
            
            with self.conn.cursor() as cursor:
                try:
                    if not args:
                        cursor.execute(sql)
                    else:
                        cursor.execute(sql, args)
                    self.conn.commit()   # 新增、刪除、修改必須存檔才有用，所以要送出指令存檔的動作，存檔這個動作本身不需要return
                    print("執行完成")
                    return True     # 成功時回傳 True，讓主程式知道有成功寫入
                except mariadb.Error as e:
                    self.conn.rollback() # ❌ 發生錯誤就自動回滾，維持資料一致
                    print(f"❌ 執行失敗，已回滾：{e}")
                    return False


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

    # with db_(uu, pp, "weather", "127.0.0.1", 3306) as w:   # 連接db的基本資訊，帳號、密碼、db名稱、host、prot，完整版
    # with db_(userid=uu, database="weather", password=pp) as w:   # 連接db的基本資訊，因為host和prot有預設值，所以補上 帳號、密碼、db名稱 就行，順序可以亂擺，要做對應
    with db_(uu, pp, "weather") as w:  # 連接db的基本資訊，因為host和prot有預設值，所以補上 帳號、密碼、db名稱 就行，順序要正確
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


        # w.close() # 使用with以後，就不需要手動關閉連線了
