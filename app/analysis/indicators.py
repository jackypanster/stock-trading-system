"""
技术指标计算模块
Technical Indicators Module

实现各种技术分析指标的计算，包括RSI、MACD、ATR等。
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, Union, Tuple
import logging
from datetime import datetime

from ..utils.logger import get_analysis_logger

logger = get_analysis_logger()


class TechnicalIndicators:
    """
    技术指标计算器
    
    提供各种技术分析指标的计算方法。
    """
    
    def __init__(self):
        """初始化技术指标计算器"""
        logger.info("技术指标计算器初始化完成")
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        计算相对强弱指标(RSI)
        
        RSI = 100 - (100 / (1 + RS))
        RS = 平均涨幅 / 平均跌幅
        
        Args:
            prices: 价格序列（通常是收盘价）
            period: 计算周期，默认14
            
        Returns:
            RSI值序列
            
        Raises:
            ValueError: 输入数据无效
        """
        if len(prices) < period + 1:
            raise ValueError(f"数据长度不足，至少需要{period + 1}个数据点")
        
        if period <= 0:
            raise ValueError("周期必须大于0")
        
        logger.debug(f"计算RSI指标，周期={period}，数据点={len(prices)}")
        
        # 计算价格变化
        delta = prices.diff()
        
        # 分离涨跌
        gains = delta.where(delta > 0, 0)  # 涨幅
        losses = -delta.where(delta < 0, 0)  # 跌幅（转为正值）
        
        # 计算初始的平均涨跌幅（使用简单移动平均）
        avg_gains = gains.rolling(window=period, min_periods=period).mean()
        avg_losses = losses.rolling(window=period, min_periods=period).mean()
        
        # 使用指数加权移动平均（Wilder's smoothing）进行后续计算
        # 这是RSI的标准计算方法
        for i in range(period, len(gains)):
            avg_gains.iloc[i] = (avg_gains.iloc[i-1] * (period - 1) + gains.iloc[i]) / period
            avg_losses.iloc[i] = (avg_losses.iloc[i-1] * (period - 1) + losses.iloc[i]) / period
        
        # 计算相对强度（RS）
        rs = avg_gains / avg_losses
        
        # 计算RSI
        rsi = 100 - (100 / (1 + rs))
        
        # 处理除零情况
        rsi = rsi.fillna(50)  # 当没有涨跌时，RSI设为50
        
        logger.info(f"RSI计算完成，有效值范围: {rsi.min():.2f} - {rsi.max():.2f}")
        
        return rsi
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """
        计算简单移动平均线(SMA)
        
        Args:
            prices: 价格序列
            period: 周期
            
        Returns:
            SMA序列
        """
        logger.debug(f"计算SMA指标，周期={period}")
        return prices.rolling(window=period, min_periods=1).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """
        计算指数移动平均线(EMA)
        
        Args:
            prices: 价格序列
            period: 周期
            
        Returns:
            EMA序列
        """
        logger.debug(f"计算EMA指标，周期={period}")
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_macd(prices: pd.Series, 
                      fast_period: int = 12, 
                      slow_period: int = 26, 
                      signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        计算MACD指标（指数平滑异同移动平均线）
        
        MACD = EMA(fast) - EMA(slow)
        信号线 = EMA(MACD, signal_period)
        柱状图 = MACD - 信号线
        
        Args:
            prices: 价格序列（通常是收盘价）
            fast_period: 快速EMA周期，默认12
            slow_period: 慢速EMA周期，默认26  
            signal_period: 信号线EMA周期，默认9
            
        Returns:
            (MACD线, 信号线, 柱状图) 的元组
            
        Raises:
            ValueError: 输入数据无效
        """
        if len(prices) < slow_period + signal_period:
            raise ValueError(f"数据长度不足，至少需要{slow_period + signal_period}个数据点")
        
        if fast_period <= 0 or slow_period <= 0 or signal_period <= 0:
            raise ValueError("所有周期必须大于0")
            
        if fast_period >= slow_period:
            raise ValueError("快速周期必须小于慢速周期")
        
        logger.debug(f"计算MACD指标，参数: fast={fast_period}, slow={slow_period}, signal={signal_period}")
        
        # 计算快速和慢速EMA
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast_period)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow_period)
        
        # 计算MACD线
        macd_line = ema_fast - ema_slow
        
        # 计算信号线（MACD的9周期EMA）
        signal_line = TechnicalIndicators.calculate_ema(macd_line, signal_period)
        
        # 计算柱状图（MACD - 信号线）
        histogram = macd_line - signal_line
        
        logger.info(f"MACD计算完成，MACD范围: {macd_line.min():.4f} - {macd_line.max():.4f}")
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        计算平均真实范围(ATR)指标
        
        真实范围(TR) = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
        ATR = TR的period期移动平均
        
        Args:
            df: 包含OHLC数据的DataFrame，需要包含High、Low、Close列
            period: 计算周期，默认14
            
        Returns:
            ATR值序列
            
        Raises:
            ValueError: 输入数据无效
        """
        required_columns = ['High', 'Low', 'Close']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"缺少必要的数据列: {missing_columns}")
        
        if len(df) < period + 1:
            raise ValueError(f"数据长度不足，至少需要{period + 1}个数据点")
        
        if period <= 0:
            raise ValueError("周期必须大于0")
        
        logger.debug(f"计算ATR指标，周期={period}，数据点={len(df)}")
        
        high = df['High']
        low = df['Low']
        close = df['Close']
        
        # 计算前一日收盘价
        prev_close = close.shift(1)
        
        # 计算三种可能的范围
        range1 = high - low  # 当日高低价差
        range2 = (high - prev_close).abs()  # 当日高价与前收盘价差
        range3 = (low - prev_close).abs()   # 当日低价与前收盘价差
        
        # 真实范围 = 三者最大值
        true_range = pd.DataFrame({
            'range1': range1,
            'range2': range2, 
            'range3': range3
        }).max(axis=1)
        
        # ATR = 真实范围的移动平均
        # 使用Wilder's smoothing方法（与RSI相同的平滑方法）
        atr = true_range.rolling(window=period, min_periods=period).mean()
        
        # 对于第一个ATR值之后的值，使用Wilder's smoothing
        for i in range(period, len(true_range)):
            atr.iloc[i] = (atr.iloc[i-1] * (period - 1) + true_range.iloc[i]) / period
        
        logger.info(f"ATR计算完成，有效值范围: {atr.min():.4f} - {atr.max():.4f}")
        
        return atr
    
    def analyze_rsi_signals(self, rsi: pd.Series, 
                           oversold_level: float = 30, 
                           overbought_level: float = 70) -> Dict[str, Any]:
        """
        分析RSI信号
        
        Args:
            rsi: RSI序列
            oversold_level: 超卖水平，默认30
            overbought_level: 超买水平，默认70
            
        Returns:
            RSI分析结果
        """
        if len(rsi) == 0:
            return {"error": "RSI数据为空"}
        
        current_rsi = rsi.iloc[-1]
        
        # 确定当前状态
        if pd.isna(current_rsi):
            status = "数据不足"
            signal = "无信号"
        elif current_rsi <= oversold_level:
            status = "超卖"
            signal = "买入信号"
        elif current_rsi >= overbought_level:
            status = "超买"
            signal = "卖出信号"
        else:
            status = "正常"
            signal = "无信号"
        
        # 计算RSI统计信息
        rsi_valid = rsi.dropna()
        
        analysis = {
            "current_rsi": round(current_rsi, 2) if not pd.isna(current_rsi) else None,
            "status": status,
            "signal": signal,
            "oversold_level": oversold_level,
            "overbought_level": overbought_level,
            "statistics": {
                "min": round(rsi_valid.min(), 2) if len(rsi_valid) > 0 else None,
                "max": round(rsi_valid.max(), 2) if len(rsi_valid) > 0 else None,
                "mean": round(rsi_valid.mean(), 2) if len(rsi_valid) > 0 else None,
                "std": round(rsi_valid.std(), 2) if len(rsi_valid) > 0 else None
            },
            "recent_values": [round(x, 2) for x in rsi.tail(5).tolist() if not pd.isna(x)]
        }
        
        logger.info(f"RSI分析完成: {status} (RSI={current_rsi:.2f})")
        
        return analysis
    
    def analyze_macd_signals(self, macd_line: pd.Series, 
                           signal_line: pd.Series, 
                           histogram: pd.Series) -> Dict[str, Any]:
        """
        分析MACD信号
        
        Args:
            macd_line: MACD线
            signal_line: 信号线
            histogram: 柱状图
            
        Returns:
            MACD分析结果
        """
        if len(macd_line) == 0 or len(signal_line) == 0 or len(histogram) == 0:
            return {"error": "MACD数据为空"}
        
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        # 检查数据有效性
        if pd.isna(current_macd) or pd.isna(current_signal) or pd.isna(current_histogram):
            return {
                "error": "MACD数据不足",
                "current_macd": None,
                "current_signal": None,
                "current_histogram": None
            }
        
        # 判断MACD信号
        # 1. 金叉/死叉
        if len(macd_line) >= 2 and len(signal_line) >= 2:
            prev_macd = macd_line.iloc[-2]
            prev_signal = signal_line.iloc[-2]
            
            # 金叉：MACD上穿信号线
            if prev_macd <= prev_signal and current_macd > current_signal:
                cross_signal = "金叉"
                signal_type = "买入信号"
            # 死叉：MACD下穿信号线
            elif prev_macd >= prev_signal and current_macd < current_signal:
                cross_signal = "死叉"
                signal_type = "卖出信号"
            else:
                cross_signal = "无交叉"
                signal_type = "无信号"
        else:
            cross_signal = "数据不足"
            signal_type = "无信号"
        
        # 2. 零轴穿越
        zero_cross = "无"
        if len(macd_line) >= 2:
            prev_macd = macd_line.iloc[-2]
            if prev_macd <= 0 and current_macd > 0:
                zero_cross = "上穿零轴"
            elif prev_macd >= 0 and current_macd < 0:
                zero_cross = "下穿零轴"
        
        # 3. 背离检测（简化版）
        # 检查最近5期的趋势
        if len(histogram) >= 5:
            recent_hist = histogram.tail(5)
            hist_trend = "上升" if recent_hist.iloc[-1] > recent_hist.iloc[0] else "下降"
        else:
            hist_trend = "未知"
        
        # 4. MACD位置分析
        if current_macd > 0 and current_signal > 0:
            position = "多头区域"
        elif current_macd < 0 and current_signal < 0:
            position = "空头区域"
        else:
            position = "过渡区域"
        
        # 计算统计信息
        macd_valid = macd_line.dropna()
        signal_valid = signal_line.dropna()
        hist_valid = histogram.dropna()
        
        analysis = {
            "current_macd": round(current_macd, 4),
            "current_signal": round(current_signal, 4),
            "current_histogram": round(current_histogram, 4),
            "cross_signal": cross_signal,
            "signal_type": signal_type,
            "zero_cross": zero_cross,
            "position": position,
            "histogram_trend": hist_trend,
            "statistics": {
                "macd": {
                    "min": round(macd_valid.min(), 4) if len(macd_valid) > 0 else None,
                    "max": round(macd_valid.max(), 4) if len(macd_valid) > 0 else None,
                    "mean": round(macd_valid.mean(), 4) if len(macd_valid) > 0 else None
                },
                "signal": {
                    "min": round(signal_valid.min(), 4) if len(signal_valid) > 0 else None,
                    "max": round(signal_valid.max(), 4) if len(signal_valid) > 0 else None,
                    "mean": round(signal_valid.mean(), 4) if len(signal_valid) > 0 else None
                },
                "histogram": {
                    "min": round(hist_valid.min(), 4) if len(hist_valid) > 0 else None,
                    "max": round(hist_valid.max(), 4) if len(hist_valid) > 0 else None,
                    "mean": round(hist_valid.mean(), 4) if len(hist_valid) > 0 else None
                }
            },
            "recent_values": {
                "macd": [round(x, 4) for x in macd_line.tail(3).tolist() if not pd.isna(x)],
                "signal": [round(x, 4) for x in signal_line.tail(3).tolist() if not pd.isna(x)],
                "histogram": [round(x, 4) for x in histogram.tail(3).tolist() if not pd.isna(x)]
            }
        }
        
        logger.info(f"MACD分析完成: {cross_signal}, {position} (MACD={current_macd:.4f})")
        
        return analysis
    
    def analyze_atr_signals(self, atr: pd.Series, prices: pd.Series) -> Dict[str, Any]:
        """
        分析ATR信号和波动率状态
        
        Args:
            atr: ATR序列
            prices: 价格序列（通常是收盘价）
            
        Returns:
            ATR分析结果
        """
        if len(atr) == 0 or len(prices) == 0:
            return {"error": "ATR或价格数据为空"}
        
        current_atr = atr.iloc[-1]
        current_price = prices.iloc[-1]
        
        if pd.isna(current_atr) or pd.isna(current_price):
            return {
                "error": "ATR数据不足",
                "current_atr": None,
                "current_price": None
            }
        
        # 计算ATR相对价格的百分比
        atr_percentage = (current_atr / current_price) * 100
        
        # 判断波动率水平
        if len(atr) >= 20:
            atr_mean = atr.tail(20).mean()
            atr_std = atr.tail(20).std()
            
            # 基于标准差判断波动率水平
            if current_atr > atr_mean + atr_std:
                volatility_level = "高波动"
                volatility_signal = "谨慎交易"
            elif current_atr < atr_mean - atr_std:
                volatility_level = "低波动"
                volatility_signal = "可能突破"
            else:
                volatility_level = "正常波动"
                volatility_signal = "正常交易"
        else:
            # 数据点不够，使用简化判断
            recent_atr = atr.tail(min(len(atr), 5))
            if len(recent_atr) > 1:
                atr_trend = "上升" if recent_atr.iloc[-1] > recent_atr.iloc[0] else "下降"
            else:
                atr_trend = "未知"
            
            volatility_level = "正常波动"
            volatility_signal = "正常交易"
            atr_mean = atr.mean()
            atr_std = atr.std()
        
        # 计算建议的止损距离（基于ATR倍数）
        stop_loss_multipliers = [1.5, 2.0, 2.5]
        stop_loss_levels = {}
        
        for multiplier in stop_loss_multipliers:
            stop_distance = current_atr * multiplier
            stop_loss_levels[f"atr_{multiplier}x"] = {
                "long_stop": round(current_price - stop_distance, 2),
                "short_stop": round(current_price + stop_distance, 2),
                "distance": round(stop_distance, 2)
            }
        
        # 计算统计信息
        atr_valid = atr.dropna()
        
        # ATR趋势分析
        if len(atr_valid) >= 5:
            recent_atr = atr_valid.tail(5)
            atr_trend = "上升" if recent_atr.iloc[-1] > recent_atr.iloc[0] else "下降"
            atr_change = ((recent_atr.iloc[-1] - recent_atr.iloc[0]) / recent_atr.iloc[0]) * 100
        else:
            atr_trend = "未知"
            atr_change = 0
        
        analysis = {
            "current_atr": round(current_atr, 4),
            "current_price": round(current_price, 2),
            "atr_percentage": round(atr_percentage, 2),
            "volatility_level": volatility_level,
            "volatility_signal": volatility_signal,
            "atr_trend": atr_trend,
            "atr_change_5d": round(atr_change, 2),
            "stop_loss_levels": stop_loss_levels,
            "statistics": {
                "min": round(atr_valid.min(), 4) if len(atr_valid) > 0 else None,
                "max": round(atr_valid.max(), 4) if len(atr_valid) > 0 else None,
                "mean": round(atr_mean, 4) if not pd.isna(atr_mean) else None,
                "std": round(atr_std, 4) if not pd.isna(atr_std) else None
            },
            "recent_values": [round(x, 4) for x in atr.tail(5).tolist() if not pd.isna(x)]
        }
        
        logger.info(f"ATR分析完成: {volatility_level} (ATR={current_atr:.4f}, {atr_percentage:.2f}%)")
        
        return analysis
    
    def get_technical_summary(self, df: pd.DataFrame, 
                            price_column: str = 'Close') -> Dict[str, Any]:
        """
        获取技术分析摘要
        
        Args:
            df: 包含价格数据的DataFrame
            price_column: 价格列名
            
        Returns:
            技术分析摘要
        """
        if price_column not in df.columns:
            raise ValueError(f"数据中没有找到价格列: {price_column}")
        
        prices = df[price_column]
        
        # 计算各种指标
        rsi_14 = self.calculate_rsi(prices, 14)
        sma_20 = self.calculate_sma(prices, 20)
        sma_50 = self.calculate_sma(prices, 50)
        ema_12 = self.calculate_ema(prices, 12)
        ema_26 = self.calculate_ema(prices, 26)
        
        # 计算MACD指标
        macd_line, signal_line, histogram = self.calculate_macd(prices, 12, 26, 9)
        
        # 计算ATR指标
        atr = self.calculate_atr(df, 14)
        
        # 计算支撑阻力位分析
        try:
            from .support_resistance import SupportResistanceAnalyzer
            sr_analyzer = SupportResistanceAnalyzer()
            support_resistance = sr_analyzer.analyze_price_action(df, price_column, window=5, min_change_pct=1.0, tolerance=0.5)
        except Exception as e:
            logger.warning(f"支撑阻力位分析失败: {e}")
            support_resistance = None
        
        current_price = prices.iloc[-1]
        
        summary = {
            "symbol": df.get('Symbol', [None]).iloc[-1] if 'Symbol' in df.columns else "Unknown",
            "current_price": round(current_price, 2),
            "analysis_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "indicators": {
                "rsi_14": self.analyze_rsi_signals(rsi_14),
                "macd": self.analyze_macd_signals(macd_line, signal_line, histogram),
                "atr": self.analyze_atr_signals(atr, prices),
                "moving_averages": {
                    "sma_20": round(sma_20.iloc[-1], 2) if not pd.isna(sma_20.iloc[-1]) else None,
                    "sma_50": round(sma_50.iloc[-1], 2) if not pd.isna(sma_50.iloc[-1]) else None,
                    "ema_12": round(ema_12.iloc[-1], 2) if not pd.isna(ema_12.iloc[-1]) else None,
                    "ema_26": round(ema_26.iloc[-1], 2) if not pd.isna(ema_26.iloc[-1]) else None,
                }
            },
            "price_position": {
                "vs_sma_20": "above" if current_price > sma_20.iloc[-1] else "below" if not pd.isna(sma_20.iloc[-1]) else "unknown",
                "vs_sma_50": "above" if current_price > sma_50.iloc[-1] else "below" if not pd.isna(sma_50.iloc[-1]) else "unknown",
                "vs_ema_12": "above" if current_price > ema_12.iloc[-1] else "below" if not pd.isna(ema_12.iloc[-1]) else "unknown",
            }
        }
        
        # 添加支撑阻力位分析
        if support_resistance:
            summary["support_resistance"] = support_resistance
        
        logger.info(f"技术分析摘要生成完成: {summary['symbol']}")
        
        return summary


# 便捷函数
def calculate_rsi(prices: Union[pd.Series, list], period: int = 14) -> pd.Series:
    """
    计算RSI指标的便捷函数
    
    Args:
        prices: 价格序列
        period: 计算周期
        
    Returns:
        RSI值序列
    """
    if isinstance(prices, list):
        prices = pd.Series(prices)
    
    return TechnicalIndicators.calculate_rsi(prices, period)


def calculate_macd(prices: Union[pd.Series, list], 
                  fast_period: int = 12, 
                  slow_period: int = 26, 
                  signal_period: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    计算MACD指标的便捷函数
    
    Args:
        prices: 价格序列
        fast_period: 快速周期，默认12
        slow_period: 慢速周期，默认26
        signal_period: 信号周期，默认9
        
    Returns:
        (MACD线, 信号线, 柱状图) 的元组
    """
    if isinstance(prices, list):
        prices = pd.Series(prices)
    
    return TechnicalIndicators.calculate_macd(prices, fast_period, slow_period, signal_period)


def calculate_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """
    计算ATR指标的便捷函数
    
    Args:
        df: 包含OHLC数据的DataFrame
        period: 计算周期，默认14
        
    Returns:
        ATR值序列
    """
    return TechnicalIndicators.calculate_atr(df, period)


def analyze_stock_technical(df: pd.DataFrame, price_column: str = 'Close') -> Dict[str, Any]:
    """
    分析股票技术指标的便捷函数
    
    Args:
        df: 股票数据DataFrame，需要包含OHLC数据
        price_column: 价格列名
        
    Returns:
        技术分析结果，包含RSI、MACD、ATR和移动平均线分析
    """
    indicators = TechnicalIndicators()
    return indicators.get_technical_summary(df, price_column) 