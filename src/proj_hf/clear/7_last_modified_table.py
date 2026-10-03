"""
************************************

程式七：所有模型最後更新的資訊
'5_snapshot.csv' 擷取出snap_id、snapshot_date、model_id、likes
每個model_id只保留最新快照
再從4_model_table.csv取得created_at、last_modified
這張表的目的是列出所有模型最新的下載數和按讚數

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


def create_last_modified_table(mod_path, sap_path, out_path):

    mod_df = read_csv(mod_path)
    sap_df = read_csv(sap_path)

    required_snapshot_cols = ['snap_id', 'snapshot_date', 'model_id', 'likes']
    required_download_cols = ['daily_actual_dls']
    required_model_cols = ['model_id', 'created_at', 'last_modified']
    missing_cols = [col for col in required_snapshot_cols + required_download_cols if col not in sap_df.columns]
    missing_cols.extend(col for col in required_model_cols if col not in mod_df.columns)

    if missing_cols:
            print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}，請確認欄位名稱是否正確。")
            return

    daily_downloads = pd.to_numeric(sap_df['daily_actual_dls'], errors='coerce')
    invalid_downloads = sap_df['daily_actual_dls'].notna() & daily_downloads.isna()
    if invalid_downloads.any():
        print("⚠️ 警告：daily_actual_dls 含有無法解析的數值，未輸出資料。")
        return

    totals_df = (
        sap_df.assign(_daily_actual_dls=daily_downloads)
        .groupby('model_id', as_index=False)['_daily_actual_dls']
        .sum()
        .rename(columns={'_daily_actual_dls': 'totle_dls'})
    )

    snapshot_dates = pd.to_datetime(sap_df['snapshot_date'], errors='coerce')
    if snapshot_dates.isna().any():
        print("⚠️ 警告：snapshot_date 含有無法解析的日期，未輸出資料。")
        return

    modified_df = sap_df[required_snapshot_cols].copy()
    modified_df['_snapshot_date'] = snapshot_dates
    modified_df = (
        modified_df
        .sort_values(['_snapshot_date', 'snap_id'], kind='stable')
        .drop_duplicates(subset=['model_id'], keep='last')
        .sort_values('model_id', kind='stable')
        .drop(columns='_snapshot_date')
        .reset_index(drop=True)
    )
    modified_df = modified_df.merge(
        totals_df,
        on='model_id',
        how='left',
        validate='one_to_one'
    )
    modified_df = modified_df.merge(
        mod_df[required_model_cols],
        on='model_id',
        how='left',
        validate='many_to_one',
        indicator=True
    )
    unmatched = modified_df['_merge'] != 'both'
    if unmatched.any():
        print(f"⚠️ 警告：有 {unmatched.sum()} 個 model_id 找不到模型資料，未輸出資料。")
        return
    modified_df = modified_df.drop(columns='_merge')
    modified_df = modified_df.rename(columns={'likes': 'total_likes'})
    modified_df.insert(
        0,
        'mfy_id',
        [f'mfy{index:04d}' for index in range(1, len(modified_df) + 1)]
    )
    
    modified_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    
    print("🎉 [快照資料表] 建立成功！")
    print(f"📁 檔案已儲存為：{out_path}")
    print(f"📊 總共成功建立了 {len(modified_df)} 筆快照資料。")
    print("\n👀 產出的資料前 5 筆範例：")
    print(modified_df.head())

if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定原始檔案與輸出檔案的完整路徑
    mod_path = root / 'data' / '4_dim_model.csv'
    sap_path = root / 'data' / '6_dim_snapshot.csv'
    out_path = root / 'data' / '7_fact_model_totals.csv'


    # 2. 呼叫函數並把路徑傳進去
    create_last_modified_table(mod_path, sap_path, out_path)