import streamlit as st
import yfinance as yf
import pandas as pd

# ==========================================
# 页面基础设置
# ==========================================
st.set_page_config(page_title="量化投研终端", layout="centered", initial_sidebar_state="expanded")

# ==========================================
# 雅虎财经数据获取函数 (海外服务器秒连，不拦截)
# ==========================================
@st.cache_data(ttl=3600)
def get_stock_hist(symbol):
    symbol = str(symbol).zfill(6)
    # 雅虎财经的A股代码规则：沪市加 .SS，深市加 .SZ
    if symbol.startswith('6'):
        ticker = f"{symbol}.SS"
    else:
        ticker = f"{symbol}.SZ"
    
    try:
        # 获取近1个月的数据（足够计算5日均线了）
        stock = yf.Ticker(ticker)
        hist = stock.history(period="1mo")
        
        if not hist.empty:
            # 把英文列名改成中文，适配后面的代码
            hist = hist.rename(columns={"Close": "收盘", "Volume": "成交量"})
            return hist
        return None
    except Exception as e:
        return None

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
    st.markdown("基于 **5日均线** 与 **1.45倍巨量** 的右侧交易纪律系统 (海外加速版)")
    st.divider()
    
    st.sidebar.markdown("---")
    st.sidebar.subheader("设置参数")
    stock_code = st.sidebar.text_input("请输入股票代码 (如: 600519)", value="600519")
    cost_price = st.sidebar.number_input("您的买入成本价 (选填)", min_value=0.00, value=0.00, step=0.10)
    analyze_btn = st.sidebar.button("开始量化分析")
    
    if analyze_btn:
        with st.spinner("正在通过海外专线拉取数据..."):
            hist = get_stock_hist(stock_code)
            
            if hist is not None and len(hist) >= 5:
                # 计算5日均线
                hist['MA5'] = hist['收盘'].rolling(window=5).mean()
                
                # 获取今天和昨天的数据
                latest = hist.iloc[-1]
                prev = hist.iloc[-2]
                
                close_price = latest['收盘']
                ma5_price = latest['MA5']
                vol_today = latest['成交量']
                vol_prev = prev['成交量']
                
                # 计算量能倍数
                vol_ratio = vol_today / vol_prev if vol_prev > 0 else 0
                
                # 显示核心数据
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
                st.error("❌ 数据获取失败，请检查股票代码是否正确（如茅台填 600519，平安银行填 000001）。")

# ==========================================
# 其他功能占位符
# ==========================================
elif menu == "🌡️ 大盘温度计":
    st.title("🌡️ 大盘温度计")
    st.info("此功能正在开发中...")

elif menu == "🔄 板块轮动监控":
    st.title("🔄 板块轮动监控")
    st.info("此功能正在开发中...")

elif menu == "🤖 战法批量扫描":
    st.title("🤖 战法批量扫描")
    st.info("此功能正在开发中...")

elif menu == "🕵️‍♂️ 个股 X 光机":
    st.title("🕵️‍♂️ 个股 X 光机")
    st.info("此功能正在开发中...")

elif menu == "💰 聪明钱监控":
    st.title("💰 聪明钱监控")
    st.info("此功能正在开发中...")
