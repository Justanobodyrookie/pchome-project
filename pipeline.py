import pandas as pd
import boto3
import json
import os
from sqlalchemy import create_engine
from sqlalchemy import inspect
from botocore.config import Config
from dotenv import load_dotenv
from datetime import datetime, timezone

# 1. 載入環境變數
load_dotenv('/home/hsu00093/.env')

# 設定變數
DB_USER = 'user'
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_HOST = 'localhost'
DB_PORT = '5432'
DB_NAME = 'pchome_db'

MINIO_ENDPOINT = 'http://localhost:9000'
MINIO_ACCESS_KEY = 'admin'
MINIO_SECRET_KEY = os.getenv('MINIO_PASSWORD')

# ==========================================
# [Block 1] Extract: 從 MinIO 讀取 (修正版：突破 1000 筆限制)
# ==========================================
def load_from_minio():
    print("Step 1 開始讀取 MinIO...")
    try:
        s3 = boto3.client(
            's3',
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            region_name='us-east-1',
            config=Config(connect_timeout=5, retries={'max_attempts': 0})
        )
        
        bucket_name = 'raw-data'
        
        # [關鍵修正] 改用 Paginator，專門處理超過 1000 個檔案的情況
        paginator = s3.get_paginator('list_objects_v2')
        page_iterator = paginator.paginate(Bucket=bucket_name, Prefix='pchome/')
        
        today = datetime.now(timezone.utc).date()
        target_files = []
        
        print("正在掃描 MinIO 檔案清單 (可能需要一點時間)...")
        
        for page in page_iterator:
            if 'Contents' not in page:
                continue
                
            for obj in page['Contents']:
                # 只抓今天的
                if obj['LastModified'].date() == today:
                    target_files.append(obj['Key'])
        
        if not target_files:
            print(f"⚠️ 找不到日期為 {today} 的檔案")
            return None

        print(f"📦 發現 {len(target_files)} 個今天的檔案，開始下載合併...")
        
        data_list = []
        # 為了顯示進度，每處理 100 個印一次
        count = 0
        for key in target_files:
            try:
                obj = s3.get_object(Bucket=bucket_name, Key=key)
                content = json.loads(obj['Body'].read().decode('utf-8'))
                data_list.append(content)
                count += 1
                if count % 500 == 0:
                    print(f"  - 已下載 {count} / {len(target_files)} 筆...")
            except Exception as e:
                print(f"讀取 {key} 失敗: {e}")

        if not data_list:
            return None
            
        return pd.DataFrame(data_list)
        
    except Exception as e:
        print(f"MinIO 讀取失敗: {e}")
        return None

# ==========================================
# [Block 2] Transform: 清洗與拆分
# ==========================================
def transform_data(df):
    print(f"Step 2 開始清洗資料 ({len(df)} 筆)...")
    
    expected_dim_cols = ['product_id', 'name', 'category', 'describe', 'img_url']
    for col in expected_dim_cols:
        if col not in df.columns:
            df[col] = None
            
    expected_fact_cols = ['product_id', 'price', 'original_price', 'rating', 'comment', 'crawled_at']
    for col in expected_fact_cols:
        if col not in df.columns:
            df[col] = None

    # Dim 表：去重
    dim_df = df[expected_dim_cols].copy()
    dim_df.drop_duplicates(subset=['product_id'], keep='last', inplace=True)
    
    # Fact 表
    fact_df = df[expected_fact_cols].copy()
    fact_df['rating'] = pd.to_numeric(fact_df['rating'], errors='coerce')
    fact_df['price'] = pd.to_numeric(fact_df['price'], errors='coerce')
    fact_df['original_price'] = pd.to_numeric(fact_df['original_price'], errors='coerce')
    fact_df['crawled_at'] = pd.to_datetime(fact_df['crawled_at'])
    
    return dim_df, fact_df

# ==========================================
# [Block 3] Load: 寫入 Postgres
# ==========================================
def load_to_postgres(dim_df, fact_df):
    print("Step 3 準備寫入資料庫...")
    
    conn_str = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(conn_str)
    
    try:
        # 1. 處理 Dim Products
        print(f"正在處理 dim_products ({len(dim_df)} 筆)...")
        inspector = inspect(engine)
        
        if not inspector.has_table("dim_products"):
            print("建立新表 dim_products...")
            dim_df.to_sql('dim_products', engine, if_exists='append', index=False)
        else:
            existing_ids = pd.read_sql("SELECT product_id FROM dim_products", engine)
            # 這裡要小心，如果資料庫是空的，existing_ids 可能會報錯或空
            if not existing_ids.empty:
                new_products = dim_df[~dim_df['product_id'].isin(existing_ids['product_id'])]
            else:
                new_products = dim_df

            if not new_products.empty:
                print(f"寫入 {len(new_products)} 筆新商品...")
                new_products.to_sql('dim_products', engine, if_exists='append', index=False, method='multi')
            else:
                print("沒有新商品需要寫入。")

        # 2. 處理 Fact Daily Prices
        print(f"寫入 fact_daily_prices ({len(fact_df)} 筆)...")
        # chunksize 設為 1000，避免一次塞太多被資料庫踢出來
        fact_df.to_sql('fact_daily_prices', engine, if_exists='append', index=False, method='multi', chunksize=1000)
        
        print("🎉 大功告成！")
        
    except Exception as e:
        print(f"❌ 資料庫寫入失敗: {e}")

# ==========================================
# 主程式
# ==========================================
if __name__ == "__main__":
    df_raw = load_from_minio()
    if df_raw is not None and not df_raw.empty:
        dim, fact = transform_data(df_raw)
        load_to_postgres(dim, fact)
    else:
        print("沒有資料需要處理。")
