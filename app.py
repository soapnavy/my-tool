import streamlit as st
import yfinance as yf
import pandas as pd
# 如果后续战法需要复杂技术指标，可能还需要 import pandas_ta 或 ta

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="量化战法分析工具", layout="wide")
st.title("📈 专属股票战法分析工具")
st.markdown("输入股票代码，一键获取战法分析结论。")

# --- 2. 侧边栏 / 用户输入区 ---
with st.sidebar:
    st.header("参数设置")
    # 允许用户输入任意股票代码，默认苹果
    ticker_input = st.text_input("请输入股票代码 (如 AAPL, TSLA, BABA)", value="AAPL")
    # 允许用户选择分析的时间跨度
    period_input = st.selectbox("获取历史数据范围", ["1mo", "3mo", "6mo", "1y", "2y"], index=2)
    analyze_button = st.button("🚀 开始执行战法分析")

# --- 3. 核心战法逻辑 (等待填入具体规则) ---
def analyze_strategy(df):
    """
    这里是核心算法区域！
    目前是占位符，需要你告诉我具体的战法规则后，我来完善这里的代码。
    例如：计算 MA5, MA20，判断金叉死叉，或者计算特定波动率等。
    """
    # 复制一份数据避免修改原始数据
    data = df.copy()
    
    # 假设战法规则 1：计算 5 日均线 (示例)
    data['MA5'] = data['Close'].rolling(window=5).mean()
    
    # 假设战法结论生成 (示例)
    latest_close = data['Close'].iloc[-1]
    latest_ma5 = data['MA5'].iloc[-1]
    
    if latest_close > latest_ma5:
        conclusion = "🟢 **战法结论：** 当前股价站上 5 日均线，呈现强势（示例结论，待替换为真实战法）。"
    else:
        conclusion = "🔴 **战法结论：** 当前股价跌破 5 日均线，呈现弱势（示例结论，待替换为真实战法）。"
        
    return data, conclusion

# --- 4. 主界面数据展示与执行 ---
if analyze_button:
    if ticker_input:
        with st.spinner(f'正在从云端获取 {ticker_input} 的数据并执行战法计算...'):
            try:
                # 获取数据
                stock = yf.Ticker(ticker_input)
                hist_data = stock.history(period=period_input)
                
                if not hist_data.empty:
                    st.success(f"{ticker_input} 数据获取成功！")
                    
                    # 调用战法核心算法
                    processed_data, final_conclusion = analyze_strategy(hist_data)
                    
                    # --- 模块 A：输出战法结论 ---
                    st.subheader("🎯 战法分析结论")
                    st.info(final_conclusion) # 醒目地展示结论
                    
                    # --- 模块 B：展示计算后的详细数据 ---
                    st.subheader("📊 详细指标数据 (近期)")
                    # 将索引(日期)转换为普通列，并倒序排列，方便看最新数据
                    display_df = processed_data.reset_index().sort_values(by='Date', ascending=False)
                    st.dataframe(display_df.head(20)) # 只展示最近20天的数据
                    
                else:
                    st.warning("获取到的数据为空，请检查股票代码是否正确（美股直接输代码，港股如 0700.HK）。")
                    
            except Exception as e:
                st.error(f"分析过程中发生错误: {e}")
    else:
        st.warning("请先在左侧输入股票代码！")
else:
    st.info("👈 请在左侧输入股票代码并点击【开始执行战法分析】")
