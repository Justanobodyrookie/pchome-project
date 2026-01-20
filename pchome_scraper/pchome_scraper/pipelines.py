import json
import boto3
import os
from botocore.config import Config
from dotenv import load_dotenv

# 強制載入最外層的 .env 檔案
load_dotenv('/home/hsu00093/.env')

class MinioPipeline:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            endpoint_url='http://localhost:9000',
            aws_access_key_id='admin',  # 這裡有寫死 admin，所以絕對不會報錯 missing key
            aws_secret_access_key=os.getenv('MINIO_PASSWORD'),
            region_name='us-east-1',
            config=Config(signature_version='s3v4')
        )
        self.bucket_name = 'raw-data'
        
        # 自動建立 Bucket
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except:
            try:
                self.s3_client.create_bucket(Bucket=self.bucket_name)
                print(f"⚠️ Bucket 已建立: {self.bucket_name}")
            except Exception as e:
                print(f"❌ 建立 Bucket 失敗: {e}")

    def process_item(self, item, spider):
        # 產生檔名
        product_id = item.get('product_id')
        if not product_id:
            import time
            product_id = f"unknown_{int(time.time())}"
            
        file_name = f"pchome/{product_id}.json"
        data = json.dumps(dict(item), ensure_ascii=False)
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_name,
                Body=data,
                ContentType='application/json'
            )
            print(f"✅ 上傳成功: {file_name}")
        except Exception as e:
            print(f"❌ 上傳失敗: {e}")
            
        return item
