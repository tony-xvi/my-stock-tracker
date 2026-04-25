import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

# ==========================================
# 1. 設定區：請填入您的 CSV 網址
# ==========================================
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTkNPFE9Hxuu4HfRVSdfYuO4VVFeNNMX08LIBNd-glPv-8A2MovJUrFetlCqTtKLs7unXN7m_DSAAIv/pubhtml?gid=0&single=true"

st.set_page_config(page_title="資產監控站", layout="wide")
st.title("🚀 投資組合自動同步中")

# ==========================================
# 2. 讀取與診斷邏輯
# ==========================================
try:
    # 嘗試讀取資料
    df = pd.read_csv(CSV_URL)
    
    if df.empty:
        st.warning("⚠️ 讀取成功，但試算表內容看起來是空的。")
        st.info("請檢查：您的 Google Sheets 第一行是否已經填寫了 ticker, type, price 等標題？")
    else:
        st.success("✅ 資料讀取成功！")
        
        # 顯示原始資料診斷
        with st.expander("🔍 診斷：查看讀取到的原始資料"):
            st.write("欄位名稱：", list(df.columns))
            st.dataframe(df)

        # 檢查關鍵欄位是否存在
        if 'ticker' in df.columns:
            st.subheader("📊 即時市場報價")
            tickers = df['ticker'].dropna().unique().tolist()
            
            # 抓取並顯示價格
            for t in tickers:
                try:
                    price = yf.Ticker(t).fast_info.last_price
                    st.metric(f"股票代號: {t}", f"${price:.2f}")
                except:
                    st.error(f"無法獲取 {t} 的報價")
        else:
            st.error("❌ 錯誤：試算表中找不到名為 'ticker' 的欄位標頭。")

except Exception as e:
    # 這就是剛才缺少的 except 區塊
    st.error("🆘 無法連線到試算表")
    st.write(f"詳細錯誤訊息: {e}")
    st.info("提示：請確認您已經在 Google Sheets 點擊『發佈到網路』並選擇了『CSV』格式。")
