import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from datetime import datetime

# ==========================================
# 1. 設定區：請填入你的 Google Sheet ID
# ==========================================
# 網址中 /d/ 之後到 /edit 之前的那串字元就是 ID
SHEET_ID = "13n6P6Kcnmzj_xx2kTJJYlMXKrJ226HlnEV2rV_CjYBo" 

# ==========================================
# 2. 核心功能：讀取 Google Sheets (免金鑰穩定版)
# ==========================================
def get_sheet_url(sheet_name):
    return f"https://docs.google.com/spreadsheets/d/13n6P6Kcnmzj_xx2kTJJYlMXKrJ226HlnEV2rV_CjYBo/edit?usp=sharing"

@st.cache_data(ttl=300) # 每 5 分鐘自動刷新一次
def load_all_data():
    try:
        df_t = pd.read_csv(get_sheet_url("transactions"))
        df_c = pd.read_csv(get_sheet_url("cash_balance"))
        df_h = pd.read_csv(get_sheet_url("history"))
        return df_t, df_c, df_h
    except Exception as e:
        st.error(f"連線失敗：請確認試算表已開啟『知道連結的使用者即可查看』。錯誤詳情: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

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
            p = yf.Ticker(t).fast_info.last_price
            prices[t] = p if p is not None else 0
        except:
            prices[t] = 0
    return prices, fx

# ==========================================
# 3. 頁面介面
# ==========================================
st.set_page_config(page_title="Global Asset Pro (Cloud)", layout="wide")
st.title("☁️ 雲端資產實時監控儀表板")

# 讀取資料
df_t, df_c, df_h = load_all_data()

# 選單
menu = st.sidebar.selectbox("功能選單", ["資產總覽 (Dashboard)", "歷史交易明細", "如何更新數據"])

if menu == "資產總覽 (Dashboard)":
    if df_t.empty or "ticker" not in df_t.columns:
        st.warning("⚠️ 偵測到試算表內容為空或格式錯誤，請檢查 Google Sheets 分頁名稱與欄位。")
    else:
        # 現金處理
        current_cash = float(df_c.iloc[0]['balance']) if not df_c.empty else 0
        
        # 股票處理
        unique_tickers = df_t['ticker'].dropna().unique().tolist()
        with st.spinner('正在同步全球市場報價...'):
            prices, fx = get_market_data(unique_tickers)
            
        summary = []
        for t in unique_tickers:
            t_data = df_t[df_t['ticker'] == t]
            buys = t_data[t_data['type'] == '買入']
            sells = t_data[t_data['type'] == '賣出']
            
            qty = buys['amount'].sum() - sells['amount'].sum()
            if qty <= 0: continue
            
            # 計算成本 (ROI 邏輯)
            total_buy_cost = (buys['price'] * buys['amount'] + buys['fee']).sum()
            avg_cost = total_buy_cost / buys['amount'].sum()
            
            now_p = prices.get(t, 0)
            rate = 1 if ".TW" in t else fx
            
            market_val = now_p * qty * rate
            total_cost = avg_cost * qty * rate
            profit = market_val - total_cost
            roi = (profit / total_cost) if total_cost > 0 else 0
            
            summary.append({
                "類別": "台股" if ".TW" in t else "美股",
                "代號": t, "持股": qty, "平均成本": round(avg_cost, 2),
                "現價": round(now_p, 2), "市值(TWD)": round(market_val, 0),
                "損益": round(profit, 0), "報酬率": f"{roi:.2%}"
            })
            
        if summary:
            res_df = pd.DataFrame(summary)
            total_stock_val = res_df["市值(TWD)"].sum()
            grand_total = total_stock_val + current_cash
            total_profit = res_df["損益"].sum()
            
            # --- 頂部數據卡片 ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("總資產價值 (TWD)", f"${grand_total:,.0f}")
            c2.metric("總未實現損益", f"${total_profit:,.0f}", delta=f"{(total_profit/(grand_total-total_profit)):.2%}")
            c3.metric("手邊現金", f"${current_cash:,.0f}")
            c4.metric("即時美金匯率", f"{fx:.2f}")
            
            # --- 圖表區 ---
            col_l, col_r = st.columns(2)
            with col_l:
                st.plotly_chart(px.pie(res_df, values='市值(TWD)', names='代號', hole=0.4, title="股票分配比例"), use_container_width=True)
            with col_r:
                if not df_h.empty and "total_value" in df_h.columns:
                    st.plotly_chart(px.line(df_h, x="date", y="total_value", title="資產成長趨勢 (歷史淨值)"), use_container_width=True)
                else:
                    st.info("💡 在 Google Sheets 的 history 分頁加入資料，即可看到成長曲線。")
            
            st.subheader("📋 庫存明細")
            st.dataframe(res_df, use_container_width=True)
        else:
            st.info("目前無持倉股票，請在試算表中新增買入紀錄。")

elif menu == "歷史交易明細":
    st.header("📜 交易紀錄存檔")
    st.dataframe(df_t, use_container_width=True)

elif menu == "如何更新數據":
    st.header("📘 使用指南")
    st.write("""
    1. **新增買賣**：直接打開您的 Google Sheets，在 `transactions` 分頁最後一行輸入新紀錄。
    2. **調整現金**：在 `cash_balance` 分頁修改數字。
    3. **歷史追蹤**：每天將您的總資產數字填入 `history` 分頁，網頁就會自動畫出曲線。
    4. **即時性**：本網頁每 5 分鐘會與 Google Sheets 同步一次，手動重新整理網頁可立即強制更新。
    """)
