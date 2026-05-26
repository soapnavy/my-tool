import streamlit as st
import pandas as pd
import akshare as ak
import datetime

# --- 页面设置 ---
st.set_page_config(page_title="量化交易信号系统", page_icon="📈")
st.title("📈 均线与量能核心战法分析器")
st.markdown("基于5日均线与1.45倍巨量的右侧交易纪律系统")

# --- 侧边栏输入 ---
st.sidebar.header("设置参数")
stock_code = st.sidebar.text_input("请输入股票代码 (如: 600519)", value="600519")
entry_price = st.sidebar.number_input("您的买入成本价 (选填，用于计算20%止损)", value=0.0, step=0.1)

# --- 核心数据获取与计算函数 ---
@st.cache_data(ttl=3600) # 缓存数据1小时，避免频繁请求
def get_and_analyze_data(code, cost_price):
    try:
        # 1. 获取过去60天的日K线数据
        end_date = datetime.datetime.now().strftime("%Y%m%d")
        # 往前推90天确保有足够的交易日算均线
        start_date = (datetime.datetime.now() - datetime.timedelta(days=90)).strftime("%Y%m%d") 
        
        df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        
        if df.empty:
            return None, "未获取到数据，请检查股票代码是否正确。"
            
        # 重命名列以便处理
        df = df[['日期', '收盘', '成交量']]
        df.columns = ['Date', 'Close', 'Volume']
        
        # 2. 计算技术指标
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['Vol_MA10'] = df['Volume'].rolling(window=10).mean()
        
        # 截取最近数据
        df = df.dropna()
        latest = df.iloc[-1]
        
        # 3. 提取关键数值
        current_price = latest['Close']
        ma5_price = latest['MA5']
        bias = (current_price - ma5_price) / ma5_price * 100
        
        # 4. 判断规则
        recent_7_days = df.tail(7)
        huge_volume_days = recent_7_days[recent_7_days['Volume'] >= 1.45 * recent_7_days['Vol_MA10']]
        
        report = {
            "date": latest['Date'],
            "current_price": current_price,
            "ma5_price": ma5_price,
            "bias": bias,
            "huge_vol_count": len(huge_volume_days),
            "signals": []
        }
        
        # 规则1：站稳5日线
        if current_price > ma5_price:
            report['signals'].append(("✅ 入场基础", "当前价格站稳5日均线之上，具备操作基础。"))
        else:
            report['signals'].append(("❌ 入场基础", "当前价格在5日均线之下，不看不做。"))
            
        # 规则2&3：巨量验证
        if len(huge_volume_days) >= 1:
            report['signals'].append(("✅ 巨量验证", f"近7天内出现了 {len(huge_volume_days)} 次1.45倍以上巨量，资金介入明显。"))
        else:
            report['signals'].append(("❌ 量能不足", "近7天未出现1.45倍以上巨量，有效启动概率低。"))
            
        # 规则5：健康持有
        if abs(bias) <= 2.5:
            report['signals'].append(("🟢 持仓建议", "当前偏离度在±2.5%内，趋势健康，建议坚定持有。"))
        elif bias > 2.5:
            report['signals'].append(("🟡 偏离警告", f"向上偏离度达 {bias:.2f}%，注意短期回调洗盘风险。"))
            
        # 规则6：第一防线
        if bias <= -7.5:
            report['signals'].append(("🔴 强制减仓", "跌破5日均线超过7.5%！必须执行第一次强制减仓或离场！"))
            
        # 规则7：绝对止损
        if cost_price > 0:
            loss_pct = (current_price - cost_price) / cost_price * 100
            if loss_pct <= -20.0:
                report['signals'].append(("☠️ 强制止损", f"较买入价下跌已达 {loss_pct:.2f}%，触发20%无条件止损线！"))
                
        # 规则8：二次入场
        if abs(bias - 4.5) < 0.5 and len(huge_volume_days) >= 1:
            report['signals'].append(("🔥 二次入场", "反抽放巨量，且偏离度接近4.5%，可能是一个重要的二次进场机会！"))
            
        return report, "success"
        
    except Exception as e:
        return None, f"发生错误: {str(e)}"

# --- 触发分析 ---
if st.sidebar.button("开始量化分析"):
    with st.spinner('正在从云端拉取最新行情数据...'):
        report, msg = get_and_analyze_data(stock_code, entry_price)
        
    if report:
        st.success(f"分析完成！最新数据日期: {report['date']}")
        
        # 关键点位展示区
        st.subheader("📍 关键价格点位")
        col1, col2, col3 = st.columns(3)
        col1.metric("当前收盘价", f"{report['current_price']:.2f} 元")
        col2.metric("5日生命线 (MA5)", f"{report['ma5_price']:.2f} 元")
        col3.metric("当前乖离率 (BIAS)", f"{report['bias']:.2f} %")
        
        st.markdown("---")
        st.markdown(f"**⚠️ 第一防线 (跌破7.5%离场价)**： `{report['ma5_price'] * 0.925:.2f} 元`")
        if entry_price > 0:
            st.markdown(f"**☠️ 第二防线 (20%绝对止损价)**： `{entry_price * 0.80:.2f} 元`")
        
        st.markdown("---")
        st.subheader("🤖 系统信号与操作建议")
        
        for title, desc in report['signals']:
            st.info(f"**{title}**：{desc}")
            
        st.markdown("---")
        st.caption("💡 纪律备忘录：买在分歧严重时。若符合条件买入，请严格遵守上述防线价格，截断亏损，让利润奔跑。")
    else:
        st.error(msg)
