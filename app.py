# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="五日线战法量化工具", layout="wide")
st.title("📈 《五日线战法》实战量化分析")
st.markdown("基于趋势+量能+风控的强势股主升浪交易模型。")

# --- 2. 侧边栏 / 用户输入区 ---
with st.sidebar:
    st.header("⚙️ 参数设置")
    ticker_input = st.text_input("股票代码 (如 AAPL, TSLA)", value="AAPL")
    
    # 新增：买入价格输入框，用于计算强制止损
    buy_price_input = st.number_input("您的买入价格 (选填，0表示未买入)", min_value=0.0, value=0.0, step=1.0)
    
    period_input = st.selectbox("获取历史数据范围", ["3mo", "6mo", "1y", "2y"], index=1)
    analyze_button = st.button("🚀 执行战法分析", type="primary")

# --- 3. 核心战法逻辑 ---
def analyze_strategy(df, buy_price):
    """
    时间复杂度: O(N)，N 为获取的历史交易天数，Pandas 向量化运算极快。
    空间复杂度: O(N)，新增了几个指标列。
    """
    data = df.copy()
    
    # 1. 计算 5日均线 (MA5)
    data['MA5'] = data['Close'].rolling(window=5).mean()
    
    # 2. 计算前期均量 (使用前5日的平均成交量作为基准)
    data['Avg_Vol_5'] = data['Volume'].rolling(window=5).mean().shift(1)
    
    # 3. 计算量比 (当日成交量 / 前期均量)，判断是否达到 1.45 倍巨量标准
    data['Vol_Ratio'] = data['Volume'] / data['Avg_Vol_5']
    data['Is_Massive_Vol'] = data['Vol_Ratio'] >= 1.45
    
    # 4. 计算收盘价偏离 5日均线的幅度
    data['Deviation_MA5'] = (data['Close'] - data['MA5']) / data['MA5']
    
    # 获取最新一天的数据和过去7天的数据
    latest = data.iloc[-1]
    last_7_days = data.iloc[-7:]
    
    # --- 战法规则判定 ---
    conclusions = []
    status_color = "🟢" # 默认偏乐观
    
    # 规则一：看趋势 (必须站上5日线)
    is_above_ma5 = latest['Close'] > latest['MA5']
    if is_above_ma5:
        conclusions.append("✅ **趋势达标**：当前股价已站上5日均线。")
    else:
        conclusions.append("❌ **趋势未达标**：当前股价在5日均线之下，不符合入场基础。")
        status_color = "🔴"
        
    # 规则二 & 三：看确认 (7个交易日内出现1-2次1.45倍巨量)
    massive_vol_count = last_7_days['Is_Massive_Vol'].sum()
    if massive_vol_count >= 1:
        conclusions.append(f"✅ **量能达标**：近7个交易日内出现了 {massive_vol_count} 次巨量(≥1.45倍)，资金交投活跃。")
    else:
        conclusions.append("⚠️ **量能欠缺**：近7个交易日内未出现明显巨量，需警惕动能不足。")
        
    # 规则五：第一道防线 (跌破5日线超7.5%离场)
    if latest['Deviation_MA5'] < -0.075:
        conclusions.append("🚨 **触发第一道防线**：收盘价跌破5日均线超过7.5%，**建议强制减仓或离场！**")
        status_color = "🔴"
    elif is_above_ma5:
        conclusions.append(f"🛡️ **持仓安全**：当前偏离度为 {latest['Deviation_MA5']*100:.2f}%，在安全范围内。")

    # 规则六：第二道防线 (跌破买入价20%无条件止损)
    if buy_price > 0:
        drawdown = (latest['Close'] - buy_price) / buy_price
        if drawdown <= -0.20:
            conclusions.append(f"💥 **触发绝对止损**：当前亏损达 {drawdown*100:.2f}% (超20%)，**必须无条件止损离场！**")
            status_color = "🔴"
        else:
            conclusions.append(f"📊 **盈亏状态**：当前较买入价盈亏比例为 {drawdown*100:.2f}%。")
            
    # 综合判定
    if status_color == "🔴":
        final_decision = "🔴 **综合建议：风险较高，建议观望或严格执行止损纪律。**"
    elif is_above_ma5 and massive_vol_count >= 1:
        final_decision = "🟢 **综合建议：符合战法特征，趋势健康，可考虑持有或寻找买点。**"
    else:
        final_decision = "🟡 **综合建议：条件未完全共振，建议继续观察量价配合情况。**"
        
    return data, conclusions, final_decision

# --- 4. 主界面数据展示 ---
if analyze_button:
    if ticker_input:
        with st.spinner(f'正在分析 {ticker_input} 的战法数据...'):
            try:
                stock = yf.Ticker(ticker_input)
                hist_data = stock.history(period=period_input)
                
                if not hist_data.empty:
                    # 调用核心算法
                    processed_data, rules_feedback, final_decision = analyze_strategy(hist_data, buy_price_input)
                    
                    # 顶层指标卡片展示最新数据
                    latest_data = processed_data.iloc[-1]
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("最新收盘价", f"${latest_data['Close']:.2f}")
                    col2.metric("5日均线 (MA5)", f"${latest_data['MA5']:.2f}")
                    col3.metric("MA5 偏离度", f"{latest_data['Deviation_MA5']*100:.2f}%")
                    col4.metric("最新量比", f"{latest_data['Vol_Ratio']:.2f}")
                    
                    st.divider()
                    
                    # 战法结论输出
                    st.subheader("🎯 战法诊断报告")
                    st.info(final_decision)
                    for feedback in rules_feedback:
                        st.markdown(feedback)
                        
                    st.divider()
                    
                    # 详细数据表格
                    st.subheader("📊 近期量价数据明细 (最近15个交易日)")
                    # 格式化显示数据，方便阅读
                    display_df = processed_data[['Close', 'Volume', 'MA5', 'Avg_Vol_5', 'Vol_Ratio', 'Deviation_MA5', 'Is_Massive_Vol']].copy()
                    display_df['Deviation_MA5'] = (display_df['Deviation_MA5'] * 100).round(2).astype(str) + '%'
                    display_df['Vol_Ratio'] = display_df['Vol_Ratio'].round(2)
                    display_df = display_df.reset_index().sort_values(by='Date', ascending=False)
                    
                    st.dataframe(display_df.head(15), use_container_width=True)
                    
                else:
                    st.warning("数据获取为空，请检查股票代码。")
            except Exception as e:
                st.error(f"分析出错: {e}")
    else:
        st.warning("请先输入股票代码！")
else:
    st.info("👈 请在左侧输入股票代码（可选填买入价），点击执行分析。")
