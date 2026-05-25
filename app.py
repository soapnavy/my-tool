import streamlit as st
import yfinance as yf
import akshare as ak
import pandas as pd
import datetime

# ==========================================
# 页面基础设置
# ==========================================
st.set_page_config(page_title="量化投研终端", layout="centered", initial_sidebar_state="expanded")

# ==========================================
# 数据获取函数 1：雅虎财经 (海外/手机专用)
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

# ==========================================
# 数据获取函数 2：AkShare (国内/电脑专用)
# ==========================================
@st.cache_data(ttl=3600)
def get_akshare_data(symbol):
    symbol = str(symbol).zfill(6)
    try:
        # 获取近60天数据
        end_date = datetime.datetime.now().strftime("%Y%m%d")
        start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime("%Y%m%d")
        df = ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        if not df.empty:
            # AkShare自带中文列名 '收盘' 和 '成交量'
            return df
        return None
    except:
        return None

# ==========================================
# 侧边栏：全局设置与导航 (只放设置和菜单)
# ==========================================
st.sidebar.title("⚙️ 全局设置")
data_source = st.sidebar.radio(
    "🔄 请选择数据引擎:",
    ["🌍 海外引擎 (YFinance - 手机防拦截)", "🇨🇳 国内引擎 (AkShare - 电脑功能全)"]
)

st.sidebar.markdown("---")
st.sidebar.title("🧭 导航菜单")
menu = st.sidebar.radio(
    "请选择功能区域:",
    ["📈 战法分析器 (核心)", "🌡️ 大盘温度计", "🔄 板块轮动监控"]
)

# ==========================================
# 功能 1：📈 战法分析器 (主界面)
# ==========================================
if menu == "📈 战法分析器 (核心)":
    st.title("📈 均线与量能核心战法分析器")
    if "海外" in data_source:
        st.caption("当前状态：🟢 已启用海外加速引擎 (适合手机端查看个股)")
    else:
        st.caption("当前状态：🔴 已启用国内全能引擎 (适合电脑端深度分析)")
    st.divider()
    
    # 【修复重点】把输入框放在主界面，并排显示更美观
    col_input1, col_input2 = st.columns(2)
    with col_input1:
        stock_code = st.text_input("请输入股票代码 (如: 600519)", value="600519")
    with col_input2:
        cost_price = st.number_input("您的买入成本价 (选填)", min_value=0.00, value=0.00, step=0.10)
    
    # 按钮也放在主界面，加粗变色
    analyze_btn = st.button("🚀 开始量化分析", type="primary")
    
    st.markdown("---") # 加一条分割线，区分输入区和结果区
    
    if analyze_btn:
        with st.spinner("正在拉取数据..."):
            # 根据用户的选择，调用不同的数据源
            if "海外" in data_source:
                hist = get_yfinance_data(stock_code)
            else:
                hist = get_akshare_data(stock_code)
            
            if hist is not None and len(hist) >= 5:
                hist['MA5'] = hist['收盘'].rolling(window=5).mean()
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                
                close_price = latest['收盘']
                ma5_price = latest['MA5']
                vol_today = latest['成交量']
                vol_prev = prev['成交量']
                vol_ratio = vol_today / vol_prev if vol_prev > 0 else 0
                
                # 展示核心数据
                col1, col2, col3 = st.columns(3)
                col1.metric("最新收盘价", f"¥{close_price:.2f}")
                col2.metric("5日均线", f"¥{ma5_price:.2f}")
                col3.metric("量能倍数", f"{vol_ratio:.2f} 倍")
                
                # 诊断结论
                st.markdown("### 📊 诊断结论")
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

# ==========================================
# 功能 2 & 3：大盘与板块 (主界面)
# ==========================================
elif menu in ["🌡️ 大盘温度计", "🔄 板块轮动监控"]:
    st.title(menu)
    
    if "海外" in data_source:
        st.error("🔒 **功能受限提示**")
        st.warning("您当前使用的是 **海外引擎 (YFinance)**，该引擎不支持获取A股大盘和板块数据。")
        st.info("💡 **解锁方法**：请在左侧栏将数据引擎切换为 **国内引擎 (AkShare)**。")
    else:
        st.success("✅ **国内引擎已激活！**")
        st.markdown("这里可以调用 AkShare 的高级接口获取全市场数据。")
        
        if st.button("点击测试获取东方财富板块数据"):
            with st.spinner("正在连接国内接口..."):
                try:
                    # 简单测试一下AkShare的板块接口
                    board_df = ak.stock_board_industry_name_em()
                    st.dataframe(board_df.head(10))
                    st.success("🎉 成功获取板块数据！(仅展示前10条)")
                except Exception as e:
                    st.error("获取失败，可能是网络问题或接口限制。")
