"""
************************************

🧬 程式四_：模型參數量(B)
爬蟲到每一個模型的首頁查詢模型的總參數量

************************************
"""


import re
import time
import urllib.error
import urllib.request

import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm
from proj_hf.clear import clear
from proj_hf.get_root import get_root

REQUEST_INTERVAL_SECONDS = 1
MAX_RETRIES = 4


def fetch_model_size(model_name):
    """從 Hugging Face 模型頁面擷取原始參數量與單位。"""
    url = f"https://huggingface.co/{model_name}"
    request = urllib.request.Request(
        url,
        headers={
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            )
        },
    )

    html_content = None
    for attempt in range(MAX_RETRIES):
        time.sleep(REQUEST_INTERVAL_SECONDS)
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                html_content = response.read()
            break
        except urllib.error.HTTPError as error:
            if error.code == 404:
                return '模型不存在/非公開'
            if error.code != 429 and error.code < 500:
                return f'HTTP錯誤({error.code})'
            if attempt + 1 == MAX_RETRIES:
                return f'HTTP錯誤({error.code})'

            retry_after = error.headers.get('Retry-After') if error.headers else None
            try:
                delay = min(float(retry_after), 60) if retry_after else 5 * (2 ** attempt)
            except ValueError:
                delay = 5 * (2 ** attempt)
            time.sleep(delay)
        except (urllib.error.URLError, TimeoutError):
            if attempt + 1 == MAX_RETRIES:
                return '連線失敗'
            time.sleep(5 * (2 ** attempt))
        except Exception:
            return '連線失敗'

    if html_content is None:
        return '連線失敗'

    soup = BeautifulSoup(html_content, 'html.parser')

    for element in soup.find_all(
        'div', class_=re.compile(r'(?:^|\s)px-1\.5(?:\s|$)')
    ):
        match = re.search(
            r'([\d,.]+\s*[BMK])\s+params\b',
            element.get_text(' ', strip=True),
            re.IGNORECASE,
        )
        if match:
            return match.group(1).strip()

    return None


def normalize_param_size(value):
    """清除浮點數尾端的二進位表示誤差，保留非數值狀態文字。"""
    if pd.isna(value):
        return value
    try:
        number = float(value)
        rounded = round(number, 4)
        if number != rounded and abs(number - rounded) <= 1e-12:
            return format(rounded, '.15g')
        return value
    except (TypeError, ValueError):
        return value


def model_size_to_param_size_b(value):
    """將模型尺寸轉成十億參數數值，非尺寸內容回傳 None。"""
    if pd.isna(value):
        return None

    match = re.fullmatch(r'\s*([\d,.]+)\s*([BMK])\s*', str(value), re.IGNORECASE)
    if not match:
        return None

    size = float(match.group(1).replace(',', ''))
    unit = match.group(2).upper()
    multiplier = {'B': 1, 'M': 0.001, 'K': 0.000001}[unit]
    size *= multiplier
    if unit == 'B' and size.is_integer():
        return int(size)
    return normalize_param_size(size)


def should_fetch_model_size(value):
    """已取得尺寸或確認 404 的模型不重抓；暫時性錯誤會再次嘗試。"""
    if pd.isna(value) or not str(value).strip():
        return True
    if model_size_to_param_size_b(value) is not None:
        return False
    status = str(value).strip()
    return status == '連線失敗' or bool(
        re.fullmatch(r'HTTP錯誤\((?:429|5\d{2})\)', status)
    )


def read_csv(path_in):
    try:
        df = pd.read_csv(path_in)
    except FileNotFoundError:
        print(f"❌ 錯誤：找不到原始檔案，請確認路徑：{path_in}")
        return
    return df


def parser_params(mod_path):
    """
    爬取原始模型參數量寫入 model_size，並更新 param_size_b 十億參數數值。
    """
    mod_df = read_csv(mod_path)
    if mod_df is None:
        return

    if 'model_name' not in mod_df.columns:
        print("⚠️ 模型表缺少必要欄位：['model_name']")
        return

    if 'model_size' not in mod_df.columns:
        mod_df['model_size'] = pd.Series(index=mod_df.index, dtype=object)
    else:
        mod_df['model_size'] = mod_df['model_size'].astype(object)

    if 'param_size_b' not in mod_df.columns:
        mod_df['param_size_b'] = pd.Series(index=mod_df.index, dtype=object)
    else:
        mod_df['param_size_b'] = mod_df['param_size_b'].astype(object)

    for index, model_name in tqdm(
        mod_df['model_name'].items(), total=len(mod_df), desc='擷取模型參數量'
    ):
        if pd.isna(model_name) or not str(model_name).strip():
            mod_df.at[index, 'model_size'] = '模型名稱缺失'
            continue
        model_size = mod_df.at[index, 'model_size']
        if should_fetch_model_size(model_size):
            model_size = fetch_model_size(str(model_name).strip())
            mod_df.at[index, 'model_size'] = model_size
        param_size_b = model_size_to_param_size_b(model_size)
        if param_size_b is not None:
            mod_df.at[index, 'param_size_b'] = param_size_b

    mod_df['param_size_b'] = pd.Series(
        [normalize_param_size(value) for value in mod_df['param_size_b']],
        index=mod_df.index,
        dtype=object,
    )

    original_columns = list(mod_df.columns)
    columns = [
        column for column in original_columns
        if column not in ('model_size', 'param_size_b')
    ]
    if 'param_size_b' in original_columns:
        insert_at = sum(
            column not in ('model_size', 'param_size_b')
            for column in original_columns[:original_columns.index('param_size_b')]
        )
    else:
        insert_at = len(columns)
    columns[insert_at:insert_at] = ['model_size', 'param_size_b']
    mod_df = mod_df[columns]

    # 儲存覆寫檔案
    mod_df.to_csv(mod_path, index=False, encoding='utf-8-sig')

    print('🎉 [模型參數] Hugging Face 參數資料更新成功！')
    print(f'📁 檔案已更新：{mod_path}')
    print(f'📊 共更新 {len(mod_df)} 筆模型資料。')
    print('\n👀 更新後的前 3 筆資料：')
    print(mod_df[['model_name', 'model_size', 'param_size_b']].head(3))


if __name__ == "__main__":
    clear() # 螢幕清除魔法
    root = get_root()  # 取得 D:\proj\proj_hf
    
    # 1. 設定模型表與函式庫表路徑
    mod_path = root / 'data' / '4_dim_model.csv'
    
    # 2. 呼叫函數並把路徑傳進去
    parser_params(mod_path)
