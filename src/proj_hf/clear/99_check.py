"""
資料清洗，大數據全資料表空值與特徵動態檢查 (修正版)
"""

import pandas as pd
import os
from proj_hf.clear import clear
from proj_hf.get_root import get_root

def clean_and_check_table(file_path):
    # 真正把 CSV 檔案讀取進來變成 DataFrame
    df = pd.read_csv(file_path)

    # 取得檔案名稱，讓 log 看起來更漂亮
    file_name = os.path.basename(file_path)
    print(f"===== 🔍 開始檢查資料表: [{file_name}] =====")
    
    # 1. 檢查有沒有任何空值
    print("  👉 空值檢查：", df.isnull().sum().to_dict())

    # 2. 動態檢查：根據資料表擁有的欄位，印出分類分佈
    if 'author_type' in df.columns:
        print("  📊 作者類型分佈：", df['author_type'].value_counts().to_dict())
        
    elif 'pipeline_tag' in df.columns:
        print("  📊 任務分類前 5 名：", df['pipeline_tag'].value_counts().head(5).to_dict())
        
    elif 'hardware_tier' in df.columns:
        print("  📊 硬體部署規格分佈：", df['hardware_tier'].value_counts().to_dict())
        
    elif 'rolling_30d_dls' in df.columns:
        print("  📊 30 天滾動下載量統計概況 (前 3 筆)：\n", df[['model_id', 'rolling_30d_dls']].head(3).to_string(index=False))
    elif 'downloads' in df.columns:
        print("  📊 下載量統計概況 (前 3 筆)：\n", df[['model_id', 'downloads']].head(3).to_string(index=False))
        
    print("================================================\n")

if __name__ == '__main__':
    clear()  # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf

    # 定義所有資料表路徑
    csv_list = {
        1: 'data/1_dim_author.csv', 
        2: 'data/2_dim_pipeline_tag.csv', 
        3: 'data/3_dim_library.csv', 
        4: 'data/4_dim_model_table.csv', 
        6: 'data/6_fact_snapshot.csv',
        7: 'data/7_fact_model_totals.csv',
        9: 'data/9_dim_date.csv'
    }

    # 🌟 修正點一：使用 .items() 才能同時正確循環 key 與 path
    for key, path in csv_list.items():
        # 修正點二：確保檔案真的存在，避免中途斷掉
        if os.path.exists(path):
            clean_and_check_table(path)
        else:
            print(f"⚠️ 提示：找不到檔案 {path}，跳過檢查。\n")