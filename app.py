import streamlit as st
import yfinance as yf
import akshare as ak
import pandas as pd
import datetime

# ==========================================
# 页面基础设置 (改为 wide 宽屏模式，更适合多标签页)
# ==========================================
st.set_page_config(page_title="量化投研终端", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 数据获取函数
# ==========================================
@st.cache_data(ttl=3600)
def get_yfinance_data(symbol):
    symbol = str(symbol).zfill(6)
    ticker = f"{symbol}.SS" if symbol.startswith('6') else f"{symbol}.SZ"
    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        if not hist.empty:
            hist = hist.rename(columns={"Close": "收盘", "Volume": "成交量"})
            return hist
        return None
    except:
        return None

@st.cache_data(ttl=3600)
def get_akshare_data(symbol):
    symbol = str(symbol).zfill(6)
    try:
        end_date = datetime.datetime.now().strftime("%Y%m%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if not df.empty:
            return df
        return None
    except:
        return None

# ==========================================
# 侧边栏：全局数据引擎切换
# ==========================================
st.sidebar.title("⚙️ 全局设置")
data_source = st.sidebar.radio(
    "🔄 数据引擎切换:",
    ["🌍 海外引擎 (YFinance - 手机专用)", "🇨🇳 国内引擎 (AkShare - 电脑全能)"],
    help="手机端请使用海外引擎防拦截；电脑端请使用国内引擎解锁所有数据。"
)
st.sidebar.divider()
st.sidebar.caption("💡 提示：顶部标签页可滑动切换功能。")

# ==========================================
# 主界面：顶部标签页布局 (完美还原你的草图)
# ==========================================
st.title("🚀 极客量化投研终端")

# 创建 6 个顶部标签页
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🌡️ 大盘温度计", 
    "📈 战法分析器", 
    "🔍 个股 X 光机", 
    "💸 聪明钱监控", 
    "🌬️ 市场风向标", 
    "⚙️ 选股与回测"
])

# ------------------------------------------
# 标签页 1：大盘温度计
# ------------------------------------------
with tab1:
    st.subheader("🌡️ 市场整体情绪与大盘温度计")
    if "海外" in data_source:
        st.warning("⚠️ 当前为海外引擎，大盘数据受限。请在电脑端切换为国内引擎查看。")
    else:
        st.success("✅ 国内引擎已连接，正在获取全市场涨跌停家数、连板高度等情绪数据...")
        # 占位UI
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("上证指数", "3150.25", "+1.2%")
        col2.metric("深证成指", "9765.41", "+0.8%")
        col3.metric("涨停家数", "56 家", "情绪回暖")
        col4.metric("跌停家数", "3 家", "-")
        st.info("开发计划：这里将接入 AkShare 的 `stock_board_industry_name_em` 板块轮动数据。")

# ------------------------------------------
# 标签页 2：战法分析器 (核心功能已接入)
# ------------------------------------------
with tab2:
    st.subheader("📈 均线与量能核心战法分析")
    
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        stock_code = st.text_input("请输入股票代码 (如: 600519)", value="600519", key="strategy_code")
    with col_input2:
        cost_price = st.number_input("您的买入成本价 (选填)", min_value=0.00, value=0.00, step=0.10)
    
    analyze_btn = st.button("🚀 开始量化分析", type="primary")
    
    if analyze_btn:
        with st.spinner("正在拉取数据..."):
            hist = get_yfinance_data(stock_code) if "海外" in data_source else get_akshare_data(stock_code)
            
            if hist is not None and len(hist) >= 5:
                hist['MA5'] = hist['收盘'].rolling(window=5).mean()
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                
                close_price = latest['收盘']
                ma5_price = latest['MA5']
                vol_today = latest['成交量']
                vol_prev = prev['成交量']
                vol_ratio = vol_today / vol_prev if vol_prev > 0 else 0
                
                st.divider()
                c1, c2, c3 = st.columns(3)
                c1.metric("最新收盘价", f"¥{close_price:.2f}")
                c2.metric("5日均线", f"¥{ma5_price:.2f}")
                c3.metric("量能倍数", f"{vol_ratio:.2f} 倍")
                
                is_above_ma5 = close_price > ma5_price
                is_huge_vol = vol_ratio >= 1.45
                
                if is_above_ma5 and is_huge_vol:
                    st.success("✅ **完美符合！** 站上5日线且放量超1.45倍。")
                elif is_above_ma5:
                    st.warning("⚠️ **部分符合。** 站上5日线，但量能不足。")
                elif is_huge_vol:
                    st.warning("⚠️ **部分符合。** 放巨量，但未站上5日线。")
                else:
                    st.error("❌ **不符合。** 破位且无量，建议观望。")
            else:
                st.error("❌ 数据获取失败，请检查代码或尝试切换数据引擎。")

# ------------------------------------------
# 标签页 3：个股 X 光机
# ------------------------------------------
with tab3:
    st.subheader("🔍 个股 X 光机 (基本面与资金面透视)")
    st.markdown("输入股票代码，一键生成体检报告：**市盈率、筹码分布、主力控盘度、财务排雷**。")
    st.text_input("要透视的股票代码:", value="000001", key="xray_code")
    st.button("开始透视")
    st.info("开发计划：这里将接入 AkShare 的财务报表接口和龙虎榜数据。")

# ------------------------------------------
# 标签页 4：聪明钱监控
# ------------------------------------------
with tab4:
    st.subheader("💸 “聪明钱”监控 (北向资金与机构动向)")
    if "海外" in data_source:
         st.error("🔒 该功能需要国内引擎支持，请在左侧切换。")
    else:
        st.markdown("监控**北向资金（外资）**净流入排行，以及**机构席位**大额买入的异动个股。")
        st.button("刷新资金流向")
        st.info("开发计划：接入 `ak.stock_hsgt_north_net_flow_in_em()` 获取沪深港通数据。")

# ------------------------------------------
# 标签页 5：市场风向标
# ------------------------------------------
with tab5:
    st.subheader("🌬️ 市场风向标 (宏观与消息面)")
    st.markdown("聚合央行动态、行业利好政策、突发重大新闻。")
    st.info("开发计划：接入财联社电报或新浪财经 7x24 小时快讯接口。")

# ------------------------------------------
# 标签页 6：自定义选股与回测
# ------------------------------------------
with tab6:
    st.subheader("⚙️ 自定义选股器与策略回测")
    st.markdown("设定你的选股条件（如：MACD金叉 + 换手率>5%），在全市场5000只股票中进行筛选，并测试该策略过去一年的胜率。")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.selectbox("技术指标", ["MACD 金叉", "KDJ 超卖", "突破 20 日均线"])
    with col_s2:
        st.selectbox("基本面过滤", ["剔除 ST 股", "市盈率 < 30", "净利润增长 > 20%"])
        
    st.button("开始全市场选股", type="primary")
    st.info("开发计划：这是一个算力密集型功能，将在电脑端本地运行循环筛选。")
