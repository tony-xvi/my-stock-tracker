import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. 初始化頁面 ---
st.set_page_config(page_title="雲端資產管理系統", layout="wide")
st.title("☁️ 雲端資產管理系統 (Google Sheets 版)")

# --- 2. 建立連線 ---
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 3. 核心數據抓取 ---
@st.cache_data(ttl=600)
def get_market_data(_tickers):
    if not _tickers: return {}, 32.5
    prices = {}
    try:
        fx = yf.Ticker("USDTWD=X").fast_info.last_price
    except:
        fx = 32.5
    for t in _tickers:
        try:
            prices[t] = yf.Ticker(t).fast_info.last_price
        except:
            prices[t] = 0
    return prices, fx

# --- 4. 讀取雲端資料 ---
def load_data():
    df_t = conn.read(worksheet="transactions", ttl=0)
    df_c = conn.read(worksheet="cash_balance", ttl=0)
    df_h = conn.read(worksheet="history", ttl=0)
    return df_t, df_c, df_h

df_t, df_c, df_h = load_data()

# --- 5. 側邊欄選單 ---
menu = st.sidebar.selectbox("切換功能", ["資產總覽", "新增交易紀錄", "現金/歷史管理"])

# --- 6. 資產總覽邏輯 ---
if menu == "資產總覽":
    if df_t.empty or len(df_t.columns) < 2:
        st.info("👋 雲端試算表目前是空的，請開始記錄交易！")
    else:
        cash = float(df_c.iloc[0]['balance'])
        unique_tickers = df_t['ticker'].unique().tolist()
        prices, fx = get_market_data(unique_tickers)
        
        summary_rows = []
        for t in unique_tickers:
            t_data = df_t[df_t['ticker'] == t]
            buys = t_data[t_data['type'] == '買入']
            sells = t_data[t_data['type'] == '賣出']
            
            qty = buys['amount'].sum() - sells['amount'].sum()
            if qty <= 0: continue
            
            avg_cost = (buys['price'] * buys['amount'] + buys['fee']).sum() / buys['amount'].sum()
            curr_p = prices.get(t, 0)
            rate = 1 if ".TW" in t else fx
            
            mkt_val = curr_p * qty * rate
            total_cost = avg_cost * qty * rate
            profit = mkt_val - total_cost
            
            summary_rows.append({
                "代號": t, "持股": qty, "成本": round(avg_cost, 2),
                "現價": round(curr_p, 2), "市值(TWD)": round(mkt_val, 0),
                "損益": round(profit, 0), "報酬率": f"{(profit/total_cost):.2%}" if total_cost > 0 else "0%"
            })
            
        if summary_rows:
            res_df = pd.DataFrame(summary_rows)
            total_stock = res_df["市值(TWD)"].sum()
            st.metric("總資產 (台幣)", f"{round(total_stock + cash, 0):,}")
            st.dataframe(res_df, use_container_width=True)
            st.plotly_chart(px.pie(res_df, values='市值(TWD)', names='代號', title="持股分布"))
        else:
            st.write(f"目前無持股。現金餘額: {cash:,}")

# --- 7. 新增交易 (寫入雲端) ---
elif menu == "新增交易紀錄":
    st.subheader("新增買賣")
    with st.form("add_form"):
        # (這裡省略部分輸入欄位，邏輯與之前相同，但最後使用 conn.update 寫回)
        # 注意：使用 st-gsheets-connection 寫回需要進階權限設定
        st.warning("提醒：若要透過網頁直接『寫入』Google Sheets，您需要按照 Google Cloud Console 的 Service Account 設定進行授權。")
        st.write("目前最穩定的方法是：直接在 Google Sheets 貼上您的交易紀錄，網頁會自動同步更新。")
