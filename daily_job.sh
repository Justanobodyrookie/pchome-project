#!/bin/bash
# 上面這行叫Shebang,告訴電腦要用 "Bash" 這種語言來執行下面的內容

# 設定變數
# $(date +"%Y%m%d") 會自動抓取今天的日期,例如"20260116"
TODAY=$(date +"%Y%m%d")

# 設定日記要存在哪裡。LOG_FILE 最後會變成 "/home/hsu00093/logs/job_20260116.log"
LOG_DIR="/home/hsu00093/logs"
LOG_FILE="$LOG_DIR/job_$TODAY.log"

# mkdir -p (Make Directory): 建立資料夾
# -p 的意思是:如果資料夾已經存在，就不要報錯;如果父資料夾不存在，就順便幫我建一個。
mkdir -p "$LOG_DIR"

# echo: 就是Python的print
# >>: 意思是寫入並附加到檔案最後面。(如果用 > 會把舊內容洗掉，>> 則是接著寫)
echo "=================" >> "$LOG_FILE"
echo "排程開始: $(date)" >> "$LOG_FILE"
echo "=================" >> "$LOG_FILE"

# 啟動虛擬環境
# source: Linux指令，載入設定檔
# 這一步就像手動打`source venv/bin/activate`一樣
# 寫完整路徑是為了讓排程機器人知道家在哪
source /home/hsu00093/venv/bin/activate

echo "開始執行Scrapy爬蟲" >> "$LOG_FILE"

cd /home/hsu00093/pchome_scraper

#執行爬蟲
# >> "$LOG_FILE": 把爬蟲印出來的東西寫進日記裡
# 2>&1: 這句是天書，意思是把錯誤訊息(2)也導向跟正常訊息(1)同一個地方
# 這樣爬蟲報錯，錯誤訊息才會被寫進Log檔，而不是憑空消失
scrapy crawl pchome >> "$LOG_FILE" 2>&1

# $?:這是一個特殊變數，代表上一個指令的執行結果成績單
# 0代表成功(100分)，非0代表失敗
if [ $? -eq 0 ]; then
    echo "爬蟲執行成功" >> "$LOG_FILE"
else
    echo "爬蟲執行失敗(檢查Log)" >> "$LOG_FILE"
    exit 1 #強制結束整個腳本，不繼續往下跑(沒資料也就不用跑ETL了)
fi

echo " 開始執行ETL pipelin" >> "$LOG_FILE"
cd /home/hsu00093
python pipeline.py >> "$LOG_FILE" 2>&1
if [ $? -eq 0 ]; then
    echo "ETL執行成功" >> "$LOG_FILE"
else
    echo "ETL執行失敗" >> "$LOG_FILE"
    exit 1
fi

echo "=======================" >> "$LOG_FILE"
echo "排程結束時間: $(date)" >> "$LOG_FILE"
echo "=======================" >> "$LOG_FILE"

