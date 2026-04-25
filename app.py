def load_all_data():
    # 這是測試連線用的
    test_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
    
    try:
        # 嘗試讀取第一個分頁（通常是 transactions）
        # 如果你不知道 GID，我們改用分頁索引
        df_t = pd.read_csv(f"{test_url}&gid=0") 
        
        # 這裡我建議你直接在程式碼中填入 GID
        # 當你點擊試算表下方的不同分頁時，網址最後面的 gid= 數字會變
        # 請根據你實際的 gid 修改下方數字
        df_c = pd.read_csv(f"{test_url}&gid=12345678") # <--- 換成 cash_balance 的 gid
        df_h = pd.read_csv(f"{test_url}&gid=87654321") # <--- 換成 history 的 gid
        
        return df_t, df_c, df_h
    except Exception as e:
        st.error("🆘 讀取失敗！")
        st.write(f"當前錯誤訊息: {e}")
        st.info("💡 提示：請確保您的 Google 試算表已經點擊『共用』，並設定為『任何知道連結的使用者都能查看』。")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
