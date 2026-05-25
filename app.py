import streamlit as st
import akshare as ak
import pandas as pd
import datetime
import plotly.graph_objects as go

# ==========================================
# 页面基础设置 (适合手机与PC)
# ==========================================
st.set_page_config(page_title="量化投研终端", layout="centered", initial_sidebar_state="expanded")

# ==========================================
# 缓存数据获取函数 (防崩溃与加速)
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
# 功能 1：📈 战法分析器 (完美复刻你的需求)
# ==========================================
if menu == "📈 战法分析器 (核心)":
    # 主界面标题
    st.title("📈 均线与量能核心战法分析器")
    st.markdown("基于 **5日均线** 与 **1.45倍巨量** 的右侧交易纪律系统")
    st.divider()
    
    # 侧边栏参数设置 (复刻截图)
    st.sidebar.markdown("---")
    st.sidebar.subheader("设置参数")
    stock_code = st.sidebar.text_input("请输入股票代码 (如: 600519)", value="600519")
    cost_price = st.sidebar.number_input("您的买入成本价 (选填，用于计算20%止损)", min_value=0.00, value=0.00, step=0.10)
    analyze_btn = st.sidebar.button("开始量化分析")
    
    if analyze_btn:
        with st.spinner("正在拉取数据并进行量化分析..."):
            try:
                hist = get_stock_hist(stock_code)
                if len(hist) >= 5:
                    # 计算指标
                    hist['MA5'] = hist['收盘'].rolling(window=5).mean()
                    latest = hist.iloc[-1]
                    prev = hist.iloc[-2]
                    
                    close_price = latest['收盘']
                    ma5_price = latest['MA5']
                    vol_today = latest['成交量']
                    vol_prev = prev['成交量']
                    vol_ratio = vol_today / vol_prev if vol_prev > 0 else 0
                    
                    # 手机端友好的指标展示 (会自动折行)
                    col1, col2, col3 = st.columns(3)
                    col1.metric("最新收盘价", f"¥{close_price:.2f}")
                    col2.metric("5日均线 (MA5)", f"¥{ma5_price:.2f}")
                    col3.metric("今日量能倍数", f"{vol_ratio:.2f} 倍")
                    
                    st.markdown("### 📊 战法诊断结论")
                    
                    # 核心逻辑判断
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
                    
                    # 止损计算逻辑
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
                st.error("分析失败，请检查股票代码是否正确或网络是否正常。")

# ==========================================
# 功能 2：🌡️ 大盘温度计
# ==========================================
elif menu == "🌡️ 大盘温度计":
    st.title("🌡️ 大盘温度计")
    try:
        df_a = get_spot_data()
        up_count = len(df_a[df_a['涨跌幅'] > 0])
        down_count = len(df_a[df_a['涨跌幅'] < 0])
        total_turnover = df_a['成交额'].sum() / 100000000
        active_market_cap = df_a[df_a['换手率'] > 3.0]['流通市值'].sum() / 100000000

        c1, c2 = st.columns(2)
        c1.metric("上涨家数 📈", f"{up_count} 家")
        c2.metric("下跌家数 📉", f"{down_count} 家")
        
        c3, c4 = st.columns(2)
        c3.metric("两市总成交额 💰", f"{total_turnover:.2f} 亿元")
        c4.metric("活跃市值 (换手>3%) 🔥", f"{active_market_cap:.2f} 亿元")
    except Exception as e:
        st.error("数据获取失败，请检查网络。")

# ==========================================
# 功能 3：🔄 板块轮动监控
# ==========================================
elif menu == "🔄 板块轮动监控":
    st.title("🔄 热门板块轮动监控")
    try:
        sectors = get_hot_sectors()
        top_sectors = sectors.sort_values(by='涨跌幅', ascending=False).head(10)
        st.write("🔥 **今日涨幅 Top 10 行业板块**")
        st.dataframe(top_sectors[['板块名称', '涨跌幅', '总市值', '领涨股票']], use_container_width=True)
    except Exception as e:
        st.error("板块数据获取失败")

# ==========================================
# 功能 4：🤖 战法批量扫描
# ==========================================
elif menu == "🤖 战法批量扫描":
    st.title("🤖 战法自动扫描器")
    st.write("自动在今日排名前 5 的热门板块中，寻找符合 **站上5日均线且放量1.45倍** 的领涨股。")
    if st.button("🚀 一键扫描"):
        with st.spinner("正在扫描，请稍候..."):
            try:
                sectors = get_hot_sectors()
                top_5_sectors = sectors.sort_values(by='涨跌幅', ascending=False).head(5)['板块名称'].tolist()
                results = []
                for sector in top_5_sectors:
                    cons = get_sector_cons(sector)
                    top_stocks = cons.sort_values(by='涨跌幅', ascending=False).head(3)
                    for _, stock in top_stocks.iterrows():
                        code = str(stock['代码']).zfill(6)
                        try:
                            hist = get_stock_hist(code)
                            if len(hist) >= 5:
                                hist['MA5'] = hist['收盘'].rolling(window=5).mean()
                                latest, prev = hist.iloc[-1], hist.iloc[-2]
                                if latest['收盘'] > latest['MA5'] and latest['成交量'] >= prev['成交量'] * 1.45:
                                    results.append({
                                        "板块": sector, "代码": code, "名称": stock['名称'],
                                        "最新价": latest['收盘'], "量能倍数": round(latest['成交量'] / prev['成交量'], 2)
                                    })
                        except:
                            continue
                if results:
                    st.success(f"扫描完成！发现 {len(results)} 只符合战法的股票：")
                    st.dataframe(pd.DataFrame(results), use_container_width=True)
                else:
                    st.warning("今日热门板块中暂无完全符合战法的股票。")
            except Exception as e:
                st.error("扫描失败。")

# ==========================================
# 功能 5：🕵️‍♂️ 个股 X 光机
# ==========================================
elif menu == "🕵️‍♂️ 个股 X 光机":
    st.title("🕵️‍♂️ 个股 X 光机 (K线)")
    symbol_k = st.text_input("输入股票代码", value="000001")
    try:
        df_k = get_stock_hist(symbol_k).tail(60)
        fig = go.Figure(data=[go.Candlestick(x=df_k['日期'], open=df_k['开盘'], high=df_k['最高'], low=df_k['最低'], close=df_k['收盘'], name="K线")])
        df_k['MA5'] = df_k['收盘'].rolling(5).mean()
        fig.add_trace(go.Scatter(x=df_k['日期'], y=df_k['MA5'], mode='lines', name='5日均线', line=dict(color='orange', width=1.5)))
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error("无法生成K线图。")

# ==========================================
# 功能 6：💰 聪明钱监控
# ==========================================
elif menu == "💰 聪明钱监控":
    st.title("💰 聪明钱 (北向资金)")
    try:
        north_money = ak.stock_hsgt_north_net_flow_in_em()
        st.line_chart(north_money.set_index('time')['value'])
    except Exception as e:
        st.error("北向资金获取失败。")
