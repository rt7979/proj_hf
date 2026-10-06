"""
************************************

程式六：時間序列追蹤日誌
hf_c.csv的整個流水時間紀錄
擷取快照時間、模型、作者、下載、按讚數、建立時間、最後更新、類別、函式庫
除了快照時間、下載、按讚數、最後更新
其餘欄位內容都用fk替代
pk的設計是以快照時間時間為依據，後面加上編號，也就是 yyyymmdd-0000
例如：20260101-0001

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


def create_snapshot_table(input_path, au_path, cat_path, lib_path, mod_path, out_path):
    """
    讀取原始 CSV，快照時間、模型、作者、下載、按讚數、建立時間、最後更新、類別、函式庫等資訊，並匯出
    """

    # 呼叫read_csv函數，讀取 CSV 檔案
    raw_df = read_csv(input_path)
    au_df = read_csv(au_path)
    cat_df = read_csv(cat_path)
    lib_df = read_csv(lib_path)
    mod_df = read_csv(mod_path)

    required_cols = [
        'snapshot_date', 'id', 'author', 'downloads', 'likes', 'created_at',
        'pipeline_tag', 'library_name', 'library_type', 'base_framework'
    ]
    missing_cols = [col for col in required_cols if col not in raw_df.columns]

    if missing_cols:
        print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}，請確認欄位名稱是否正確。")
        return

    snapshot_df = raw_df[required_cols].copy().rename(
        columns={'downloads': 'rolling_30d_dls'}
    )
    snapshot_df = snapshot_df.merge(
        mod_df[['model_id', 'model_name']],
        left_on='id',
        right_on='model_name',
        how='left',
        validate='many_to_one'
    )
    snapshot_df = snapshot_df.merge(
        au_df[['author_id', 'author_name']],
        left_on='author',
        right_on='author_name',
        how='left',
        validate='many_to_one'
    )
    snapshot_df = snapshot_df.merge(
        cat_df[['pipeline_id', 'pipeline_name']],
        left_on='pipeline_tag',
        right_on='pipeline_name',
        how='left',
        validate='many_to_one'
    )
    snapshot_df = snapshot_df.merge(
        lib_df[['lib_id', 'library_name', 'library_type', 'base_framework']],
        on=['library_name', 'library_type', 'base_framework'],
        how='left',
        validate='many_to_one'
    )
    snapshot_df = snapshot_df[[
        'snapshot_date', 'model_id', 'author_id', 'likes', 'rolling_30d_dls', 'created_at',
        'pipeline_id', 'lib_id'
    ]].copy()

    # 修改日期格式為yyyy-mm-dd
    date_columns = ['snapshot_date', 'created_at']
    parsed_dates = {}
    for column in date_columns:
        parsed = pd.to_datetime(snapshot_df[column], errors='coerce')
        invalid_dates = snapshot_df[column].notna() & parsed.isna()
        if invalid_dates.any():
            print(f"⚠️ 警告：{column} 含有無法解析的日期，未輸出快照檔案。")
            return
        parsed_dates[column] = parsed

    snapshot_dates = parsed_dates['snapshot_date']
    for column, parsed in parsed_dates.items():
        snapshot_df[column] = parsed.dt.strftime('%Y-%m-%d')

    # pk，[snap_id]，格式為yyyymmdd-0001，也就是20260101-0001
    date_keys = snapshot_dates.dt.strftime('%Y%m%d')
    sequence_numbers = snapshot_df.groupby(date_keys, sort=False).cumcount() + 1
    snapshot_df.insert(
        0,
        'snap_id',
        [f'{date}-{sequence:04d}' for date, sequence in zip(date_keys, sequence_numbers)]
    )

    snapshot_df.to_csv(out_path, index=False, encoding='utf-8-sig')

    print("🎉 [快照資料表] 建立成功！")
    print(f"📁 檔案已儲存為：{out_path}")
    print(f"📊 總共成功建立了 {len(snapshot_df)} 筆快照資料。")
    print("\n👀 產出的資料前 5 筆範例：")
    print(snapshot_df.head())


if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定原始檔案與輸出檔案的完整路徑
    raw_path = root / 'data' / 'origin_csv' / 'hf_c.csv'
    au_path = root / 'data' / '1_dim_author.csv'
    cat_path = root / 'data' / '2_dim_pipeline_tag.csv'
    lib_path = root / 'data' / '3_dim_library.csv'
    mod_path = root / 'data' / '4_dim_model.csv'
    out_path = root / 'data' / '6_dim_snapshot.csv'
    
    # 2. 呼叫函數並把路徑傳進去
    create_snapshot_table(raw_path, au_path, cat_path, lib_path, mod_path, out_path)