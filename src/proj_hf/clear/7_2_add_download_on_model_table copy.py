"""
************************************

程式七：下載數和按讚數加回4_dim_model_table.csv

************************************
"""

import pandas as pd
from proj_hf.clear import clear
from proj_hf.get_root import get_root


def read_csv(path_in):
    try:
        df = pd.read_csv(path_in)
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到原始檔案，請確認路徑：{path_in}")
        return
    return df


def add_modified_table(totals_path, model_path, out_path):
    totals_df = read_csv(totals_path)
    model_df = read_csv(model_path)
    if totals_df is None or model_df is None:
        return

    required_totals_cols = ['model_id', 'total_likes', 'totle_dls']
    required_model_cols = ['model_id']
    missing_totals_cols = [col for col in required_totals_cols if col not in totals_df.columns]
    missing_model_cols = [col for col in required_model_cols if col not in model_df.columns]
    if missing_totals_cols or missing_model_cols:
        print(
            "⚠️ 警告：原始檔案缺少必要欄位，"
            f"7_fact_model_totals.csv: {missing_totals_cols}；"
            f"4_dim_model_table.csv: {missing_model_cols}。"
        )
        return

    if model_df['model_id'].isna().any() or totals_df['model_id'].isna().any():
        print("⚠️ 警告：model_id 含有空值，未輸出資料。")
        return

    if model_df['model_id'].duplicated().any() or totals_df['model_id'].duplicated().any():
        print("⚠️ 警告：model_id 有重複值，無法保證一對一合併，未輸出資料。")
        return

    metric_cols = ['total_likes', 'totle_dls']
    model_df = model_df.drop(columns=metric_cols, errors='ignore')
    modified_df = model_df.merge(
        totals_df[['model_id', *metric_cols]],
        on='model_id',
        how='left',
        validate='one_to_one'
    )

    unmatched = modified_df[metric_cols].isna().any(axis=1)
    if unmatched.any():
        print(f"⚠️ 警告：有 {unmatched.sum()} 個 model_id 找不到對應的下載或按讚總數。")

    modified_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    
    print("🎉 [快照資料表] 建立成功！")
    print(f"📁 檔案已儲存為：{out_path}")
    print(f"📊 總共成功更新了 {len(modified_df)} 筆模型資料。")
    print("\n👀 產出的資料前 5 筆範例：")
    print(modified_df.head())

if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定原始檔案與輸出檔案的完整路徑
    totals_path = root / 'data' / '7_fact_model_totals.csv'
    model_path = root / 'data' / '4_dim_model_table.csv'
    out_path = root / 'data' / '4_dim_model_table.csv'
    


    # 2. 呼叫函數並把路徑傳進去
    add_modified_table(totals_path, model_path, out_path)