import streamlit as st
import akshare as ak
import pandas as pd
import datetime
import plotly.graph_objects as go
import time

# ==========================================
# 页面基础设置
# ==========================================
st.set_page_config(page_title="量化投研终端", layout="centered", initial_sidebar_state="expanded")

# ==========================================
# 缓存数据获取函数 (增加重试机制)
# ==========================================
@st.cache_data(ttl=300)
def get_spot_data():
    return ak.stock_zh_a_spot_em()

@st.cache_data(ttl=3600)
def get_hot_sectors():
    return ak.stock_board_industry_name_em()

@st.cache_data(ttl=3600)
def get_sector_cons(sector_name):
    return ak.stock_board_industry_cons_em(symbol=sector_name)

@st.cache_data(ttl=3600)
def get_stock_hist(symbol):
    symbol = str(symbol).zfill(6)
    end_date = datetime.datetime.now().strftime("%Y%m%d")
    start_date = (datetime.datetime.now() - datetime.timedelta(days=60)).strftime("%Y%m%d")
    # 尝试拉取数据，失败则重试1次
    try:
        return ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
    except Exception as e:
        time.sleep(1)
        return ak.stock_zh_a_hist(symbol=symbol, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")

# ==========================================
# 侧边栏导航
# ==========================================
st.sidebar.title("🧭 导航菜单")
menu = st.sidebar.radio(
    "请选择功能区域:",
    ["📈 战法分析器 (核心)", "🌡️ 大盘温度计", "🔄 板块轮动监控", "🤖 战法批量扫描", "🕵️‍♂️ 个股 X 光机", "💰 聪明钱监控"]
)

# ==========================================
# 功能 1：📈 战法分析器
# ==========================================
if menu == "📈 战法分析器 (核心)":
    st.title("📈 均线与量能核心战法分析器")
    st.markdown("基于 **5日均线** 与 **1.45倍巨量** 的右侧交易纪律系统")
    st.divider()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("设置参数")
    stock_code = st.sidebar.text_input("请输入股票代码 (如: 600519)", value="600519")
    cost_price = st.sidebar.number_input("您的买入成本价 (选填，用于计算20%止损)", min_value=0.00, value=0.00, step=0.10)
    analyze_btn = st.sidebar.button("开始量化分析")
    
    if analyze_btn:
        with st.spinner("正在拉取数据并进行量化分析... (如果卡住说明海外服务器被拦截)"):
            try:
                hist = get_stock_hist(stock_code)
                if hist is not None and len(hist) >= 5:
                    hist['MA5'] = hist['收盘'].rolling(window=5).mean()
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    
                    close_price = latest['收盘']
                    ma5_price = latest['MA5']
                    vol_today = latest['成交量']
                    vol_prev = prev['成交量']
                    vol_ratio = vol_today / vol_prev if vol_prev > 0 else 0
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("最新收盘价", f"¥{close_price:.2f}")
                    col2.metric("5日均线 (MA5)", f"¥{ma5_price:.2f}")
                    col3.metric("今日量能倍数", f"{vol_ratio:.2f} 倍")
                    
                    st.markdown("### 📊 战法诊断结论")
                    is_above_ma5 = close_price > ma5_price
                    is_huge_vol = vol_ratio >= 1.45
                    
                    if is_above_ma5 and is_huge_vol:
                        st.success("✅ **完美符合战法！** 股价已站上5日均线，且量能放大超过1.45倍，属于强势右侧突破。")
                    elif is_above_ma5:
                        st.warning("⚠️ **部分符合 (缩量企稳)。** 股价在5日均线之上，但量能未达1.45倍，动能略显不足，建议观察。")
                    elif is_huge_vol:
                        st.warning("⚠️ **部分符合 (放量滞涨)。** 爆出1.45倍以上巨量，但未能站上5日均线，警惕主力出货或上方抛压。")
                    else:
                        st.error("❌ **不符合战法。** 破位5日均线且未见明显资金进场，处于弱势区间，严格按纪律观望。")
                    
                    if cost_price > 0:
                        st.markdown("### 🛡️ 风控与止损建议")
                        stop_loss_price = cost_price * 0.80
                        if close_price <= stop_loss_price:
                            st.error(f"🚨 **警告：已触发 20% 绝对止损线！** 您的成本价 {cost_price} 元，当前价 {close_price} 元已跌破止损价 {stop_loss_price:.2f} 元。请严格执行纪律！")
                        else:
                            st.info(f"🛡️ 您的成本价为 {cost_price} 元，**20% 纪律止损位为：{stop_loss_price:.2f} 元**。当前安全。")
                else:
                    st.warning("股票数据不足，无法计算5日均线。")
            except Exception as e:
                st.error(f"分析失败！\n\n**真实报错原因：** `{e}`\n\n*(注：如果报错里写着 timeout、ConnectionError 或 JSONDecodeError，说明 Streamlit 的海外服务器被东方财富拦截了，请多点击几次按钮重试。)*")

# ==========================================
# 其他功能 (省略具体实现，保持原样即可)
# ==========================================
elif menu == "🌡️ 大盘温度计":
    st.title("🌡️ 大盘温度计")
    try:
        df_a = get_spot_data()
        st.success(f"成功获取到 {len(df_a)} 只股票数据！")
    except Exception as e:
        st.error(f"获取失败，报错：{e}")
