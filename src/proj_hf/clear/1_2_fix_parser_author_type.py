"""
************************************

程式一_：從 https://huggingface.co/ 網站爬蟲各個作者的網站
根據作者隸屬於 [個人] 或者 [組織/公司]
將其結果存入 data/1_author.csv 的 [author_type] 欄位
[author_type] 欄位應為 'user' 或 'org'
假如出現 '找不到此作者' ，則要再另外補齊資料
假如origin_csv/hf_c.csv的資料已經做過清洗(沒有 '找不到此作者' )的紀錄
則不用再執行這支爬蟲程式

************************************
"""


import os
import time
import urllib.request
import pandas as pd
from tqdm import tqdm
from proj_hf.clear import clear
from proj_hf.get_root import get_root

def check_author_type_by_html(author_name):
    """
    完全偽裝成普通瀏覽器，直接抓取網頁 HTML 進行特徵比對。
    不需要 Token，不需要 huggingface_hub 套件！
    """
    url = f"https://huggingface.co/{author_name}"
    
    # 完美偽裝成 Chrome 瀏覽器標頭，防止被平台判定成 Python 爬蟲
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        # 設定 10 秒逾時
        with urllib.request.urlopen(req, timeout=10) as response:
            html_content = response.read().decode('utf-8')
            
            # ── 物理特徵判斷法 ──
            # 1. 如果網頁內含有 'organization' 或組織專屬標籤，通常是組織
            # 2. 如果包含 "Enterprise"、"company"、"non-profit" 也是組織
            if 'href="/organizations/' in html_content or '"type":"org"' in html_content:
                return 'org'
            elif 'company' in html_content or 'non-profit' in html_content or 'university' in html_content:
                return 'org'
            elif '"type":"user"' in html_content or 'contributions' in html_content:
                return 'user'
            else:
                # 如果兩邊特徵都有點模糊，預設歸類為個人，或至少不是錯誤
                return 'user'
                
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return '找不到此作者'
        elif e.code == 429:
            print(f"\n⚠️ 點擊太快，被網頁暫時限制，請等待 10 秒...")
            time.sleep(10)
            return '連線失敗'
        else:
            return f'HTTP錯誤({e.code})'
    except Exception as e:
        return '連線失敗'

def extract_authors_other(input_path):
    print("===== 🌟 步驟 2: 開始啟用 [物理外掛網頁特徵比對法] =====")
    
    if not os.path.exists(input_path):
        print(f"❌ 錯誤：找不到原始檔案 {input_path}")
        return

    df = pd.read_csv(input_path)
    
    if 'author_type' not in df.columns:
        # 如果原本沒這欄，直接初始化為字串型態
        df['author_type'] = None
        df['author_type'] = df['author_type'].astype(object)
    else:
        # 如果原本就有這欄（但可能全是空的而被誤判為 float64），強制轉換成 object (字串) 型態
        df['author_type'] = df['author_type'].astype(object)
    
    print("正在透過模擬瀏覽器分析作者類型...")

    # 使用 tqdm 顯示進度
    for index, row in tqdm(df.iterrows(), total=len(df)):
        # 中斷續爬：如果已經有正確分類，就直接跳過
        if pd.notna(row['author_type']) and row['author_type'] in ['個人', '組織/公司', '找不到此作者']:
            continue
            
        author_name = row['author_name']
        
        # 執行網頁暴力比對
        result = check_author_type_by_html(author_name)
        df.at[index, 'author_type'] = result
        
        # 模擬人類瀏覽網頁的速度，冷卻 0.6 秒
        time.sleep(0.6)
        
        # 每處理 10 筆存檔一次
        if index % 10 == 0:
            df.to_csv(input_path, index=False, encoding='utf-8-sig')

    # 最後完整存檔
    df.to_csv(input_path, index=False, encoding='utf-8-sig')
    print(f"\n🎉 任務徹底完成！結果已儲存至：{input_path}")

if __name__ == '__main__':
    clear()
    root = get_root()
    input_path = root / 'data' / '1_author.csv'

    extract_authors_other(input_path)
