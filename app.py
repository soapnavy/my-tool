# app.py
# 必要的引用库
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import akshare as ak
from datetime import datetime, timedelta

# --- 1. 页面基础设置 (适配移动端) ---
st.set_page_config(page_title="五日线战法", layout="centered") # 手机端用 centered 留白更自然
st.title("📈 五日线战法量化分析")
st.markdown("基于趋势+量能+风控的强势股主升浪交易模型。")

# --- 2. 顶部参数设置区 (移出侧边栏，适配手机操作) ---
st.markdown("### ⚙️ 参数设置")
col_in1, col_in2 = st.columns(2)
with col_in1:
    data_source = st.selectbox("数据源", ["AkShare (国内A股)", "Yahoo Finance (国际/备用)"])
    ticker_input = st.text_input("股票代码 (如 600026)", value="600026")
with col_in2:
    period_input = st.selectbox("数据范围", ["3mo", "6mo", "1y", "2y"], index=1)
    buy_price_input = st.number_input("您的买入价 (0为未买)", min_value=0.0, value=22.0, step=1.0)

# 手机端友好的全宽按钮
analyze_button = st.button("🚀 执行战法分析", type="primary", use_container_width=True)

# --- 3. 核心功能函数 ---

def format_ticker_yahoo(ticker):
    """为 Yahoo Finance 自动处理 A 股代码后缀"""
    ticker = ticker.strip().upper()
    if ticker.isdigit() and len(ticker) == 6:
        if ticker.startswith('6'):
            return f"{ticker}.SS"  
        elif ticker.startswith('0') or ticker.startswith('3'):
            return f"{ticker}.SZ"  
    return ticker

def get_akshare_dates(period_str):
    """为 AkShare 计算起始和结束日期 (YYYYMMDD)"""
    end_date = datetime.now()
    if period_str == "3mo":
        start_date = end_date - timedelta(days=90)
    elif period_str == "6mo":
        start_date = end_date - timedelta(days=180)
    elif period_str == "1y":
        start_date = end_date - timedelta(days=365)
    elif period_str == "2y":
        start_date = end_date - timedelta(days=730)
    else:
        start_date = end_date - timedelta(days=180)
    return start_date.strftime("%Y%m%d"), end_date.strftime("%Y%m%d")

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_stock_data(ticker, period, source):
    """统一的数据获取路由函数"""
    if "AkShare" in source:
        code = ''.join(filter(str.isdigit, ticker))
        if len(code) != 6:
            raise ValueError("AkShare 模式下，请输入 6 位 A 股纯数字代码！")
            
        start_str, end_str = get_akshare_dates(period)
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_str, end_date=end_str, adjust="qfq")
        
        if df.empty:
            return pd.DataFrame()
            
        df = df.rename(columns={
            "日期": "Date", "开盘": "Open", "收盘": "Close", 
            "最高": "High", "最低": "Low", "成交量": "Volume"
        })
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        df['Close'] = pd.to_numeric(df['Close'])
        df['Volume'] = pd.to_numeric(df['Volume'])
        return df
    else:
        real_ticker = format_ticker_yahoo(ticker)
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        stock = yf.Ticker(real_ticker, session=session)
        return stock.history(period=period)

def analyze_strategy(df, buy_price):
    """战法核心算法：严格对应8条规则"""
    data = df.copy()
    
    # 核心指标计算
    data['MA5'] = data['Close'].rolling(window=5).mean()
    data['Avg_Vol_5'] = data['Volume'].rolling(window=5).mean().shift(1)
    data['Vol_Ratio'] = data['Volume'] / data['Avg_Vol_5']
    data['Is_Massive_Vol'] = data['Vol_Ratio'] >= 1.45
    data['Deviation_MA5'] = (data['Close'] - data['MA5']) / data['MA5']
    data['Is_Vol_Expand'] = data['Volume'] > data['Volume'].shift(1)
    
    latest = data.iloc[-1]
    last_7_days = data.iloc[-7:]
    
    consecutive_expand = 0
    max_consecutive = 0
    for val in last_7_days['Is_Vol_Expand']:
        if val:
            consecutive_expand += 1
            max_consecutive = max(max_consecutive, consecutive_expand)
        else:
            consecutive_expand = 0
            
    massive_vol_count = last_7_days['Is_Massive_Vol'].sum()
    is_above_ma5 = latest['Close'] > latest['MA5']
    
    report_lines = []
    
    # 规则 1
    report_lines.append("**1. 入场基础**：价格必须站稳5日均线之上。")
    report_lines.append(f"> 💡 **状态**：{'✅ 达标' if is_above_ma5 else '❌ 未达标'}")

    # 规则 2
    report_lines.append("\n**2. 成交量验证**：连续三日放量，七日内有巨量。")
    vol_status = "✅ 达标" if (max_consecutive >= 3 and 1 <= massive_vol_count <= 2) else "⚠️ 未完全达标"
    report_lines.append(f"> 💡 **状态**：{vol_status} (最大连放: {max_consecutive}天, 巨量: {massive_vol_count}天)")

    # 规则 3 (包含详细数据推导)
    report_lines.append("\n**3. 巨量标准**：当日成交量≥前期均量1.45倍。")
    if latest['Is_Massive_Vol']:
        report_lines.append(f"> 💡 **状态**：✅ **今日巨量** (量比 {latest['Vol_Ratio']:.2f})")
    else:
        report_lines.append(f"> 💡 **状态**：ℹ️ **今日未达巨量** (量比 {latest['Vol_Ratio']:.2f})")
    
    vol_today = latest['Volume']
    vol_avg5 = latest['Avg_Vol_5']
    report_lines.append(f"> 📊 **数据明细**：今日成交量为 **{vol_today:,.0f}**，前期5日均量为 **{vol_avg5:,.0f}**。")
    report_lines.append(f"> 🧮 **计算结论**：{vol_today:,.0f} ÷ {vol_avg5:,.0f} = **{latest['Vol_Ratio']:.2f}** 倍。")

    # 规则 4
    report_lines.append("\n**4. 买入时机**：买在分歧严重时。")
    report_lines.append("> 💡 **状态**：ℹ️ *结合消息面主观判断*")

    # 规则 5
    dev_pct = latest['Deviation_MA5'] * 100
    report_lines.append("\n**5. 持有逻辑**：偏离度在±7.5%内视为健康。")
    report_lines.append(f"> 💡 **状态**：{'✅ 趋势健康' if -7.5 <= dev_pct <= 7.5 else '⚠️ 偏离过大'} (偏离度 {dev_pct:.2f}%)")

    # 规则 6
    report_lines.append("\n**6. 第一道防线**：跌破5日线超7.5%减仓/离场。")
    report_lines.append(f"> 💡 **状态**：{'🚨 触发防线！' if dev_pct < -7.5 else '🛡️ 安全'}")

    # 规则 7
    report_lines.append("\n**7. 第二道防线**：亏损达20%无条件止损。")
    if buy_price > 0:
        drawdown = (latest['Close'] - buy_price) / buy_price * 100
        report_lines.append(f"> 💡 **状态**：{'💥 触发止损！' if drawdown <= -20.0 else '🛡️ 安全'} (盈亏 {drawdown:.2f}%)")
    else:
        report_lines.append("> 💡 **状态**：ℹ️ 未设置买入价")

    # 规则 8
    report_lines.append("\n**8. 二次入场**：止损后反抽放巨量，偏离度4.5%左右。")
    report_lines.append(f"> 💡 **状态**：{'🎯 触发二次入场！' if latest['Is_Massive_Vol'] and (4.0 <= dev_pct <= 5.0) else 'ℹ️ 未触发'}")

    # 综合判定
    if dev_pct < -7.5 or (buy_price > 0 and (latest['Close'] - buy_price) / buy_price <= -0.20):
        final_decision = "🔴 **综合建议：已触发风控防线，建议离场！**"
    elif is_above_ma5 and massive_vol_count >= 1:
        final_decision = "🟢 **综合建议：符合战法特征，可考虑持有或寻找买点。**"
    else:
        final_decision = "🟡 **综合建议：条件未完全共振，继续观察。**"
        
    return data, report_lines, final_decision

# --- 4. 主界面执行与展示 ---
if analyze_button:
    if ticker_input:
        with st.spinner(f'正在获取 {ticker_input} 数据...'):
            try:
                hist_data = fetch_stock_data(ticker_input, period_input, data_source)
                
                if not hist_data.empty:
                    st.success(f"数据获取成功！")
                    
                    processed_data, report_lines, final_decision = analyze_strategy(hist_data, buy_price_input)
                    
                    # 手机端友好的 2x2 指标卡片布局
                    latest_data = processed_data.iloc[-1]
                    col1, col2 = st.columns(2)
                    col1.metric("最新收盘价", f"{latest_data['Close']:.2f}")
                    col2.metric("5日均线 (MA5)", f"{latest_data['MA5']:.2f}")
                    
                    col3, col4 = st.columns(2)
                    col3.metric("MA5 偏离度", f"{latest_data['Deviation_MA5']*100:.2f}%")
                    col4.metric("最新量比", f"{latest_data['Vol_Ratio']:.2f}")
                    
                    st.divider()
                    
                    # 战法诊断报告
                    st.subheader("🎯 战法诊断报告")
                    st.info(final_decision)
                    for line in report_lines:
                        st.markdown(line)
                        
                    st.divider()
                    
                    # 详细数据表格 (已修复 NaN 导致 int 转换失败的 Bug)
                    st.subheader("📊 近期量价明细")
                    display_df = processed_data[['Close', 'Volume', 'MA5', 'Avg_Vol_5', 'Vol_Ratio', 'Deviation_MA5', 'Is_Massive_Vol']].copy()
                    
                    # 核心修复：使用 fillna(0) 处理前几天的空数据，防止 astype(int) 报错
                    display_df['Deviation_MA5'] = (display_df['Deviation_MA5'].fillna(0) * 100).round(2).astype(str) + '%'
                    display_df['Vol_Ratio'] = display_df['Vol_Ratio'].fillna(0).round(2)
                    display_df['MA5'] = display_df['MA5'].fillna(0).round(2)
                    display_df['Avg_Vol_5'] = display_df['Avg_Vol_5'].fillna(0).round(0).astype(int)
                    
                    display_df = display_df.reset_index().sort_values(by='Date', ascending=False)
                    
                    display_df = display_df.rename(columns={
                        'Date': '日期', 'Close': '收盘价', 'Volume': '成交量',
                        'MA5': '5日线', 'Avg_Vol_5': '5日均量',
                        'Vol_Ratio': '量比', 'Deviation_MA5': '偏离度', 'Is_Massive_Vol': '巨量'
                    })
                    
                    if '日期' in display_df.columns:
                        display_df['日期'] = display_df['日期'].dt.strftime('%m-%d') # 手机端只显示月-日省空间
                        
                    st.dataframe(display_df.head(15), use_container_width=True)
                    
                else:
                    st.warning("获取到的数据为空，请检查代码。")
            except Exception as e:
                st.error(f"分析出错: {e}")
    else:
        st.warning("请先输入股票代码！")
