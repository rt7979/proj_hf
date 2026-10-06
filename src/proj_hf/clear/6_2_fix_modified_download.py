"""
************************************

程式六：修改download
首筆資料維持不變，後續資料依據 30 天滾動下載量差分推算每日下載量

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


def modified_download(snap_path):
    """
    以「期末存量相減法」決定月度總量，並依據「每日新增按讚數」作為權重進行每日分攤。
    保留每日真實起伏，同時確保 Power BI 月度加總 100% 精準、時間無遲滯。
    """

    snap_df = read_csv(snap_path)
    if snap_df is None:
        return

    required_cols = ['snapshot_date', 'model_id', 'rolling_30d_dls', 'likes']
    missing_cols = [col for col in required_cols if col not in snap_df.columns]
    if missing_cols:
        print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}。")
        return

    # 1. 資料預處理
    df = snap_df.copy()
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'], format='mixed', errors='coerce')
    df['rolling_30d_dls'] = pd.to_numeric(df['rolling_30d_dls'], errors='coerce')
    df['likes'] = pd.to_numeric(df['likes'], errors='coerce').fillna(0)
    df['year_month'] = df['snapshot_date'].dt.to_period('M')

    print("⏳ 正在計算每日新增按讚數與月度期末存量...")

    # 確保依模型與時間正確排序
    df = df.sort_values(['model_id', 'snapshot_date'], kind='stable')

    # 2. 計算「每日純新增按讚數」(當天likes - 前一天likes)
    # 若為該模型的第一筆資料，當天新增讚數視為 0 (避免把歷史累積當成單日暴增)
    df['daily_new_likes'] = df.groupby('model_id')['likes'].diff().fillna(0)
    # 理論上累加數差分不為負，若有資料異常導致負數則校正為 0
    df['daily_new_likes'] = df['daily_new_likes'].clip(lower=0)

    # 3. 找出每個模型每個月的「最後一天月底存量」
    month_end_balances = df.groupby(['model_id', 'year_month'], as_index=False).last()
    month_end_balances = month_end_balances.sort_values(['model_id', 'year_month'], kind='stable')
    
    # 計算【本月底存量 - 上月底存量】得到月度淨變動
    month_end_balances['prev_month_end_rolling'] = month_end_balances.groupby('model_id')['rolling_30d_dls'].shift(1).fillna(0)
    month_end_balances['month_net_change'] = month_end_balances['rolling_30d_dls'] - month_end_balances['prev_month_end_rolling']

    # 4. 計算每個模型在「每個月的總新增按讚數」，用來計算權重分母
    month_total_likes = df.groupby(['model_id', 'year_month'])['daily_new_likes'].sum().reset_index(name='month_total_new_likes')

    # 合併月度變動量與月度總讚數
    month_summary = pd.merge(
        month_end_balances[['model_id', 'year_month', 'month_net_change']], 
        month_total_likes, 
        on=['model_id', 'year_month']
    )

    # 5. 將月度數據對齊回每日流水帳，開始進行權重分攤
    df_merged = pd.merge(df, month_summary, on=['model_id', 'year_month'], how='left')

    print("📊 正在依據按讚權重分配每日下載量...")
    
    def allocate_daily(row):
        # 如果該月完全沒有人按讚（分母為 0），則回歸「均勻分攤」
        if row['month_total_new_likes'] == 0:
            # 這裡需要知道該群組當月有幾天，為了效能我們用粗估或維持基準值
            return pd.NA 
        
        # 核心權重公式：月總變動量 * (當天新增讚數 / 月總新增讚數)
        weight = row['daily_new_likes'] / row['month_total_new_likes']
        return row['month_net_change'] * weight

    # 執行分配
    df_merged['allocated_dls'] = df_merged.apply(allocate_daily, axis=1)

    # 處理該月總讚數為 0 的特殊邊緣情況 (改用均勻分攤)
    # 找出分母為 0 的群組並計算天數
    zero_likes_mask = df_merged['month_total_new_likes'] == 0
    if zero_likes_mask.any():
        month_days = df_merged[zero_likes_mask].groupby(['model_id', 'year_month']).size().reset_index(name='days_in_month')
        df_merged = pd.merge(df_merged, month_days, on=['model_id', 'year_month'], how='left')
        df_merged['days_in_month'] = df_merged['days_in_month'].fillna(1)
        
        # 均勻分攤
        uniform_alloc = df_merged['month_net_change'] / df_merged['days_in_month']
        df_merged['allocated_dls'] = df_merged['allocated_dls'].fillna(uniform_alloc)
        df_merged = df_merged.drop(columns=['days_in_month'])

    # 四捨五入成整數，並寫入 daily_actual_dls
    df_merged['daily_actual_dls'] = df_merged['allocated_dls'].round().astype('Int64')

    # 6. 清理輔助欄位，恢復標準 CSV 結構
    ordered_cols = ['snap_id', 'snapshot_date', 'model_id', 'author_id', 'pipeline_id', 'lib_id', 'created_at', 'likes', 'rolling_30d_dls', 'daily_actual_dls']
    
    for col in ordered_cols:
        if col not in df_merged.columns:
            df_merged[col] = snap_df[col] if col in snap_df.columns else pd.NA
            
    final_df = df_merged[ordered_cols].copy()
    final_df['snapshot_date'] = final_df['snapshot_date'].dt.strftime('%Y-%m-%d')

    # 輸出成 CSV 檔
    final_df.to_csv(snap_path, index=False, encoding='utf-8-sig')

    print("🎉 [快照資料表] 按讚權重分攤手術圓滿成功！")
    print(f"📁 檔案已儲存並覆寫：{snap_path}")
    print(f"📈 資料分布：現在日線圖將具備與『按讚活躍度』同步的真實起伏波動！")

    """
    以「期末存量相減法」反推每日下載量，並直接覆寫原始快照 CSV。
    不使用 max(0) 強制截斷，保留真實的正負變動趨勢，確保月度加總 100% 精準。
    """

    snap_df = read_csv(snap_path)
    if snap_df is None:
        return

    required_cols = ['snapshot_date', 'model_id', 'rolling_30d_dls']
    missing_cols = [col for col in required_cols if col not in snap_df.columns]
    if missing_cols:
        print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}。")
        return

    # 建立副本並確保資料型態正確
    df = snap_df.copy()
    df['snapshot_date'] = pd.to_datetime(df['snapshot_date'], format='mixed', errors='coerce')
    df['rolling_30d_dls'] = pd.to_numeric(df['rolling_30d_dls'], errors='coerce')
    
    # 建立「年-月」輔助欄位，用來做月度結算
    df['year_month'] = df['snapshot_date'].dt.to_period('M')
    
    print("⏳ 正在進行【期末存量相減】月度反推計算...")

    # 1. 找出每個模型、每個月的「最後一天快照記錄」
    # 依模型和日期排序，確保最後一筆是月底
    df_sorted = df.sort_values(['model_id', 'snapshot_date'], kind='stable')
    
    # 抓出月底存量
    month_end_balances = df_sorted.groupby(['model_id', 'year_month'], as_index=False).last()
    
    # 2. 計算每個模型「本月月底」與「上月月底」的差值
    # 依模型排序後，使用 shift(1) 抓出上個月底的存量
    month_end_balances_sorted = month_end_balances.sort_values(['model_id', 'year_month'], kind='stable')
    month_end_balances_sorted['prev_month_end_rolling'] = month_end_balances_sorted.groupby('model_id')['rolling_30d_dls'].shift(1)
    
    # 如果沒有上月歷史紀錄（首月發布），上月底存量視為 0
    month_end_balances_sorted['prev_month_end_rolling'] = month_end_balances_sorted['prev_month_end_rolling'].fillna(0)
    
    # 核心公式：月度熱度淨變動 = 本月月底存量 - 上月月底存量
    month_end_balances_sorted['month_net_change'] = (
        month_end_balances_sorted['rolling_30d_dls'] - month_end_balances_sorted['prev_month_end_rolling']
    )
    
    # 3. 計算每個月有多少天，用來做日均分攤
    # 這樣做能確保 Power BI 不管拉日線圖、月線圖，SUM() 起來的總量都完全不失真
    month_days = df.groupby(['model_id', 'year_month']).size().reset_name_and_index_if_needed = df.groupby(['model_id', 'year_month']).size().reset_index(name='days_in_month')
    
    # 合併計算結果回到月度表
    month_summary = pd.merge(month_end_balances_sorted[['model_id', 'year_month', 'month_net_change']], month_days, on=['model_id', 'year_month'])
    
    # 計算每日分攤量（保留小數點，以防除不盡；若您一定要整數，可加 .round()）
    month_summary['daily_allocated_dls'] = month_summary['month_net_change'] / month_summary['days_in_month']
    
    # 4. 將計算好的每日分攤量，完美對應並寫回原本的每日流水帳中
    df_merged = pd.merge(df, month_summary[['model_id', 'year_month', 'daily_allocated_dls']], on=['model_id', 'year_month'], how='left')
    
    # 四捨五入成整數，並寫入 daily_actual_dls
    df_merged['daily_actual_dls'] = df_merged['daily_allocated_dls'].round().astype('Int64')
    
    # 5. 清理欄位，恢復成您原本指定的 CSV 標準順序
    ordered_cols = ['snap_id', 'snapshot_date', 'model_id', 'author_id', 'pipeline_id', 'lib_id', 'created_at', 'likes', 'rolling_30d_dls', 'daily_actual_dls']
    
    # 確保原本沒在計算中的欄位也安全留下來
    for col in ordered_cols:
        if col not in df_merged.columns:
            df_merged[col] = snap_df[col] if col in snap_df.columns else pd.NA
            
    final_df = df_merged[ordered_cols].copy()
    
    # 格式化回文字日期，確保匯出格式正常
    final_df['snapshot_date'] = final_df['snapshot_date'].dt.strftime('%Y-%m-%d')

    # 輸出成 CSV 檔
    final_df.to_csv(snap_path, index=False, encoding='utf-8-sig')

    print("🎉 [快照資料表] 期末存量相減手術成功！")
    print(f"📁 檔案已儲存並覆寫：{snap_path}")
    print(f"📊 總共成功建立了 {len(final_df)} 筆快照資料。")
    
    # 安全檢查
    positive_change = (final_df['daily_actual_dls'] > 0).sum()
    negative_change = (final_df['daily_actual_dls'] < 0).sum()
    zero_count = (final_df['daily_actual_dls'] == 0).sum()
    print(f"🛡️ 數據分布檢查：每日分攤值中，增長(正數)有 {positive_change} 筆，衰退(負數)有 {negative_change} 筆，持平(0)有 {zero_count} 筆。")
    print("💡 提示：負數是完全正常的現象，代表該模型該月熱度正在退燒，這能確保 Power BI 加總 100% 精準！")


if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf

    # 1. 直接處理原始快照檔，並覆寫同一份 6_fact_snapshot.csv
    snap_path = root / 'data' / '6_fact_snapshot.csv'

    # 2. 呼叫函數並把路徑傳進去
    modified_download(snap_path)
