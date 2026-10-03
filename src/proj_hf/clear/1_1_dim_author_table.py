"""
************************************

程式一：從hf_c.csv導出作者維度表
欄位名稱[author_id、author_name、author_type]
將結果存入data/1_author.csv
假如hf_c.csv是完全未整理的資料，hf_c.csv根本沒有hf_c.csv欄位
作者表的[author_type]欄位預設都是空白，需要另外使用爬蟲補上

************************************
"""


import pandas as pd
from proj_hf.clear import clear
from proj_hf.get_root import get_root


def create_author_table(input_path, out_path):
    """
    讀取原始 CSV，提取作者資訊並匯出
    """
    # 【核心修正 1】在函數內部，用傳進來的 input_path 讀取 CSV 檔案
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到原始檔案，請確認路徑：{input_path}")
        return

    # 2. 檢查欄位是否存在
    required_cols = ['author', 'author_type']
    
    # 【核心修正 2】現在函數認識 df 了
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}，請確認欄位名稱是否正確。")
    else:
        # 3. 提取作者與作者類型，去除重複值，並依作者名稱英文字母排序
        author_df = (
            df[required_cols]
            .drop_duplicates()
            .dropna(subset=['author'])
            .sort_values(by='author', key=lambda s: s.str.lower())
            .reset_index(drop=True)
        )
        author_df = author_df.rename(columns={'author': 'author_name'})
        
        # 4. 依排序後的順序，自動生成主鍵 author_id，格式為 au0001、au0002...
        author_df.insert(0, 'author_id', [f'au{idx:04d}' for idx in range(1, len(author_df) + 1)])
        
        # 【核心修正 3】改用參數傳進來的 out_path 儲存檔案，不再寫死
        author_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        
        print(f"🎉 [作者csv] 還原成功！")
        print(f"📁 檔案已儲存為：{out_path}")
        print(f"📊 總共成功提取了 {len(author_df)} 位不重複的作者。")
        
        # 顯示前 5 筆資料讓你確認外觀
        print("\n👀 產出的資料前 5 筆範例：")
        print(author_df.head())


if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定原始檔案與輸出檔案的完整路徑
    input_path = root / 'data' / 'origin_csv' / 'hf_c.csv'
    out_path = root / 'data' / '1_dim_author.csv'
    
    # 2. 呼叫函數並把路徑傳進去
    create_author_table(input_path, out_path)