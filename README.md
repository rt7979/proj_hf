

```
proj_hf/
├─ .streamlit/
│  ├─ config.toml  --- # ⚙️ 告訴 Streamlit 啟用靜態資料夾功能（非常重要！）。
│  └─ secrets.toml --- # 🔏 SQL 資料庫帳號、密碼、連線位置、連接埠、資料庫名稱。
│
├─ .venv/
│
├─ data/
│  ├─ origin_csv/ --- # 📁 大數據來源，檔案太大所以沒上傳。
│  ├─ 1_dim_author.csv
│  ├─ 2_dim_pipeline_tag.csv
│  ├─ 3_dim_library.csv
│  ├─ 4_dim_model_table.csv
│  ├─ 6_fact_snapshot.csv
│  ├─ 7_fact_model_totals.csv
│  └─ 9_dim_date.csv
│
├─ docs/ --- # 📁 一些文件，沒上傳。
│
├─ src/
│  └─ proj_hf/
│     ├─ clear/ --- # 🛀 資料清洗的程式放置區。
│     ├─ connect_db/ --- # 🔗 連接db的程式放置區。
│     │
│     ├─ __init__.py    --- # 初始檔，無視
│     ├─ __pycache__    --- # 🗑️ 垃圾暫存檔，無視
│     ├─ clear.py       --- # 🖥️ 清除螢幕的魔法
│     ├─ get_root.py    --- # 🎋 絕對能找到專案路徑(root)的小函數
│     ├─ (db_connect_db.py) --- # 連接db用的程式
│     ├─ (db_query.py)      --- # select語法的程式
│     └─ templates.py   --- # 🎨 專門放你的網頁公共樣板（如頁首、頁尾）
│
├─ static/
│  ├─ css/          --- # css檔案位置(應該用不到)
│  ├─ images/       --- # 各式圖片檔位置
│  └─ js/           --- # javascript檔案位置(應該用不到)
│
├─ .gitignore       --- # 🚫 設定禁止上傳到github的資料夾或檔案
├─ .python-version  --- # 🧬 python版本
├─ 讀我(main).txt   --- # 方便顯示目前專案分支，還有架構圖
├─ app.py           --- # 🏠 真正的首頁 / 網站大門
├─ pyproject.toml   --- # 🔧 uv設定檔、安裝了什麼套件，使用uv sync可以快速恢復裝過的插件
├─ README.md        --- # 🗺️ 架構圖， <----- 在這 ----->
└─  uv.lock         --- # 安裝streamlit會自動產生的檔案

```