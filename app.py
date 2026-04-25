import streamlit as st
import pandas as pd
import yfinance as yf

# ==========================================
# 填入你「發佈到網路」得到的那個 CSV 網址
# ==========================================
CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTkNPFE9Hxuu4HfRVSdfYuO4VVFeNNMX08LIBNd-glPv-8A2MovJUrFetlCqTtKLs7unXN7m_DSAAIv/pub?gid=0&single=true&output=csv"
st.set_page_config(page_title="資產監測站", layout="wide")

st.title("🚀 投資組合自動同步中")

# 讀取測試
try:
    # 讀取交易紀錄 (假設它是第一個分頁)
    df = pd.read_csv(CSV_URL)
    
    if df.empty:
        st.warning("⚠️ 讀取成功，但試算表裡面好像沒資料？")
    else:
        st.success("✅ 資料庫連線成功！")
        
        # 顯示原始資料 (除錯用)
        with st.expander("查看原始資料"):
            st.write(df)

        # 簡單計算邏輯
        if 'ticker' in df.columns:
            tickers = df['ticker'].dropna().unique().tolist()
            
            # 抓取即時價
            st.subheader("📊 即時市場數據")
            prices = {}
            for t in tickers:
                prices[t] = yf.Ticker(t).fast_info.last_price
            
            # 建立簡易儀表板
            for t in tickers:
                col1, col2 = st.columns(2)
                col1.metric(f"股票: {t}", f"${prices[t]:.2f}")
        else:
            st.error("❌ 找不到 'ticker' 欄位，請檢查試算表標頭。")

except Exception as e:
    st.error("🆘 致命錯誤：無法讀取 CSV 連結")
    st.write(f"請確認您是否已經點擊『發佈到網路』並選擇了『CSV 格式』。")
    st.write(f"詳細報錯: {e}")
