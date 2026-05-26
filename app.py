# app.py
import streamlit as st
import yfinance as yf
import pandas as pd
import requests
import akshare as ak  # 新增：国内开源金融数据接口
from datetime import datetime, timedelta

# --- 1. 页面基础设置 ---
st.set_page_config(page_title="五日线战法量化工具", layout="wide")
st.title("📈 《五日线战法》实战量化分析")
st.markdown("基于趋势+量能+风控的强势股主升浪交易模型。")

# --- 2. 侧边栏 / 用户输入区 ---
with st.sidebar:
    st.header("⚙️ 参数设置")
    
    # 新增：数据源选择
    data_source = st.selectbox(
        "选择数据源", 
        ["AkShare (国内A股推荐/东方财富源)", "Yahoo Finance (国际/备用)"], 
        index=0,
        help="国内A股建议使用 AkShare，速度更快且无网络限制。"
    )
    
    ticker_input = st.text_input("股票代码 (如 600026, AAPL)", value="600026")
    buy_price_input = st.number_input("您的买入价格 (选填，0表示未买入)", min_value=0.0, value=22.0, step=1.0)
    period_input = st.selectbox("获取历史数据范围", ["3mo", "6mo", "1y", "2y"], index=1)
    analyze_button = st.button("🚀 执行战法分析", type="primary")

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
        # --- 使用国内 AkShare 数据源 (东方财富/新浪) ---
        # 提取纯数字代码
        code = ''.join(filter(str.isdigit, ticker))
        if len(code) != 6:
            raise ValueError("AkShare 模式下，请输入 6 位 A 股纯数字代码！")
            
        start_str, end_str = get_akshare_dates(period)
        # 获取 A股日K历史数据 (qfq = 前复权，保证技术分析准确)
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_str, end_date=end_str, adjust="qfq")
        
        if df.empty:
            return pd.DataFrame()
            
        # 统一格式化为 Yahoo 风格的列名，以便下游算法无缝对接
        df = df.rename(columns={
            "日期": "Date",
            "开盘": "Open",
            "收盘": "Close",
            "最高": "High",
            "最低": "Low",
            "成交量": "Volume",
            "成交额": "Amount"
        })
        df['Date'] = pd.to_datetime(df['Date'])
        df.set_index('Date', inplace=True)
        
        # 确保核心列为数值类型
        df['Close'] = pd.to_numeric(df['Close'])
        df['Volume'] = pd.to_numeric(df['Volume'])
        return df
        
    else:
        # --- 使用 Yahoo Finance 数据源 ---
        real_ticker = format_ticker_yahoo(ticker)
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        stock = yf.Ticker(real_ticker, session=session)
        return stock.history(period=period)

def analyze_strategy(df, buy_price):
    """战法核心算法：严格对应8条规则"""
    data = df.copy()
    
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
    report_lines.append("**1. 入场基础**：价格必须站稳5日均线之上，此为第一前提，否则不看不做。")
    if is_above_ma5:
        report_lines.append(f"> 💡 **当前状态**：✅ **达标** (最新收盘价 {latest['Close']:.2f} > 5日均线 {latest['MA5']:.2f})")
    else:
        report_lines.append(f"> 💡 **当前状态**：❌ **未达标** (最新收盘价 {latest['Close']:.2f} 跌破 5日均线 {latest['MA5']:.2f})")

    # 规则 2
    report_lines.append("\n**2. 成交量验证**：站上5日后，需连续至少三个交易日放量。且在七个交易日以内，必须出现一到两个交易日的巨量。")
    vol_status = "✅ 达标" if (max_consecutive >= 3 and 1 <= massive_vol_count <= 2) else "⚠️ 未完全达标"
    report_lines.append(f"> 💡 **当前状态**：{vol_status} (近7日最大连续放量天数: {max_consecutive}天, 巨量天数: {massive_vol_count}天)")

    # 规则 3
    report_lines.append("\n**3. 巨量标准**：巨量定义为当日成交量不低于前期均量的1.45倍。这是筛选有效启动的关键。")
    if latest['Is_Massive_Vol']:
        report_lines.append(f"> 💡 **当前状态**：✅ **今日出现巨量** (今日量比达 {latest['Vol_Ratio']:.2f} 倍)")
    else:
        report_lines.append(f"> 💡 **当前状态**：ℹ️ 今日量比为 {latest['Vol_Ratio']:.2f} 倍，未达巨量标准。")

    # 规则 4
    report_lines.append("\n**关键市场心理与持有原则：**")
    report_lines.append("**4. 买入时机**：强调“买在分歧严重时”。即当市场对某股走势判断对立、存在重大利空却不跌反涨时，往往是机会。")
    report_lines.append("> 💡 **当前状态**：ℹ️ *此为心法，需结合市场消息面与基本面主观判断。*")

    # 规则 5
    report_lines.append("\n**5. 持有逻辑**：一旦符合条件买入，需坚定持有。只要股价收盘价始终维持在5日均线的±2.5%范围内（即不偏离超过7.5%），趋势就被视为健康，应一直持股，忽略短期波动。")
    dev_pct = latest['Deviation_MA5'] * 100
    if -7.5 <= dev_pct <= 7.5:
        report_lines.append(f"> 💡 **当前状态**：✅ **趋势健康** (当前偏离度为 {dev_pct:.2f}%)")
    else:
        report_lines.append(f"> 💡 **当前状态**：⚠️ **偏离过大** (当前偏离度为 {dev_pct:.2f}%)")

    # 规则 6
    report_lines.append("\n**风险控制与卖出/止损纪律：**")
    report_lines.append("**6. 第一道防线（止盈/止损）**：若收盘价跌破5日均线超过7.5%，必须执行第一次强制减仓或离场。")
    if dev_pct < -7.5:
        report_lines.append(f"> 💡 **当前状态**：🚨 **触发防线** (跌破均线超7.5%，当前偏离 {dev_pct:.2f}%，建议立刻减仓/离场！)")
    else:
        report_lines.append(f"> 💡 **当前状态**：🛡️ 安全 (未触发第一道防线)")

    # 规则 7
    report_lines.append("\n**7. 第二道防线（强制止损）**：若股价从买入点下跌达到20%，必须无条件止损离场，控制风险。")
    if buy_price > 0:
        drawdown = (latest['Close'] - buy_price) / buy_price * 100
        if drawdown <= -20.0:
            report_lines.append(f"> 💡 **当前状态**：💥 **触发绝对止损** (当前亏损 {drawdown:.2f}%，必须无条件离场！)")
        else:
            report_lines.append(f"> 💡 **当前状态**：🛡️ 安全 (当前盈亏 {drawdown:.2f}%)")
    else:
        report_lines.append("> 💡 **当前状态**：ℹ️ 未设置买入价，跳过此项检测。")

    # 规则 8
    report_lines.append("\n**8. 可能的重新入场机会**：在止损离场后，若股价反抽时再次放巨量，且收盘价距5日均线的偏离度精确为4.5%，可考虑重新进场，这可能是一个重要的二次机会。")
    if latest['Is_Massive_Vol'] and (4.0 <= dev_pct <= 5.0):
        report_lines.append(f"> 💡 **当前状态**：🎯 **触发二次入场信号！** (今日放巨量且偏离度为 {dev_pct:.2f}%)")
    else:
        report_lines.append(f"> 💡 **当前状态**：ℹ️ 未触发二次入场条件。")

    # 综合判定
    if dev_pct < -7.5 or (buy_price > 0 and (latest['Close'] - buy_price) / buy_price <= -0.20):
        final_decision = "🔴 **综合建议：已触发风控防线，严格执行纪律，建议离场！**"
    elif is_above_ma5 and massive_vol_count >= 1:
        final_decision = "🟢 **综合建议：符合战法主要特征，趋势健康，可考虑持有或寻找买点。**"
    else:
        final_decision = "🟡 **综合建议：条件未完全共振，建议继续观察量价配合情况。**"
        
    return data, report_lines, final_decision

# --- 4. 主界面执行与展示 ---
if analyze_button:
    if ticker_input:
        with st.spinner(f'正在通过 {data_source.split()[0]} 获取 {ticker_input} 的数据...'):
            try:
                hist_data = fetch_stock_data(ticker_input, period_input, data_source)
                
                if not hist_data.empty:
                    st.success(f"成功获取数据！(数据源: {data_source.split()[0]})")
                    
                    processed_data, report_lines, final_decision = analyze_strategy(hist_data, buy_price_input)
                    
                    # 顶层指标卡片
                    latest_data = processed_data.iloc[-1]
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("最新收盘价", f"{latest_data['Close']:.2f}")
                    col2.metric("5日均线 (MA5)", f"{latest_data['MA5']:.2f}")
                    col3.metric("MA5 偏离度", f"{latest_data['Deviation_MA5']*100:.2f}%")
                    col4.metric("最新量比", f"{latest_data['Vol_Ratio']:.2f}")
                    
                    st.divider()
                    
                    # 战法诊断报告
                    st.subheader("🎯 战法诊断报告")
                    st.info(final_decision)
                    for line in report_lines:
                        st.markdown(line)
                        
                    # 总结精髓
                    st.markdown("---")
                    st.markdown("### 📖 总结精髓")
                    st.info("这套方法将交易简化为对5日均线和成交量（特别是巨量）的严格量化跟踪。核心理念是：在放量突破关键均线时介入，在量能配合的上升通道中持有，在价格结构被破坏时果断离场。其目的是通过纪律性规则，在控制风险的前提下，捕捉持续的主升浪。")
                        
                    st.divider()
                    
                    # 详细数据表格
                    st.subheader("📊 近期量价数据明细 (最近15个交易日)")
                    display_df = processed_data[['Close', 'Volume', 'MA5', 'Avg_Vol_5', 'Vol_Ratio', 'Deviation_MA5', 'Is_Massive_Vol']].copy()
                    
                    display_df['Deviation_MA5'] = (display_df['Deviation_MA5'] * 100).round(2).astype(str) + '%'
                    display_df['Vol_Ratio'] = display_df['Vol_Ratio'].round(2)
                    display_df['MA5'] = display_df['MA5'].round(2)
                    display_df['Avg_Vol_5'] = display_df['Avg_Vol_5'].round(0).astype(int)
                    
                    display_df = display_df.reset_index().sort_values(by='Date', ascending=False)
                    
                    display_df = display_df.rename(columns={
                        'Date': '交易日期',
                        'Close': '收盘价',
                        'Volume': '当日成交量',
                        'MA5': '5日均线',
                        'Avg_Vol_5': '前期5日均量',
                        'Vol_Ratio': '量比 (巨量≥1.45)',
                        'Deviation_MA5': '5日线偏离度',
                        'Is_Massive_Vol': '是否巨量'
                    })
                    
                    # 格式化日期显示，去除时间部分
                    if '交易日期' in display_df.columns:
                        display_df['交易日期'] = display_df['交易日期'].dt.strftime('%Y-%m-%d')
                        
                    st.dataframe(display_df.head(15), use_container_width=True)
                    
                else:
                    st.warning(f"获取到的数据为空，请检查股票代码是否正确或该股是否停牌。")
            except Exception as e:
                st.error(f"分析出错: {e}\n\n提示：如果使用 AkShare 报错，请确保已安装库 (pip install akshare) 且输入的是纯数字A股代码。")
    else:
        st.warning("请先输入股票代码！")
else:
    st.info("👈 请在左侧输入股票代码，选择数据源后点击执行分析。")
