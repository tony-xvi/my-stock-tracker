try:
    df = pd.read_csv(CSV_URL)
    
    # 診斷訊息
    st.write("--- 診斷資訊 ---")
    st.write(f"讀取到的欄位有: {list(df.columns)}")
    st.write(f"資料筆數: {len(df)}")
    
    if df.empty or len(df.columns) < 2:
        st.warning("⚠️ 雖然連線成功，但讀取的內容是空的。")
        st.info("請檢查：您的 transactions 分頁第一行是否有填寫標題（date, ticker, type...）？")
    else:
        st.success("✅ 成功獲取資料！")
        st.dataframe(df) # 顯示前幾行看看
