import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import sqlite3
from datetime import datetime

# --- 1. 資料庫初始化 ---
def init_db():
    conn = sqlite3.connect('assets_pro_v3.db')
    c = conn.cursor()
    # 交易紀錄表
    c.execute('''CREATE TABLE IF NOT EXISTS transactions 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  date TEXT, ticker TEXT, type TEXT, price REAL, amount REAL, fee REAL)''')
    # 現金餘額表
    c.execute('''CREATE TABLE IF NOT EXISTS cash_balance (id INTEGER PRIMARY KEY, balance REAL)''')
    # 歷史淨值表 (記錄每日總額)
    c.execute('''CREATE TABLE IF NOT EXISTS history (date TEXT PRIMARY KEY, total_value REAL)''')
    
    # 初始現金設為 0
    c.execute("SELECT count(*) FROM cash_balance")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO cash_balance (id, balance) VALUES (1, 0)")
    conn.commit()
    conn.close()

init_db()

# --- 2. 核心數據抓取 (含快取與錯誤處理) ---
@st.cache_data(ttl=600)
def get_market_data(_tickers):
    if not _tickers:
        return {}, 32.5
    
    prices = {}
    try:
        # 獲取美金對台幣匯率
        fx_ticker = yf.Ticker("USDTWD=X")
        usd_twd = fx_ticker.fast_info.last_price
    except:
        usd_twd = 32.5  # 保底匯率
        
    for t in _tickers:
        try:
            stock = yf.Ticker(t)
            p = stock.fast_info.last_price
            prices[t] = p if p is not None else 0
        except:
            prices[t] = 0
    return prices, usd_twd

# --- 3. 介面設定 ---
st.set_page_config(page_title="Global Asset Pro", layout="wide", page_icon="📈")
st.sidebar.title("💎 投資組合管理")
menu = st.sidebar.selectbox("切換功能", ["資產總覽", "交易紀錄與報表", "新增交易", "現金/歷史管理"])

# --- 4. 功能模組：資產總覽 ---
if menu == "資產總覽":
    st.header("🏢 資產總覽 (Overview)")
    
    conn = sqlite3.connect('assets_pro_v3.db')
    df_t = pd.read_sql_query("SELECT * FROM transactions", conn)
    cash = pd.read_sql_query("SELECT balance FROM cash_balance WHERE id=1", conn).iloc[0,0]
    conn.close()

    if df_t.empty:
        st.info("👋 目前尚無交易紀錄。請先至「現金/歷史管理」設定本金，再到「新增交易」買入股票。")
    else:
        # 轉換為 List 避免快取錯誤
        unique_tickers = df_t['ticker'].unique().tolist()
        with st.spinner('獲取即時報價中...'):
            prices, fx = get_market_data(unique_tickers)
        
        summary_rows = []
        for t in unique_tickers:
            t_data = df_t[df_t['ticker'] == t]
            buys = t_data[t_data['type'] == '買入']
            sells = t_data[t_data['type'] == '賣出']
            
            qty = buys['amount'].sum() - sells['amount'].sum()
            if qty <= 0: continue
            
            # 加權平均成本
            total_buy_cost = (buys['price'] * buys['amount'] + buys['fee']).sum()
            avg_cost = total_buy_cost / buys['amount'].sum()
            
            now_p = prices.get(t, 0)
            is_tw = ".TW" in t
            rate = 1 if is_tw else fx
            
            mkt_val = now_p * qty * rate
            total_cost = avg_cost * qty * rate
            profit = mkt_val - total_cost
            roi = (profit / total_cost) if total_cost > 0 else 0
            
            summary_rows.append({
                "類別": "台股" if is_tw else "美股",
                "代號": t, "持股": qty, "平均成本": round(avg_cost, 2),
                "現價": round(now_p, 2), "市值 (TWD)": round(mkt_val, 0),
                "損益": round(profit, 0), "報酬率": f"{roi:.2%}",
                "raw_roi": roi
            })
        
        if summary_rows:
            res_df = pd.DataFrame(summary_rows)
            total_stock_val = res_df["市值 (TWD)"].sum()
            total_profit = res_df["損益"].sum()
            grand_total = total_stock_val + cash
            
            # --- 頂部指標 ---
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("總資產 (TWD)", f"{grand_total:,.0f}")
            c2.metric("總帳面損益", f"{total_profit:,.0f}", delta=f"{(total_profit/grand_total):.2%}")
            c3.metric("現金部位", f"{cash:,.0f}")
            c4.metric("USD/TWD", f"{fx:.2f}")
            
            # --- 圖表區 ---
            col_l, col_r = st.columns(2)
            with col_l:
                fig_pie = px.pie(res_df, values='市值 (TWD)', names='代號', hole=0.4, title="股票資產分布")
                st.plotly_chart(fig_pie, use_container_width=True)
            with col_r:
                struct_df = pd.DataFrame([{"項": "股票", "值": total_stock_val}, {"項": "現金", "值": cash}])
                st.plotly_chart(px.pie(struct_df, values='值', names='項', title="資產結構 (股票 vs 現金)"), use_container_width=True)
            
            st.subheader("📋 即時持股清單")
            st.dataframe(res_df.drop(columns=['raw_roi']), use_container_width=True)
        else:
            st.write(f"目前無持倉。現金餘額: {cash:,}")

# --- 5. 功能模組：新增交易 ---
elif menu == "新增交易":
    st.header("📝 新增買賣紀錄")
    with st.form("trade_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        date = col1.date_input("交易日期", datetime.now())
        ticker = col1.text_input("股票代號 (例: 2330.TW, TSLA)").upper()
        ttype = col2.selectbox("交易類型", ["買入", "賣出"])
        price = col2.number_input("成交單價", min_value=0.0, step=0.01)
        amount = col1.number_input("交易數量 (股)", min_value=0.0, step=1.0)
        fee = col2.number_input("手續費/稅 (TWD 或 原幣)", min_value=0.0)
        
        if st.form_submit_button("提交交易紀錄"):
            if ticker and amount > 0:
                conn = sqlite3.connect('assets_pro_v3.db')
                conn.execute("INSERT INTO transactions (date, ticker, type, price, amount, fee) VALUES (?,?,?,?,?,?)",
                          (date.strftime("%Y-%m-%d"), ticker, ttype, price, amount, fee))
                # 簡單匯率估算扣款
                est_fx = 32.5 if ".TW" not in ticker else 1
                flow = (price * amount * est_fx) + (fee if ".TW" in ticker else fee * est_fx)
                if ttype == "買入":
                    conn.execute("UPDATE cash_balance SET balance = balance - ? WHERE id=1", (flow,))
                else:
                    conn.execute("UPDATE cash_balance SET balance = balance + ? WHERE id=1", (flow,))
                conn.commit()
                conn.close()
                st.success(f"成功紀錄 {ticker} {ttype}")
            else:
                st.error("請填寫正確代號與數量")

# --- 6. 功能模組：報表 ---
elif menu == "交易紀錄與報表":
    st.header("📜 歷史交易清單")
    conn = sqlite3.connect('assets_pro_v3.db')
    df_history = pd.read_sql_query("SELECT * FROM transactions ORDER BY date DESC", conn)
    conn.close()
    st.dataframe(df_history, use_container_width=True)

# --- 7. 功能模組：現金與歷史管理 ---
elif menu == "現金/歷史管理":
    st.header("⚙️ 帳戶管理")
    conn = sqlite3.connect('assets_pro_v3.db')
    curr_cash = pd.read_sql_query("SELECT balance FROM cash_balance WHERE id=1", conn).iloc[0,0]
    
    # 現金調整
    new_cash = st.number_input("手動調整現金總額 (TWD)", value=float(curr_cash))
    if st.button("更新現金餘額"):
        conn.execute("UPDATE cash_balance SET balance = ? WHERE id=1", (new_cash,))
        conn.commit()
        st.success("現金已更新")

    st.divider()
    
    # 歷史淨值紀錄
    st.subheader("📈 歷史淨值追蹤")
    if st.button("📌 紀錄今日資產總額"):
        # 這裡需要重複一次計算總額的邏輯 (簡化處理)
        df_t = pd.read_sql_query("SELECT * FROM transactions", conn)
        tickers = df_t['ticker'].unique().tolist()
        ps, f_rate = get_market_data(tickers)
        stock_sum = 0
        for t in tickers:
            t_data = df_t[df_t['ticker'] == t]
            q = t_data[t_data['type'] == '買入']['amount'].sum() - t_data[t_data['type'] == '賣出']['amount'].sum()
            if q > 0:
                stock_sum += q * ps.get(t, 0) * (1 if ".TW" in t else f_rate)
        
        today_total = stock_sum + curr_cash
        today_str = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT OR REPLACE INTO history (date, total_value) VALUES (?,?)", (today_str, today_total))
        conn.commit()
        st.success(f"已紀錄 {today_str} 總資產為 ${today_total:,.0f}")

    # 顯示歷史折線圖
    df_h = pd.read_sql_query("SELECT * FROM history ORDER BY date", conn)
    if not df_h.empty:
        fig_line = px.line(df_h, x="date", y="total_value", title="個人資產成長曲線", markers=True)
        st.plotly_chart(fig_line, use_container_width=True)
    
    conn.close()