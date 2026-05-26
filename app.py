# 5d_moving_average_strategy.py
# 必要的引用库
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def analyze_stock_strategy(ticker_symbol: str, lookback_days: int = 60):
    """
    根据“五日线战法”量化分析股票当前状态
    :param ticker_symbol: 股票代码 (如美股 'AAPL', A股 '600519.SS' 或 '000001.SZ')
    :param lookback_days: 获取历史数据的天数
    """
    print(f"========== 正在分析股票: {ticker_symbol} ==========")
    
    # 1. 获取历史数据
    end_date = datetime.today()
    start_date = end_date - timedelta(days=lookback_days)
    try:
        # 使用 yfinance 获取日线数据
        df = yf.download(ticker_symbol, start=start_date.strftime('%Y-%m-%d'), end=end_date.strftime('%Y-%m-%d'), progress=False)
        if df.empty:
            print("错误：未获取到股票数据，请检查股票代码是否正确。")
            return
    except Exception as e:
        print(f"数据获取异常: {e}")
        return

    # 确保列名是一维的 (处理 yfinance 多层索引问题)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    # 2. 计算核心量化指标
    # 5日收盘价均线
    df['MA5'] = df['Close'].rolling(window=5).mean()
    # 5日成交量均线 (作为前期均量基准)
    df['VMA5'] = df['Volume'].rolling(window=5).mean()
    
    # 价格偏离度: (Close - MA5) / MA5
    df['Deviation_MA5'] = (df['Close'] - df['MA5']) / df['MA5']
    
    # 巨量判定: 当日成交量 >= 1.45 * 5日均量
    df['Is_Huge_Volume'] = df['Volume'] >= (1.45 * df['VMA5'].shift(1))
    
    # 连续3日放量判定 (这里定义为: 连续3天成交量大于前一天)
    df['Vol_Increase'] = df['Volume'] > df['Volume'].shift(1)
    df['3_Days_Vol_Up'] = df['Vol_Increase'].rolling(window=3).sum() == 3

    # 近7个交易日内是否有巨量
    df['Huge_Vol_in_7_Days'] = df['Is_Huge_Volume'].rolling(window=7).sum() >= 1

    # 剔除 NaN 值
    df = df.dropna()
    if df.empty:
        print("错误：有效数据不足以计算5日均线，请增加 lookback_days。")
        return

    # 3. 获取最新一个交易日的数据进行结论输出
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    current_price = latest['Close']
    ma5_price = latest['MA5']
    deviation = latest['Deviation_MA5'] * 100 # 转换为百分比

    print(f"【基础数据】")
    print(f"最新收盘价: {current_price:.2f}")
    print(f"5日均线(MA5): {ma5_price:.2f}")
    print(f"当前偏离度: {deviation:.2f}%\n")

    print(f"【战法条件诊断】")
    
    # 条件1: 站上5日线
    is_above_ma5 = current_price > ma5_price
    print(f"1. 站上5日线: {'✅ 是' if is_above_ma5 else '❌ 否'}")

    # 条件2: 连续3日放量
    is_3d_vol_up = latest['3_Days_Vol_Up']
    print(f"2. 连续3日放量: {'✅ 是' if is_3d_vol_up else '❌ 否'}")

    # 条件3: 7日内出现巨量 (1.45倍)
    has_huge_vol_7d = latest['Huge_Vol_in_7_Days']
    print(f"3. 近7日内出现巨量(>=1.45倍): {'✅ 是' if has_huge_vol_7d else '❌ 否'}")

    print(f"\n【交易决策建议】")
    # 入场逻辑判断
    if is_above_ma5 and has_huge_vol_7d:
        print("🟢 [入场信号] 满足站上5日线且近期有巨量资金异动，可结合市场情绪考虑建仓。")
    else:
        print("⚪ [观望] 暂不满足核心启动条件，建议继续观察。")

    # 风控逻辑判断
    if deviation < -7.5:
        print("🔴 [风控警报] 跌破5日线超过7.5%！触发第一道防线，建议立即减仓或止损！")
    elif current_price < ma5_price:
        print("🟡 [注意] 股价已跌破5日线，趋势可能走弱，请密切关注。")
    elif abs(deviation) <= 2.5:
        print("🟢 [持仓健康] 股价在5日线 ±2.5% 范围内，趋势健康，建议坚定持有。")

    # 二波入场逻辑判断
    if latest['Is_Huge_Volume'] and abs(deviation) <= 4.5:
        print("🟣 [二波机会] 今日再次放出巨量，且偏离度在4.5%以内，若前期已止损，可视为二波启动信号！")

    print("==================================================\n")


# --- 测试入口 ---
if __name__ == "__main__":
    # 测试用例 1: 苹果公司 (美股)
    analyze_stock_strategy("AAPL")
    
    # 测试用例 2: 贵州茅台 (A股，使用 .SS 后缀代表上交所)
    # 注意：周末或节假日运行可能显示的是上一个交易日的数据
    analyze_stock_strategy("600519.SS")
