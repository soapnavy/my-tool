# 文件名: app.py
# 必要的引用库 (注意这里用的是井号 #)

import akshare as ak
import pandas as pd
import datetime
import plotly.graph_objects as go

# ==========================================
# 页面基础设置 (适合手机与PC)
# 下面继续写你的原有代码...

st.set_page_config(page_title="五日线战法量化工具", layout="centered")

st.title("📈 五日线战法量化分析工具")
st.markdown("基于趋势+量能+情绪的强势股主升浪交易模型")

# 用户输入区
ticker_symbol = st.text_input("请输入股票代码 (美股如 AAPL, A股如 600519.SS, 000001.SZ)", "AAPL")
lookback_days = st.slider("历史数据回溯天数", min_value=30, max_value=120, value=60)

if st.button("开始分析"):
    with st.spinner(f"正在获取 {ticker_symbol} 的数据..."):
        end_date = datetime.today()
        start_date = end_date - timedelta(days=lookback_days)
        
        try:
            df = yf.download(ticker_symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
            
            if df.empty:
                st.error("未获取到股票数据，请检查股票代码是否正确。")
            else:
                # 处理 yfinance 多层索引
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)

                # 计算核心指标
                df['MA5'] = df['Close'].rolling(window=5).mean()
                df['VMA5'] = df['Volume'].rolling(window=5).mean()
                df['Deviation_MA5'] = (df['Close'] - df['MA5']) / df['MA5']
                df['Is_Huge_Volume'] = df['Volume'] >= (1.45 * df['VMA5'].shift(1))
                df['Vol_Increase'] = df['Volume'] > df['Volume'].shift(1)
                df['3_Days_Vol_Up'] = df['Vol_Increase'].rolling(window=3).sum() == 3
                df['Huge_Vol_in_7_Days'] = df['Is_Huge_Volume'].rolling(window=7).sum() >= 1
                
                df = df.dropna()
                
                if df.empty:
                    st.warning("有效数据不足以计算5日均线，请增加回溯天数。")
                else:
                    latest = df.iloc[-1]
                    current_price = float(latest['Close'])
                    ma5_price = float(latest['MA5'])
                    deviation = float(latest['Deviation_MA5']) * 100
                    
                    # 界面展示：基础数据
                    st.subheader("📊 基础数据")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("最新收盘价", f"{current_price:.2f}")
                    col2.metric("5日均线 (MA5)", f"{ma5_price:.2f}")
                    col3.metric("当前偏离度", f"{deviation:.2f}%")
                    
                    # 界面展示：战法条件诊断
                    st.subheader("🔍 战法条件诊断")
                    is_above_ma5 = current_price > ma5_price
                    is_3d_vol_up = bool(latest['3_Days_Vol_Up'])
                    has_huge_vol_7d = bool(latest['Huge_Vol_in_7_Days'])
                    
                    st.write(f"- **站上5日线**: {'✅ 是' if is_above_ma5 else '❌ 否'}")
                    st.write(f"- **连续3日放量**: {'✅ 是' if is_3d_vol_up else '❌ 否'}")
                    st.write(f"- **近7日内出现巨量(>=1.45倍)**: {'✅ 是' if has_huge_vol_7d else '❌ 否'}")
                    
                    # 界面展示：交易决策建议
                    st.subheader("💡 交易决策建议")
                    if is_above_ma5 and has_huge_vol_7d:
                        st.success("🟢 **[入场信号]** 满足站上5日线且近期有巨量资金异动，可结合市场情绪考虑建仓。")
                    else:
                        st.info("⚪ **[观望]** 暂不满足核心启动条件，建议继续观察。")

                    if deviation < -7.5:
                        st.error("🔴 **[风控警报]** 跌破5日线超过7.5%！触发第一道防线，建议立即减仓或止损！")
                    elif current_price < ma5_price:
                        st.warning("🟡 **[注意]** 股价已跌破5日线，趋势可能走弱，请密切关注。")
                    elif abs(deviation) <= 2.5:
                        st.success("🟢 **[持仓健康]** 股价在5日线 ±2.5% 范围内，趋势健康，建议坚定持有。")

                    if bool(latest['Is_Huge_Volume']) and abs(deviation) <= 4.5:
                        st.info("🟣 **[二波机会]** 今日再次放出巨量，且偏离度在4.5%以内，若前期已止损，可视为二波启动信号！")

        except Exception as e:
            st.error(f"发生错误: {str(e)}")
