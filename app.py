import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from io import StringIO

# ==========================================
# 1. 填入您的 CSV 網址
# ==========================================
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTkNPFE9Hxuu4HfRVSdfYuO4VVFeNNMX08LIBNd-glPv-8A2MovJUrFetlCqTtKLs7unXN7m_DSAAIv/pub?gid=0&single=true&output=csv"

st.set_page_config(page_title="資產監控站", layout="wide")
st.title("🚀 投資組合自動同步中")

# ==========================================
# 2. 強力讀取邏輯
# ==========================================
def fetch_data(url):
    try:
        # 使用 requests 抓取，增加穩定性
        response = requests.get(url)
        response.encoding = 'utf-8' # 確保中文不亂碼
        if response.status_code == 200:
            return pd.read_csv(StringIO(response.text))
        else:
            st.error(f"伺服器回傳代碼錯誤: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"連線發生異常: {e}")
        return None

df = fetch_data(CSV_URL)

if df is not None:
    if df.empty:
        st.warning("⚠️ 連線成功，但讀取到的資料是空的，請確認試算表內有內容。")
    else:
        st.success("✅ 雲端同步成功！")
        with st.expander("查看原始數據"):
            st.dataframe(df)
            
        # 這裡檢查欄位並抓取股價 (邏輯同前)
        if 'ticker' in df.columns:
            tickers = df['ticker'].dropna().unique().tolist()
            # ... 抓取股價代碼 ...
else:
    st.error("🆘 依然無法連線到試算表")
    st.info("請檢查：1. 網址是否正確 2. 試算表是否已『發佈到網路』")
