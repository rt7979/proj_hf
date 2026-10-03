"""
************************************

🧬 程式四：處理模型明細 (硬體需求特徵升級版)
過濾重複的模型 ID。除了關聯類別 ID 與作者 ID 外，
更透過業界推估演算法，自動衍生出模型所需的 VRAM、RAM、建議顯卡與硬體分層。
相比3_clean_models.py
這支3_x_clean_models.py多了處理部分pipeline_tag的程式碼
(還需要英文排序)

※目前last_modified欄位不是最終時間

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


def create_model_table(raw_path, au_path, cat_path, lib_path, out_path):
    """
    讀取原始 CSV，並關聯作者表、類別表、函式庫表，最後匯出模型表
    """
    
    # 呼叫read_csv函數，讀取 CSV 檔案
    raw_df = read_csv(raw_path)
    au_df = read_csv(au_path)
    cat_df = read_csv(cat_path)
    lib_df = read_csv(lib_path)

    # 2. 檢查原始檔案欄位是否存在
    required_cols = [
        'id', 'author', 'created_at', 'last_modified', 'pipeline_tag',
        'library_name', 'library_type', 'base_framework', 'tags', 'private', 'gated'
    ]
    missing_cols = [col for col in required_cols if col not in raw_df.columns]

    if missing_cols:
        print(f"⚠️ 警告：原始檔案中找不到欄位 {missing_cols}，請確認欄位名稱是否正確。")
        return
        
    # 3. 擷取需要的原始欄位，並去除重複的模型 (以 id 作為唯一依據)
    model_base_df = raw_df[required_cols].drop_duplicates(subset=['id']).reset_index(drop=True)

    # 4. 【核心步驟】開始進行外鍵對照 (Merge / JOIN)
    # (1) 串接作者表：用原始的 'author' 欄位對應作者表的 'author_name'
    # 使用 how='left' 確保沒作者的模型也不會消失
    model_base_df = pd.merge(
        model_base_df,
        au_df[['author_name', 'author_id']],
        left_on='author',
        right_on='author_name',
        how='left'
    )

    # (2) 串接任務類別表：注意！你在第 2 張表把欄位改名叫 'pipeline_name' 了
    # 所以要用原始的 'pipeline_tag' 對應 cat_df 的 'pipeline_name'
    model_base_df = pd.merge(
        model_base_df, 
        cat_df[['pipeline_id', 'pipeline_name']], 
        left_on='pipeline_tag', 
        right_on='pipeline_name', 
        how='left'
    )

    # (3) 串接函式庫表，以三個欄位組合對應函式庫代理鍵
    model_base_df = pd.merge(
        model_base_df,
        lib_df[['lib_id', 'library_name', 'library_type', 'base_framework']].rename(
            columns={'lib_id': 'library_id'}
        ),
        on=['library_name', 'library_type', 'base_framework'],
        how='left',
        validate='many_to_one'
    )

    # 5. 清洗多餘的舊文字欄位，只留下資料庫要用的 ID 與基本資訊
    final_cols = ['id', 'author_id', 'created_at', 'last_modified', 'pipeline_id', 'library_id', 'tags', 'private', 'gated']
    model_df = model_base_df[final_cols].copy()

    # 6. 將原始代表模型名稱的 'id' 欄位重新命名為 'model_name' 
    # 這樣才能騰出欄位名稱來建立我們專屬的 'model_id' 主鍵
    model_df = model_df.rename(columns={'id': 'model_name'})

    # 依照模型名稱的英文字母順序排列，不區分大小寫
    model_df = model_df.sort_values(by='model_name', key=lambda names: names.str.lower()).reset_index(drop=True)

    # 7. 自動生成工業級模型主鍵 model_id (格式：mod0001, mod0002... 代表 Model)
    # 固定長度、不加底線，整齊又省空間！
    model_df.insert(0, 'model_id', [f"mod{str(i).zfill(4)}" for i in (model_df.index + 1)])

    # 8. 修改日期格式為yyyy-mm-dd
    for column in ['created_at', 'last_modified']:
        parsed_dates = pd.to_datetime(model_df[column], errors='coerce')
        invalid_dates = model_df[column].notna() & parsed_dates.isna()
        if invalid_dates.any():
            print(f"⚠️ 警告：{column} 含有無法解析的日期，未輸出模型資料表。")
            return
        model_df[column] = parsed_dates.dt.strftime('%Y-%m-%d')

    # 9. 匯出成新的 CSV 檔案
    model_df.to_csv(out_path, index=False, encoding='utf-8-sig')
    
    print(f"🎉 [模型基本資料表] 還原成功！")
    print(f"📁 檔案已儲存為：{out_path}")
    print(f"📊 總共成功還原了 {len(model_df)} 筆模型資料。")
    
    # 顯示前 3 筆資料確認外觀
    print("\n👀 產出的資料前 3 筆範例：")
    print(model_df.head(3))


if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定原始檔案與輸出檔案的完整路徑
    raw_path = root / 'data' / 'origin_csv' / 'hf_c.csv'
    au_path = root / 'data' / '1_dim_author.csv' # 關聯作者表
    cat_path = root / 'data' / '2_dim_pipeline_tag.csv' # 關聯類別-任務表
    lib_path = root / 'data' / '3_dim_library.csv' # 關聯類別-函式庫表
    out_path = root / 'data' / '4_dim_model.csv'
    
    # 2. 呼叫函數並把路徑傳進去
    create_model_table(raw_path, au_path, cat_path, lib_path, out_path)