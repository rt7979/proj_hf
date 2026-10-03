"""
************************************

🧬 程式四_：取得各模型 commit 的日期
首次提交日期，寫入 initial 欄位供檢查。
最新提交日期，寫入 new 欄位供檢查。
會剩下必須人工審核、或者模型遭刪除的欄位是空白
所以還需手動改欄位
hf_c.csv 的 created_at 是更新後的狀態，但 created_at 還是舊的

************************************
"""

import asyncio
import json
import re
from urllib.parse import parse_qs, quote, urljoin, urlsplit

import aiohttp
import pandas as pd
from bs4 import BeautifulSoup
from tqdm import tqdm

from proj_hf.clear import clear
from proj_hf.get_root import get_root


MAX_CONCURRENT_REQUESTS = 4
MAX_RETRIES = 5
COMMITS_PER_PAGE = 50
REQUEST_INTERVAL_SECONDS = 0.65


class RequestPacer:
    def __init__(self, interval):
        self.interval = interval
        self.lock = asyncio.Lock()
        self.next_request_at = 0

    async def wait(self):
        async with self.lock:
            loop = asyncio.get_running_loop()
            delay = self.next_request_at - loop.time()
            if delay > 0:
                await asyncio.sleep(delay)
            self.next_request_at = loop.time() + self.interval


async def fetch_page(session, semaphore, pacer, url):
    for attempt in range(MAX_RETRIES):
        retry = False
        try:
            async with semaphore:
                await pacer.wait()
                async with session.get(url) as response:
                    if response.status == 429 or response.status >= 500:
                        retry = True
                        retry_after = response.headers.get('Retry-After')
                    else:
                        return response.status, await response.text()
        except (aiohttp.ClientError, asyncio.TimeoutError):
            retry = True
            retry_after = None

        if retry and attempt + 1 < MAX_RETRIES:
            try:
                delay = float(retry_after) if retry_after else 2 ** attempt
            except ValueError:
                delay = 2 ** attempt
            await asyncio.sleep(min(delay, 60))

    return None, None


def get_last_page_number(soup, page_url):
    page_path = urlsplit(page_url).path.rstrip('/')
    page_numbers = [0]

    for link in soup.find_all('a', href=True):
        linked_url = urljoin(page_url, link['href'])
        parts = urlsplit(linked_url)
        if parts.path.rstrip('/') != page_path:
            continue

        page_values = parse_qs(parts.query).get('p', [])
        for page_value in page_values:
            try:
                page_numbers.append(int(page_value))
            except ValueError:
                continue

    return max(page_numbers)


def get_commit_count(soup):
    history_pattern = re.compile(r'History:\s*([\d,]+)\s+commits?', re.IGNORECASE)
    for link in soup.find_all('a', href=True):
        if '/commits/' not in link['href']:
            continue
        match = history_pattern.search(link.get_text(' ', strip=True))
        if match:
            return int(match.group(1).replace(',', ''))

    for element in soup.select('[data-props]'):
        try:
            props = json.loads(element['data-props'])
        except (json.JSONDecodeError, TypeError):
            continue
        commit_count = props.get('numCommits')
        if isinstance(commit_count, int):
            return commit_count

    return None


async def fetch_model_dates(session, semaphore, pacer, index, model_name, needs_initial, needs_new):
    if pd.isna(model_name) or not str(model_name).strip():
        return index, None, None

    encoded_name = quote(str(model_name).strip(), safe='/')
    newest_date = None
    if needs_new:
        api_url = f'https://huggingface.co/api/models/{encoded_name}/commits/main'
        status, api_response = await fetch_page(session, semaphore, pacer, api_url)
        if status == 200 and api_response is not None:
            try:
                commits = json.loads(api_response)
            except json.JSONDecodeError:
                commits = []
            if isinstance(commits, list) and commits and isinstance(commits[0], dict):
                newest = pd.to_datetime(commits[0].get('date'), errors='coerce', utc=True)
                if not pd.isna(newest):
                    newest_date = newest.strftime('%Y-%m-%d')

    if not needs_initial:
        return index, None, newest_date

    first_page_url = f'https://huggingface.co/{encoded_name}/commits/main?p=0'
    status, first_page_html = await fetch_page(session, semaphore, pacer, first_page_url)
    if status != 200 or first_page_html is None:
        return index, None, newest_date

    first_page_soup = BeautifulSoup(first_page_html, 'html.parser')
    commit_times = first_page_soup.select('article time[datetime]')
    if not commit_times:
        return index, None, newest_date

    commit_count = get_commit_count(first_page_soup)
    if commit_count is not None:
        last_page = max(0, (commit_count - 1) // COMMITS_PER_PAGE)
    else:
        last_page = get_last_page_number(first_page_soup, first_page_url)

    if last_page == 0:
        last_page_soup = first_page_soup
    else:
        last_page_url = f'https://huggingface.co/{encoded_name}/commits/main?p={last_page}'
        status, last_page_html = await fetch_page(session, semaphore, pacer, last_page_url)
        if status != 200 or last_page_html is None:
            return index, None, newest_date
        last_page_soup = BeautifulSoup(last_page_html, 'html.parser')

    oldest_page_times = last_page_soup.select('article time[datetime]')
    if not oldest_page_times:
        return index, None, newest_date

    oldest = pd.to_datetime(oldest_page_times[-1].get('datetime'), errors='coerce', utc=True)
    initial_date = None if pd.isna(oldest) else oldest.strftime('%Y-%m-%d')
    return index, initial_date, newest_date


def prepare_initial_column(model_df, limit=None):
    if 'initial' not in model_df.columns:
        model_df['initial'] = pd.Series(pd.NA, index=model_df.index, dtype='object')

    existing_dates = pd.to_datetime(
        model_df['initial'],
        format='mixed',
        errors='coerce'
    )
    valid_dates = existing_dates.notna()
    target_indices = model_df.head(limit).index if limit is not None else model_df.index
    model_df.loc[target_indices, 'initial'] = existing_dates.loc[target_indices].dt.strftime('%Y-%m-%d')

    return [
        (index, row['model_name'])
        for index, row in model_df.loc[target_indices].iterrows()
        if not valid_dates.loc[index]
    ]


def normalize_date_columns(model_df):
    for column in ('created_at', 'last_modified', 'initial', 'new'):
        if column not in model_df.columns:
            continue

        parsed_dates = pd.to_datetime(
            model_df[column],
            format='mixed',
            errors='coerce'
        )
        invalid_dates = model_df[column].notna() & parsed_dates.isna()
        if invalid_dates.any():
            print(f'❌ {column} 含有無法解析的日期，未寫入模型資料表。')
            return False
        model_df[column] = parsed_dates.dt.strftime('%Y-%m-%d')

    return True


async def process_model_csv(model_path, limit=None):
    try:
        model_df = pd.read_csv(model_path)
    except FileNotFoundError:
        print(f'❌ 錯誤：找不到模型資料檔案：{model_path}')
        return

    if 'model_name' not in model_df.columns:
        print("❌ CSV 缺少必要欄位：['model_name']")
        return

    initial_tasks = prepare_initial_column(model_df, limit=limit)
    initial_indices = {index for index, _ in initial_tasks}
    if 'new' not in model_df.columns:
        model_df['new'] = pd.Series(pd.NA, index=model_df.index, dtype='object')

    target_indices = model_df.head(limit).index if limit is not None else model_df.index
    existing_new_dates = pd.to_datetime(
        model_df['new'],
        format='mixed',
        errors='coerce'
    )
    valid_new_dates = existing_new_dates.notna()
    model_df.loc[target_indices, 'new'] = existing_new_dates.loc[target_indices].dt.strftime('%Y-%m-%d')
    new_indices = {
        index for index in target_indices
        if not valid_new_dates.loc[index]
    }
    todo_tasks = [
        (index, row['model_name'], index in initial_indices, index in new_indices)
        for index, row in model_df.loc[target_indices].iterrows()
        if index in initial_indices or index in new_indices
    ]
    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    pacer = RequestPacer(REQUEST_INTERVAL_SECONDS)
    timeout = aiohttp.ClientTimeout(total=30, connect=10)
    connector = aiohttp.TCPConnector(limit=MAX_CONCURRENT_REQUESTS, ttl_dns_cache=300)
    initial_failures = []
    new_failures = []
    estimated_requests = len(new_indices) + len(initial_tasks) * 2
    print(
        f'待補 initial：{len(initial_indices)} 筆，new：{len(new_indices)} 筆；'
        f'跳過兩欄皆完整：{len(target_indices) - len(todo_tasks)} 筆；預估約 '
        f'{estimated_requests * REQUEST_INTERVAL_SECONDS / 60:.0f} 分鐘（不含重試）。',
        flush=True
    )

    async with aiohttp.ClientSession(
        connector=connector,
        timeout=timeout,
        headers={'User-Agent': 'proj-hf commit history collector'}
    ) as session:
        tasks = [
            fetch_model_dates(session, semaphore, pacer, index, model_name, needs_initial, needs_new)
            for index, model_name, needs_initial, needs_new in todo_tasks
        ]
        with tqdm(total=len(tasks), desc='查詢 commit 日期', unit='模型') as progress:
            for task in asyncio.as_completed(tasks):
                index, initial_date, newest_date = await task
                if index in initial_indices:
                    if initial_date is None:
                        initial_failures.append(model_df.at[index, 'model_name'])
                    else:
                        model_df.at[index, 'initial'] = initial_date
                if index in new_indices:
                    if newest_date is None:
                        new_failures.append(model_df.at[index, 'model_name'])
                    else:
                        model_df.at[index, 'new'] = newest_date
                progress.update(1)

    if not normalize_date_columns(model_df):
        return

    try:
        model_df.to_csv(model_path, index=False, encoding='utf-8-sig')
    except PermissionError:
        print(f'❌ 無法寫入 {model_path}，請先關閉正在使用該 CSV 的程式。')
        return

    print(f'🎉 完成：新增 {len(new_indices) - len(new_failures)} 筆最新日期，')
    print(f'並補上 {len(initial_tasks) - len(initial_failures)} 筆缺漏的首次日期。')
    print(f'📁 檔案已儲存至：{model_path}')
    if new_failures:
        print(f'⚠️ {len(new_failures)} 個模型未能取得最新日期：')
        for model_name in new_failures[:20]:
            print(f'  - {model_name}')
    if initial_failures:
        print(f'⚠️ {len(initial_failures)} 個模型未能補上首次日期：')
        for model_name in initial_failures[:20]:
            print(f'  - {model_name}')

    print('\n👀 資料範例：')
    print(model_df[['model_name', 'initial', 'new']].head())


if __name__ == '__main__':
    clear()
    root = get_root()
    model_path = root / 'data' / '4_dim_model.csv'
    asyncio.run(process_model_csv(model_path))