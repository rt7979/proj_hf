"""
************************************

程式三：導出函式庫表格
欄位名稱[library_name、library_type、base_framework]
將結果存入data/3_library.csv
其中library_type欄位只有public / custom
public：完全原生且開放的函式庫，或者經由原生的函式庫衍生，但也是完全開放大眾化，屬於 公開/通用 的函式庫
custom：因應特殊任務，將public微調，且非通用模型，屬於 私有/客製 的函式庫，下載量較低

************************************
"""


import pandas as pd
from proj_hf.clear import clear
from proj_hf.get_root import get_root

def create_library_table(input_path, out_path):
    """
    讀取原始 CSV，提取 函式庫 資訊並匯出
    """
    # 【核心修正 1】在函數內部，用傳進來的 input_path 讀取 CSV 檔案
    try:
        df = pd.read_csv(input_path)
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到原始檔案，請確認路徑：{input_path}")
        return

    # 2. 檢查欄位是否存在
    required_cols = ['library_name', 'library_type', 'base_framework']
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
            print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}，請確認欄位名稱是否正確。")
    else:
        # 3. 提取不重複的函式庫組合，並依函式庫名稱排序
        library_df = (
            df[required_cols]
            .drop_duplicates()
            .dropna(subset=['library_name'])
            .sort_values(by='library_name', key=lambda s: s.str.lower())
            .reset_index(drop=True)
        )
        
        # 4. 依排序後的順序，自動生成主鍵 lib_id，格式為 lib001、lib002...
        library_df.insert(0, 'library_id', [f'lib{idx:03d}' for idx in range(1, len(library_df) + 1)])
        
        # 【核心修正 3】改用參數傳進來的 out_path 儲存檔案，不再寫死
        library_df.to_csv(out_path, index=False, encoding='utf-8-sig')
        
        print(f"🎉 [函式庫csv] 還原成功！")
        print(f"📁 檔案已儲存為：{out_path}")
        print(f"📊 總共成功提取了 {len(library_df)} 組不重複的函式庫資料。")
        
        # 顯示前 5 筆資料讓你確認外觀
        print("\n👀 產出的資料前 5 筆範例：")
        print(library_df.head())


if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定原始檔案與輸出檔案的完整路徑
    input_path = root / 'data' / 'origin_csv' / 'hf_c.csv'
    out_path = root / 'data' / '3_dim_library.csv'
    
    # 2. 呼叫函數並把路徑傳進去
    create_library_table(input_path, out_path)