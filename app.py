import streamlit as st
import pandas as pd
import numpy as np
import os
import time
import random
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine
from datetime import datetime
from dotenv import load_dotenv

# 1. 頁面基本設定
st.set_page_config(page_title='PChome 監控所', layout='wide', page_icon='🗿')

# 2. 載入環境變數
load_dotenv()

# ==========================================
# 🧠 核心大腦：智能分類函式
# ==========================================
def classify_product(category_val, name):
    cat = str(category_val).lower()
    name = str(name).lower()
    
    # === 1. Apple 區 ===
    if 'apple' in cat or 'dyaj' in cat or 'iphone' in name:
        if any(x in name for x in ['殼', '套', '線', '貼', '筆尖', '轉接', '充電', '錶帶']): return 'Apple配件'
        if 'watch' in name: return 'Apple Watch'
        if 'mac' in name or 'studio' in name or 'mini' in name: return 'Mac電腦'
        if 'pad' in name: return 'iPad'
        if 'airpods' in name or '耳機' in name: return 'AirPods'
        if 'phone' in name: return 'iPhone'
        return 'Apple其他'

    # === 2. 遊戲機 區 ===
    if '遊戲' in cat or 'game' in cat or 'dgbj' in cat or 'switch' in name or 'ps5' in name:
        if any(x in name for x in ['手把', '控制器', '殼', '包', '貼', '方向盤']): return '遊戲周邊'
        if any(x in name for x in ['主機', 'oled', 'console']): return '遊戲主機'
        if any(x in name for x in ['遊戲', '片', '版', '特典', '薩爾達', '瑪利歐']): return '遊戲軟體'
        return '遊戲其他'

    # === 3. 衛生紙 區 ===
    if '衛生紙' in cat or 'daao' in cat or '紙巾' in name:
        if '濕' in name: # 這裡要攔截濕紙巾
             if any(x in name for x in ['酒精', '抗菌', '消毒']): return '抗菌濕巾'
             if '純水' in name: return '嬰兒純水濕巾'
             return '一般濕巾'
        if '廚房' in name or '擦手' in name: return '廚房紙巾'
        if '捲' in name: return '捲筒衛生紙'
        if any(x in name for x in ['袖珍', '隨身', '面紙']): return '隨身面紙'
        if '平版' in name: return '平版衛生紙'
        return '抽取衛生紙'

    # === 4. 濕紙巾 區 ===
    if '濕紙巾' in cat or 'daat' in cat:
        if any(x in name for x in ['酒精', '抗菌', '消毒']): return '抗菌濕巾'
        if any(x in name for x in ['隨身', '10抽', '20抽']): return '隨身濕巾'
        if '純水' in name: return '嬰兒純水濕巾'
        return '一般濕巾'

    # === 5. 洗衣 區 ===
    if '洗衣' in cat or 'daak' in cat or '洗衣' in name:
        if any(x in name for x in ['球', '膠囊']): return '洗衣球'
        if '粉' in name: return '洗衣粉'
        if '皂' in name: return '洗衣皂'
        if any(x in name for x in ['香', '柔']): return '衣物護理'
        return '洗衣精'

    # === 6. 清潔/洗碗 區 ===
    if '清潔' in cat or 'daaz' in cat or '洗碗' in name:
        if any(x in name for x in ['蟑', '蟻', '蚊', '蟲']): return '除蟲殺菌'
        if any(x in name for x in ['洗碗', '碗盤']): return '洗碗精'
        if any(x in name for x in ['香', '除濕']): return '空氣濕度'
        return '居家清潔'

    # === 7. 口腔 區 ===
    if '口腔' in cat or 'daal' in cat or '牙' in name:
        if '刷頭' in name: return '電動牙刷耗材'
        if '電動' in name: return '電動牙刷'
        if '漱' in name: return '漱口水'
        if '牙膏' in name: return '牙膏'
        return '牙刷牙線'

    # === 8. 洗髮 區 ===
    if '洗髮' in cat or 'daaa' in cat:
        if any(x in name for x in ['養髮', '頭皮', '生髮', '落建']): return '頭皮護理'
        return '洗髮精'

    # === 9. 沐浴 區 ===
    if '沐浴' in cat or 'daaj' in cat:
        if '皂' in name: return '香皂'
        if any(x in name for x in ['角質', '磨砂', '鹽']): return '身體去角質'
        return '沐浴乳'
    
    return '其他'

# ==========================================
# 📊 模組 B: 資料庫連線
# ==========================================
@st.cache_data(ttl=3600)
def load_data():
    DB_USER = 'user'
    DB_PASSWORD = os.getenv('DB_PASSWORD')
    DB_HOST = 'localhost'
    DB_PORT = '5432'
    DB_NAME = 'pchome_db'
    
    conn_str = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    engine = create_engine(conn_str)

    sql = """
    WITH price_stats AS (
        SELECT 
            product_id,
            STDDEV(price) as price_std,
            AVG(price) as price_mean,
            MAX(price) as hist_high,
            MIN(price) as hist_low
        FROM fact_daily_prices
        GROUP BY product_id
    ),
    latest_price AS (
        SELECT DISTINCT ON (product_id)
            product_id, price, original_price, rating, comment, crawled_at
        FROM fact_daily_prices
        ORDER BY product_id, crawled_at DESC
    )
    SELECT 
        d.category,
        d.name,
        d.img_url,
        lp.product_id,
        coalesce(NULLIF(lp.price, 0), NULLIF(lp.original_price, 0), 0) as current_price,
        coalesce(NULLIF(lp.original_price, 0), lp.price) as original_price,
        lp.rating,
        lp.comment,
        ps.price_std,
        ps.price_mean,
        ps.hist_high,
        ps.hist_low
    FROM latest_price lp
    JOIN dim_products d ON lp.product_id = d.product_id
    JOIN price_stats ps ON lp.product_id = ps.product_id;
    """
    
    with engine.connect() as conn:
        df = pd.read_sql(sql, conn)
    return df

def process_data(df):
    df['sub_category'] = df.apply(lambda x: classify_product(x['category'], x['name']), axis=1)
    df['rating'] = pd.to_numeric(df['rating'], errors='coerce').fillna(0)
    df['comment'] = pd.to_numeric(df['comment'], errors='coerce').fillna(0)
    
    # 🔥🔥🔥 這裡就是補救的重點！拼出網址！ 🔥🔥🔥
    # PChome 網址規則: https://24h.pchome.com.tw/prod/ + product_id
    df['product_url'] = 'https://24h.pchome.com.tw/prod/' + df['product_id']
    
    # 購物模式計算
    df['discount_pct'] = 0.0
    valid_discount = (df['original_price'] > df['current_price']) & (df['original_price'] > 0)
    df.loc[valid_discount, 'discount_pct'] = (
        (df.loc[valid_discount, 'original_price'] - df.loc[valid_discount, 'current_price']) 
        / df.loc[valid_discount, 'original_price']
    )
    df['discount_bonus'] = (df['discount_pct'] * 10).clip(upper=5)
    df['log_bonus'] = 0.5 * np.log10(df['comment'] + 1)
    df['true_rating'] = df['rating'] + df['log_bonus']
    
    # 專業模式計算
    df['price_std'] = df['price_std'].fillna(0)
    df['volatility_cv'] = df.apply(
        lambda x: (x['price_std'] / x['price_mean']) if x['price_mean'] > 0 else 0, 
        axis=1
    )
    
    def label_discount(row):
        if row['discount_pct'] > 0.15 and row['rating'] >= 4.5: return "🔥 真・神物"
        elif row['discount_pct'] > 0.2 and row['rating'] < 3.0: return "⚠️ 雷品清倉"
        elif row['discount_pct'] > 0: return "💰 普通特價"
        else: return "➖ 無折扣"
            
    df['deal_type'] = df.apply(label_discount, axis=1)
    return df

def check_festival_radar():
    today = datetime.now()
    month, day = today.month, today.day
    radar_msg = None
    if month == 1 or (month == 2 and day < 15):
        radar_msg = {"title": "🧧 農曆春節 (CNY) 警報", "body": "市場關注：『掃除』、『送禮』、『遊戲機』。", "type": "info"}
    elif month == 11 and day <= 15:
        radar_msg = {"title": "🔥 雙11 購物節警報", "body": "全年度最大流量！請注意 3C 產品歷史低價是否突破。", "type": "error"}
    return radar_msg

# ==========================================
# 🖥️ UI 介面層
# ==========================================
def main():
    raw_df = load_data()
    df = process_data(raw_df)
    
    st.sidebar.title("🎛️ 智能中控台")
    mode = st.sidebar.radio("選擇模式", ["📊 專業市場分析", "🛒 購物小幫手"], index=1)
    st.sidebar.markdown("---")
    
    all_cats = sorted(df['category'].unique())
    selected_main_cat = st.sidebar.selectbox("選擇大分類", all_cats)
    available_sub_cats = df[df['category'] == selected_main_cat]['sub_category'].unique()
    selected_sub_cats = st.sidebar.multiselect("選擇次分類", available_sub_cats, default=available_sub_cats)
    filtered_df = df[(df['category'] == selected_main_cat) & (df['sub_category'].isin(selected_sub_cats))]

    # ==========================================
    # 情境 A: 專業市場分析
    # ==========================================
    if mode == "📊 專業市場分析":
        st.title(f"📈 {selected_main_cat} - 市場競品分析")
        
        with st.expander("🔮 數位擲筊系統 (數據看不懂？問天吧)", expanded=True):
            c1, c2 = st.columns([1, 4])
            with c1:
                ask_button = st.button("🙏 誠心請示", use_container_width=True)
            with c2:
                if ask_button:
                    with st.spinner("神明思考中..."):
                        time.sleep(0.8)
                    result = random.choice(["買了", "先冷靜"])
                    st.success(f"神明指示：**{result}**")
                else:
                    st.write("請先在心中默念商品名稱，再按下按鈕...")

        st.markdown("---")
        radar = check_festival_radar()
        if radar:
            if radar['type'] == 'info': st.info(f"**{radar['title']}**\n\n{radar['body']}")
            else: st.error(f"**{radar['title']}**\n\n{radar['body']}")

        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("1. 價格波動率 (Price Volatility)")
            st.caption("紅色(CV高)代表價格像海鮮一樣跳動，適合蹲低點。")
            if not filtered_df.empty:
                # 這裡把顏色靈敏度調成 0.01，這樣你比較容易看到紅色
                vol_data = filtered_df.groupby('sub_category')['volatility_cv'].mean().reset_index().sort_values('volatility_cv', ascending=False)
                vol_data['color'] = vol_data['volatility_cv'].apply(lambda x: '#EF553B' if x > 0.01 else '#636EFA')
                fig_vol = go.Figure(go.Bar(
                    x=vol_data['volatility_cv'], y=vol_data['sub_category'],
                    orientation='h', marker_color=vol_data['color']
                ))
                fig_vol.update_layout(xaxis_title="變異係數 (CV)", margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig_vol, use_container_width=True)
            else:
                st.warning("無資料可分析")

        with col_right:
            st.subheader("2. 折扣真實度 (Discount Authenticity)")
            st.caption("右上角綠色代表真神物，右下角紅色代表清倉雷品。")
            scatter_data = filtered_df[filtered_df['discount_pct'] > 0]
            if not scatter_data.empty:
                fig_scat = px.scatter(
                    scatter_data, x="discount_pct", y="rating",
                    size="comment", color="deal_type",
                    color_discrete_map={"神物": "#00CC96", "雷品清倉": "#EF553B", "💰 普通特價": "#AB63FA"},
                    hover_name="name", hover_data=["current_price"]
                )
                fig_scat.add_hline(y=4.5, line_dash="dot", opacity=0.5)
                fig_scat.add_vline(x=0.15, line_dash="dot", opacity=0.5)
                fig_scat.update_layout(xaxis_title="折扣幅度", yaxis_title="評分", margin=dict(l=0,r=0,t=0,b=0))
                st.plotly_chart(fig_scat, use_container_width=True)
            else:
                st.info("目前區間內無特價商品。")

        st.subheader("📋 競品監控清單")
        st.dataframe(
            # 🔥 記得把 product_url 加進來
            filtered_df[['img_url', 'sub_category', 'name', 'product_url', 'current_price', 'volatility_cv', 'deal_type']].sort_values('volatility_cv', ascending=False),
            column_config={
                "img_url": st.column_config.ImageColumn("圖片"),
                "name": st.column_config.TextColumn("商品名稱"),
                # 🔥 設定 LinkColumn
                "product_url": st.column_config.LinkColumn("購買", display_text="🔗 前往賣場"),
                "current_price": st.column_config.NumberColumn("價格", format="$%d"),
                "volatility_cv": st.column_config.NumberColumn("波動CV", format="%.3f"),
            },
            use_container_width=True
        )

    # ==========================================
    # 情境 B: 購物小幫手
    # ==========================================
    else:
        st.title(f"🛒 {selected_main_cat} - 購物小幫手")
        max_p = int(filtered_df['current_price'].max()) if not filtered_df.empty else 10000
        price_range = st.slider("💰 預算範圍", 0, max_p, (0, max_p))
        final_df = filtered_df[(filtered_df['current_price'] >= price_range[0]) & (filtered_df['current_price'] <= price_range[1])].copy()
        
        if not final_df.empty:
            avg_p = final_df['current_price'].mean()
            final_df['price_adv'] = (avg_p - final_df['current_price']) / avg_p
            final_df['final_score'] = (final_df['true_rating']*0.4) + (final_df['price_adv']*0.4) + (final_df['discount_bonus']*0.2)
            final_df = final_df.sort_values('final_score', ascending=False)
            
            top = final_df.iloc[0]
            k1, k2, k3 = st.columns(3)
            # 自訂 HTML 樣式讓冠軍字體變大
            k1.markdown(f"""
                <p style="font-size: 14px; margin-bottom: 0px; color: gray;">👑 CP值冠軍</p>
                <p style="font-size: 20px; font-weight: bold; margin: 0px;">{top['name'][:10]}...</p>
                <p style="font-size: 14px; color: green;">分數: {top['final_score']:.1f}分</p>
            """, unsafe_allow_html=True)
            
            k2.metric("⚖️ 本日均價", f"${avg_p:,.0f}", "🔥歷史低" if avg_p < final_df['hist_low'].min() else "持平")
            k3.metric("📅 歷史區間", f"${final_df['hist_low'].min():,.0f} ~ ${final_df['hist_high'].max():,.0f}")
            
            st.subheader("📉 價格分佈")
            fig = px.area(final_df.sort_values('current_price'), x='name', y='current_price', color='sub_category')
            fig.update_xaxes(showticklabels=False)
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 智能選物表")
            st.dataframe(
                # 🔥 這裡也要加 product_url
                final_df[['img_url', 'name', 'product_url', 'current_price', 'final_score', 'true_rating']],
                column_config={
                    "img_url": st.column_config.ImageColumn("圖片"),
                    "name": st.column_config.TextColumn("商品名稱"),
                    # 🔥 設定 LinkColumn
                    "product_url": st.column_config.LinkColumn("購買", display_text="🛍️ 去買"),
                    "current_price": st.column_config.NumberColumn("價格", format="$%d"),
                    "final_score": st.column_config.ProgressColumn("CP分數", max_value=10, format="%.1f"),
                    "true_rating": st.column_config.NumberColumn("真實評分", format="⭐ %.1f"),
                },
                use_container_width=True
            )

if __name__ == "__main__":
    main()
