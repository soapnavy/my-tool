// app.py
import streamlit as st
import yfinance as yf
import pandas as pd

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="量化工具测试", layout="wide")

# --- 2. 核心界面输出（必须有这些，网页才不会空白） ---
st.title("📈 我的量化分析工具")
st.write("恭喜！环境配置成功，网页可以正常显示了。")

# --- 3. 测试 yfinance 数据获取 ---
st.subheader("苹果 (AAPL) 近期股价数据测试")

try:
    # 增加状态提示，防止网络卡顿时用户以为死机
    with st.spinner('正在从 yfinance 获取数据，请稍候...'):
        # 获取苹果公司股票对象
        aapl = yf.Ticker("AAPL")
        # 获取过去 1 个月的历史数据
        hist_data = aapl.history(period="1mo")
        
        if not hist_data.empty:
            st.success("数据获取成功！")
            # 在网页上以表格形式展示数据
            st.dataframe(hist_data)
        else:
            st.warning("获取到的数据为空，请检查网络或股票代码。")
            
except Exception as e:
    # 捕获并显示具体的错误信息，方便排查
    st.error(f"数据获取失败，错误信息: {e}")

// --- 测试入口 ---
// 将此代码覆盖到你的 app.py，提交到 GitHub。
// 回到你的 Streamlit 网页，刷新页面（或等待自动刷新），即可看到带表格的界面。
