"""
************************************

程式六：修改download
全新逻辑：直接使用 30天滾動下載量 / 30 生產每日實際下載量
並且最終結果嚴格按照 snap_id 進行全局排序

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
        return None
    return df


def modified_download(snap_path):
    """
    直接使用 rolling_30d_dls / 30 作為 daily_actual_dls。
    依照每個 model_id 的快照順序計算 likes 增量。
    徹底抹平首日歷史洪峰斷崖，且數值永遠大於等於 0，完美修復 Power BI 負數與圖表壞掉的問題。
    """

    snap_df = read_csv(snap_path)
    if snap_df is None:
        return

    required_cols = ['snap_id', 'model_id', 'likes', 'rolling_30d_dls']
    missing_cols = [col for col in required_cols if col not in snap_df.columns]
    if missing_cols:
        print(f"⚠️ 警告：原始檔案中找不到核心欄位 {missing_cols}。")
        return

    # 1. 複製資料，避免改動原 df
    df = snap_df.copy()

    # 2. 將滾動下載量轉為數值型態（防呆處理）
    df['rolling_30d_dls'] = pd.to_numeric(df['rolling_30d_dls'], errors='coerce').fillna(0)

    print("⏳ 正在依據「滾動下載量 / 30」生產每日實際下載量...")

    # 3. 核心安全公式：直接除以 30，並四捨五入成整數
    # 使用 'Int64' 可以完美相容未來可能產生的空值（NaN）
    df['daily_actual_dls'] = (df['rolling_30d_dls'] / 30).round().astype('Int64')

    likes = pd.to_numeric(df['likes'], errors='coerce')
    invalid_likes = df['likes'].notna() & likes.isna()
    if invalid_likes.any():
        print("⚠️ 警告：likes 含有無法解析的數值，未輸出資料。")
        return
    if likes.dropna().mod(1).ne(0).any():
        print("⚠️ 警告：likes 含有非整數數值，未輸出資料。")
        return

    df['likes'] = likes.astype('Int64')
    model_order = df.sort_values(['model_id', 'snap_id'], kind='stable')
    daily_likes = model_order.groupby('model_id', sort=False)['likes'].diff()
    first_observations = model_order.groupby('model_id', sort=False).cumcount().eq(0)
    daily_likes.loc[first_observations] = model_order.loc[first_observations, 'likes']
    df['daily_actual_likes'] = daily_likes.reindex(df.index).astype('Int64')

    # 4. 依照您的最新需求：嚴格按照 snap_id 進行全局排序
    print("🔀 正在按照 snap_id 進行全局排序...")
    df = df.sort_values(by='snap_id', ascending=True, kind='stable').reset_index(drop=True)

    # 5. 確保恢復您原本指定的 CSV 標準欄位順序與內容
    ordered_cols = ['snap_id', 'snapshot_date', 'model_id', 'author_id', 'pipeline_id', 'lib_id', 'created_at', 'likes', 'daily_actual_likes', 'rolling_30d_dls', 'daily_actual_dls']
    
    # 若有其他非核心欄位，安全保留
    for col in ordered_cols:
        if col not in df.columns:
            df[col] = snap_df[col] if col in snap_df.columns else pd.NA
            
    final_df = df[ordered_cols].copy()

    # 6. 輸出成 CSV 檔並覆寫
    final_df.to_csv(snap_path, index=False, encoding='utf-8-sig')

    print("🎉 [快照資料表] 每日下載量與按讚增量建立暨 snap_id 排序手術圓滿成功！")
    print(f"📁 檔案已儲存並覆寫：{snap_path}")
    print(f"📊 總共成功建立了 {len(final_df)} 筆按 snap_id 排序的快照資料。")


if __name__ == "__main__":
    clear()        # 螢幕清除魔法
    root = get_root()  # 取得路徑 D:\proj\proj_hf

    # 直接處理原始快照檔，並覆寫同一份 6_fact_snapshot.csv
    snap_path = root / 'data' / '6_fact_snapshot.csv'

    # 執行函數
    modified_download(snap_path)
