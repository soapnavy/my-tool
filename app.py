# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import requests

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="五日线战法量化工具", layout="wide")
st.title("📈 《五日线战法》实战量化分析")
st.markdown("基于趋势+量能+风控的强势股主升浪交易模型。")

# --- 2. 侧边栏 / 用户输入区 ---
with st.sidebar:
    st.header("⚙️ 参数设置")
    ticker_input = st.text_input("股票代码 (如 600026, AAPL)", value="600026")
    buy_price_input = st.number_input("您的买入价格 (选填，0表示未买入)", min_value=0.0, value=22.0, step=1.0)
    period_input = st.selectbox("获取历史数据范围", ["3mo", "6mo", "1y", "2y"], index=1)
    analyze_button = st.button("🚀 执行战法分析", type="primary")

# --- 3. 核心功能函数 ---

def format_ticker(ticker):
    """自动处理 A 股代码后缀"""
    ticker = ticker.strip().upper()
    # 如果是纯数字且长度为6，自动判断沪深市
    if ticker.isdigit() and len(ticker) == 6:
        if ticker.startswith('6'):
            return f"{ticker}.SS"  # 沪市
        elif ticker.startswith('0') or ticker.startswith('3'):
            return f"{ticker}.SZ"  # 深市/创业板
    return ticker

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker, period):
    """
    带缓存和防封禁机制的数据获取函数。
    ttl=3600 表示缓存1小时，避免重复点击按钮导致被封 IP。
    """
    # 伪装浏览器请求头，绕过 Yahoo Finance 的基础反爬限制
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36'
    })
    
    stock = yf.Ticker(ticker, session=session)
    return stock.history(period=period)

def analyze_strategy(df, buy_price):
    """战法核心算法"""
    data = df.copy()
    
    # 计算核心指标
    data['MA5'] = data['Close'].rolling(window=5).mean()
    data['Avg_Vol_5'] = data['Volume'].rolling(window=5).mean().shift(1)
    data['Vol_Ratio'] = data['Volume'] / data['Avg_Vol_5']
    data['Is_Massive_Vol'] = data['Vol_Ratio'] >= 1.45
    data['Deviation_MA5'] = (data['Close'] - data['MA5']) / data['MA5']
    
    latest = data.iloc[-1]
    last_7_days = data.iloc[-7:]
    
    conclusions = []
    status_color = "🟢" 
    
    # 规则1: 趋势 (必须站上5日线)
    is_above_ma5 = latest['Close'] > latest['MA5']
    if is_above_ma5:
        conclusions.append("✅ **趋势达标**：当前股价已站上5日均线。")
    else:
        conclusions.append("❌ **趋势未达标**：当前股价在5日均线之下，不符合入场基础。")
        status_color = "🔴"
        
    # 规则2 & 3: 量能 (7个交易日内出现1-2次1.45倍巨量)
    massive_vol_count = last_7_days['Is_Massive_Vol'].sum()
    if massive_vol_count >= 1:
        conclusions.append(f"✅ **量能达标**：近7个交易日内出现了 {massive_vol_count} 次巨量(≥1.45倍)，资金交投活跃。")
    else:
        conclusions.append("⚠️ **量能欠缺**：近7个交易日内未出现明显巨量，需警惕动能不足。")
        
    # 规则5: 偏离度防线 (跌破5日线超7.5%离场)
    if latest['Deviation_MA5'] < -0.075:
        conclusions.append("🚨 **触发第一道防线**：收盘价跌破5日均线超过7.5%，**建议强制减仓或离场！**")
        status_color = "🔴"
    elif is_above_ma5:
        conclusions.append(f"🛡️ **持仓安全**：当前偏离度为 {latest['Deviation_MA5']*100:.2f}%，在安全范围内。")

    # 规则6: 绝对止损 (跌破买入价20%无条件止损)
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

# --- 4. 主界面执行与展示 ---
if analyze_button:
    if ticker_input:
        real_ticker = format_ticker(ticker_input)
        
        with st.spinner(f'正在获取 {real_ticker} 的数据并执行分析 (已启用防封禁机制)...'):
            try:
                hist_data = fetch_stock_data(real_ticker, period_input)
                
                if not hist_data.empty:
                    st.success(f"成功获取 {real_ticker} 数据！")
                    
                    # 调用核心算法
                    processed_data, rules_feedback, final_decision = analyze_strategy(hist_data, buy_price_input)
                    
                    # 顶层指标卡片展示最新数据
                    latest_data = processed_data.iloc[-1]
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("最新收盘价", f"{latest_data['Close']:.2f}")
                    col2.metric("5日均线 (MA5)", f"{latest_data['MA5']:.2f}")
                    col3.metric("MA5 偏离度", f"{latest_data['Deviation_MA5']*100:.2f}%")
                    col4.metric("最新量比", f"{latest_data['Vol_Ratio']:.2f}")
                    
                    st.divider()
                    
                    # 战法结论输出
                    st.subheader("🎯 战法诊断报告")
                    st.info(final_decision)
                    for feedback in rules_feedback:
                        st.markdown(feedback)
                        
                    st.divider()
                    
                    # 详细数据表格 (全中文显示)
                    st.subheader("📊 近期量价数据明细 (最近15个交易日)")
                    display_df = processed_data[['Close', 'Volume', 'MA5', 'Avg_Vol_5', 'Vol_Ratio', 'Deviation_MA5', 'Is_Massive_Vol']].copy()
                    
                    # 格式化百分比和保留两位小数
                    display_df['Deviation_MA5'] = (display_df['Deviation_MA5'] * 100).round(2).astype(str) + '%'
                    display_df['Vol_Ratio'] = display_df['Vol_Ratio'].round(2)
                    display_df['MA5'] = display_df['MA5'].round(2)
                    display_df['Avg_Vol_5'] = display_df['Avg_Vol_5'].round(0).astype(int) # 成交量取整
                    
                    # 重置索引并按时间倒序
                    display_df = display_df.reset_index().sort_values(by='Date', ascending=False)
                    
                    # 将列名重命名为中文
                    display_df = display_df.rename(columns={
                        'Date': '交易日期',
                        'Close': '收盘价',
                        'Volume': '当日成交量',
                        'MA5': '5日均线',
                        'Avg_Vol_5': '前期5日均量',
                        'Vol_Ratio': '量比 (巨量标准≥1.45)',
                        'Deviation_MA5': '5日线偏离度',
                        'Is_Massive_Vol': '是否达标巨量'
                    })
                    
                    st.dataframe(display_df.head(15), use_container_width=True)
                    
                else:
                    st.warning(f"获取到的 {real_ticker} 数据为空，请检查该股票是否停牌或退市。")
            except Exception as e:
                st.error(f"分析出错: {e}\n\n提示：如果依然报错 Too Many Requests，说明该云服务器 IP 暂时被雅虎财经硬封锁，请等待几分钟后重试。")
    else:
        st.warning("请先输入股票代码！")
else:
    st.info("👈 请在左侧输入股票代码（国内A股直接输6位数字即可自动识别），点击执行分析。")
