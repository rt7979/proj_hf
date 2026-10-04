"""
************************************

程式六：修改download
採用統計學「比率分配縮放法」，保證首筆維持不變且全站無不切實際的 0
首筆資料維持不變，後續資料依照統計學按比例縮放，保證全站無不切實際的 0

************************************
"""
import pandas as pd
import numpy as np
from proj_hf.clear import clear
from proj_hf.get_root import get_root
from pathlib import Path


def read_csv(path_in):
    try:
        df = pd.read_csv(path_in)
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到原始檔案，請確認路徑：{path_in}")
        return
    return df


def modified_download(snap_path):
    """
    將 30 天滾動下載量換算為每日下載量，並直接覆寫原始 6_snapshot.csv。
    """

    snap_df = read_csv(snap_path)
    if snap_df is None:
        return

    required_cols = ['snapshot_date', 'model_id', 'created_at', 'rolling_30d_dls']
    missing_cols = [col for col in required_cols if col not in snap_df.columns]

    if missing_cols:
        print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}，請確認欄位名稱是否正確。")
        return

    snapshot_dates = pd.to_datetime(snap_df['snapshot_date'], format='mixed', errors='coerce')
    if snapshot_dates.isna().any():
        print("⚠️ 警告：snapshot_date 含有空值或無法解析的日期，未輸出資料。")
        return

    rolling_downloads = pd.to_numeric(snap_df['rolling_30d_dls'], errors='coerce')
    if rolling_downloads.isna().any() or (rolling_downloads.dropna() < 0).any():
        print("⚠️ 警告：rolling_30d_dls 數據異常，未輸出資料。")
        return
        
    if snap_df['model_id'].isna().any():
        print("⚠️ 警告：model_id 含有空值，未輸出資料。")
        return

    dates = snapshot_dates.dt.normalize()
    snapshot_df = snap_df.copy()
    snapshot_df['rolling_30d_dls'] = rolling_downloads
    snapshot_df['daily_actual_dls'] = pd.Series(pd.NA, index=snapshot_df.index, dtype='Int64')
    snapshot_df['_snapshot_date'] = dates

    calculated_rows = 0
    first_day_locked_rows = 0

    # 依模型分組進行統計學按比例縮放
    for model_id, model_rows in snapshot_df.sort_values(
        ['model_id', '_snapshot_date'], kind='stable'
    ).groupby('model_id', sort=False):
        
        # 如果該模型在日誌中只有 1 筆快照，直接讓日下載量 = 滾動下載量
        if len(model_rows) == 1:
            idx = model_rows.index[0]
            snapshot_df.at[idx, 'daily_actual_dls'] = int(model_rows['rolling_30d_dls'].iloc[0])
            first_day_locked_rows += 1
            continue

        # 區分「第一天」與「其他後續天數」
        first_idx = model_rows.index[0]
        other_idxs = model_rows.index[1:]
        
        # 1. 🔒 第一筆強制維持不變 (如 8/21 的 421918)
        first_rolling = model_rows['rolling_30d_dls'].iloc[0]
        snapshot_df.at[first_idx, 'daily_actual_dls'] = int(first_rolling)
        first_day_locked_rows += 1
        
        # 2. 📊 後續天數的每日下載量 = 30 天滾動下載量 / 30，四捨五入取整數
        other_rolling = model_rows['rolling_30d_dls'].iloc[1:]
        snapshot_df.loc[other_idxs, 'daily_actual_dls'] = np.floor(other_rolling / 30 + 0.5).astype(int)
        calculated_rows += len(other_idxs)

    # 移除輔助用時間欄位
    snapshot_df = snapshot_df.drop(columns=['_snapshot_date'])

    # 自訂欄位順序列表（保持原英文欄位名）
    ordered_cols = ['snap_id', 'snapshot_date', 'model_id', 'author_id', 'pipeline_id', 'lib_id', 'created_at', 'likes', 'rolling_30d_dls', 'daily_actual_dls']
    snapshot_df = snapshot_df[ordered_cols]

    # 輸出成 CSV 檔
    snapshot_df.to_csv(snap_path, index=False, encoding='utf-8-sig')

    print("🎉 [快照資料表] 建立成功！")
    print(f"📁 檔案已儲存為：{snap_path}")
    print(f"📊 總共成功建立了 {len(snapshot_df)} 筆快照資料。")
    print(f"📈 第一天鎖定不變：{first_day_locked_rows} 筆；其餘統計學按比例縮放：{calculated_rows} 筆。")
    
    # 檢查是否有任何未預期的負數或 0 外流
    zero_count = (snapshot_df['daily_actual_dls'] == 0).sum()
    negative_check = (snapshot_df['daily_actual_dls'] < 0).sum()
    print(f"🛡️ 安全檢查：發現 {zero_count} 筆 0，{negative_check} 筆負數資料（指標：必須均為 0 筆）。")
    
    print("\n👀 產出的資料前 5 筆範例（第 1 筆完全保留）：")
    print(snapshot_df.head())


if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf

    # 1. 直接處理原始快照檔，並覆寫同一份 6_fact_snapshot.csv
    snap_path = root / 'data' / '6_fact_snapshot.csv'

    # 2. 呼叫函數並把路徑傳進去
    modified_download(snap_path)
