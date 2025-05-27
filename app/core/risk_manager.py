"""
风险管理模块
负责计算止损止盈价位、仓位大小、总仓位控制等风险管理功能
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import math

from .config import get_config

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """风险指标数据类"""
    max_position_value: float
    stop_loss_price: float
    take_profit_price: float
    position_size: int
    risk_amount: float
    reward_amount: float
    risk_reward_ratio: float
    portfolio_risk_pct: float


@dataclass
class PortfolioRisk:
    """投资组合风险数据类"""
    total_value: float
    total_exposure: float
    exposure_pct: float
    available_cash: float
    max_new_position: float
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL


class RiskManager:
    """
    风险管理器
    负责所有风险控制相关的计算和验证
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化风险管理器
        
        Args:
            config: 系统配置字典。如果为None，则使用系统配置
        """
        # 使用统一的配置读取方式
        if config is None:
            system_config = get_config()
            self.config = system_config.to_dict()
        else:
            self.config = config
            
        self.risk_config = self.config.get('risk', {})
        
        # 全局风险参数
        self.max_total_exposure = self.risk_config.get('max_total_exposure', 0.80)
        self.emergency_cash_reserve = self.risk_config.get('emergency_cash_reserve', 0.05)
        self.max_daily_trades = self.risk_config.get('max_daily_trades', 10)
        self.max_consecutive_losses = self.risk_config.get('max_consecutive_losses', 3)
        
        # 默认风险参数
        self.default_max_position_pct = self.risk_config.get('default_max_position_pct', 0.15)
        self.default_stop_loss_pct = self.risk_config.get('default_stop_loss_pct', 0.02)
        self.default_take_profit_pct = self.risk_config.get('default_take_profit_pct', 0.05)
        
        logger.info("风险管理器初始化完成")
    
    def calculate_stop_loss_take_profit(self, 
                                      entry_price: float, 
                                      action: str,
                                      stock_config: Dict) -> Tuple[float, float]:
        """
        计算止损止盈价位
        
        Args:
            entry_price: 入场价格
            action: 交易动作 ('BUY' 或 'SELL')
            stock_config: 股票配置
            
        Returns:
            Tuple[止损价位, 止盈价位]
        """
        try:
            risk_params = stock_config.get('risk', {})
            
            # 获取止损比例
            stop_loss_pct = risk_params.get('stop_loss_pct', self.default_stop_loss_pct)
            
            # 获取止盈设置
            take_profit_levels = risk_params.get('take_profit_levels', [])
            if not take_profit_levels:
                # 使用默认止盈
                take_profit_pct = risk_params.get('take_profit_pct', self.default_take_profit_pct)
                take_profit_levels = [{'level': take_profit_pct, 'quantity_pct': 1.0}]
            
            if action.upper() == 'BUY':
                # 买入：止损在下方，止盈在上方
                stop_loss_price = entry_price * (1 - stop_loss_pct)
                take_profit_price = entry_price * (1 + take_profit_levels[0]['level'])
                
            elif action.upper() == 'SELL':
                # 卖出：止损在上方，止盈在下方
                stop_loss_price = entry_price * (1 + stop_loss_pct)
                take_profit_price = entry_price * (1 - take_profit_levels[0]['level'])
                
            else:
                raise ValueError(f"无效的交易动作: {action}")
            
            logger.debug(f"计算止损止盈 - 入场价: ${entry_price:.2f}, "
                        f"止损: ${stop_loss_price:.2f}, 止盈: ${take_profit_price:.2f}")
            
            return stop_loss_price, take_profit_price
            
        except Exception as e:
            logger.error(f"计算止损止盈失败: {e}")
            # 返回保守的默认值
            if action.upper() == 'BUY':
                return entry_price * 0.98, entry_price * 1.03
            else:
                return entry_price * 1.02, entry_price * 0.97
    
    def calculate_position_size(self, 
                              entry_price: float,
                              stop_loss_price: float,
                              available_capital: float,
                              stock_config: Dict) -> int:
        """
        计算仓位大小
        
        Args:
            entry_price: 入场价格
            stop_loss_price: 止损价格
            available_capital: 可用资金
            stock_config: 股票配置
            
        Returns:
            建议的股票数量
        """
        try:
            risk_params = stock_config.get('risk', {})
            trading_params = stock_config.get('trading', {})
            
            # 获取仓位计算方式
            position_sizing = trading_params.get('position_sizing', 'fixed_percent')
            
            if position_sizing == 'fixed_percent':
                # 固定百分比仓位
                max_position_pct = risk_params.get('max_position_pct', self.default_max_position_pct)
                max_position_value = available_capital * max_position_pct
                shares = int(max_position_value / entry_price)
                
            elif position_sizing == 'risk_based':
                # 基于风险的仓位计算
                risk_per_share = abs(entry_price - stop_loss_price)
                max_risk_amount = available_capital * risk_params.get('max_risk_pct', 0.01)  # 默认1%风险
                shares = int(max_risk_amount / risk_per_share) if risk_per_share > 0 else 0
                
            elif position_sizing == 'fixed_amount':
                # 固定金额
                fixed_amount = trading_params.get('fixed_trade_amount', 1000)
                shares = int(fixed_amount / entry_price)
                
            else:
                # 默认使用固定百分比
                max_position_value = available_capital * self.default_max_position_pct
                shares = int(max_position_value / entry_price)
            
            # 应用最小和最大限制
            min_shares = trading_params.get('min_shares', 1)
            max_shares = trading_params.get('max_shares', 10000)
            
            shares = max(min_shares, min(shares, max_shares))
            
            # 检查最小交易金额
            min_trade_amount = trading_params.get('min_trade_amount', 100)
            if shares * entry_price < min_trade_amount:
                shares = max(1, int(min_trade_amount / entry_price))
            
            logger.debug(f"计算仓位大小 - 价格: ${entry_price:.2f}, "
                        f"可用资金: ${available_capital:.2f}, 建议股数: {shares}")
            
            return shares
            
        except Exception as e:
            logger.error(f"计算仓位大小失败: {e}")
            # 返回保守的默认值
            return max(1, int(1000 / entry_price))
    
    def calculate_risk_metrics(self,
                             entry_price: float,
                             stop_loss_price: float,
                             take_profit_price: float,
                             shares: int,
                             portfolio_value: float) -> RiskMetrics:
        """
        计算风险指标
        
        Args:
            entry_price: 入场价格
            stop_loss_price: 止损价格
            take_profit_price: 止盈价格
            shares: 股票数量
            portfolio_value: 投资组合总价值
            
        Returns:
            RiskMetrics: 风险指标对象
        """
        try:
            position_value = shares * entry_price
            risk_amount = abs(shares * (entry_price - stop_loss_price))
            reward_amount = abs(shares * (take_profit_price - entry_price))
            
            risk_reward_ratio = reward_amount / risk_amount if risk_amount > 0 else 0
            portfolio_risk_pct = risk_amount / portfolio_value if portfolio_value > 0 else 0
            
            return RiskMetrics(
                max_position_value=position_value,
                stop_loss_price=stop_loss_price,
                take_profit_price=take_profit_price,
                position_size=shares,
                risk_amount=risk_amount,
                reward_amount=reward_amount,
                risk_reward_ratio=risk_reward_ratio,
                portfolio_risk_pct=portfolio_risk_pct
            )
            
        except Exception as e:
            logger.error(f"计算风险指标失败: {e}")
            return RiskMetrics(0, 0, 0, 0, 0, 0, 0, 0)
    
    def assess_portfolio_risk(self, 
                            current_positions: List[Dict],
                            total_cash: float) -> PortfolioRisk:
        """
        评估投资组合风险
        
        Args:
            current_positions: 当前持仓列表
            total_cash: 总现金
            
        Returns:
            PortfolioRisk: 投资组合风险对象
        """
        try:
            # 计算总持仓价值
            total_position_value = sum(pos.get('market_value', 0) for pos in current_positions)
            total_value = total_position_value + total_cash
            
            # 计算暴露比例
            exposure_pct = total_position_value / total_value if total_value > 0 else 0
            
            # 计算可用于新仓位的资金
            emergency_reserve = total_value * self.emergency_cash_reserve
            available_for_trading = total_cash - emergency_reserve
            max_new_position = available_for_trading * self.default_max_position_pct
            
            # 评估风险级别
            if exposure_pct >= 0.9:
                risk_level = "CRITICAL"
            elif exposure_pct >= 0.8:
                risk_level = "HIGH"
            elif exposure_pct >= 0.6:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            return PortfolioRisk(
                total_value=total_value,
                total_exposure=total_position_value,
                exposure_pct=exposure_pct,
                available_cash=total_cash,
                max_new_position=max(0, max_new_position),
                risk_level=risk_level
            )
            
        except Exception as e:
            logger.error(f"评估投资组合风险失败: {e}")
            return PortfolioRisk(0, 0, 0, 0, 0, "UNKNOWN")
    
    def validate_trade_risk(self,
                          signal_data: Dict,
                          portfolio_risk: PortfolioRisk,
                          stock_config: Dict) -> Tuple[bool, str]:
        """
        验证交易风险是否可接受
        
        Args:
            signal_data: 信号数据
            portfolio_risk: 投资组合风险
            stock_config: 股票配置
            
        Returns:
            Tuple[是否通过验证, 验证消息]
        """
        try:
            # 检查投资组合总暴露
            if portfolio_risk.exposure_pct >= self.max_total_exposure:
                return False, f"投资组合暴露过高: {portfolio_risk.exposure_pct:.1%} >= {self.max_total_exposure:.1%}"
            
            # 检查可用资金
            required_capital = signal_data.get('position_value', 0)
            if required_capital > portfolio_risk.max_new_position:
                return False, f"所需资金超出限制: ${required_capital:.2f} > ${portfolio_risk.max_new_position:.2f}"
            
            # 检查风险回报比
            risk_reward_ratio = signal_data.get('risk_reward_ratio', 0)
            min_risk_reward = stock_config.get('risk', {}).get('min_risk_reward_ratio', 1.5)
            if risk_reward_ratio < min_risk_reward:
                return False, f"风险回报比过低: {risk_reward_ratio:.2f} < {min_risk_reward:.2f}"
            
            # 检查单笔风险
            portfolio_risk_pct = signal_data.get('portfolio_risk_pct', 0)
            max_single_risk = self.risk_config.get('max_single_risk_pct', 0.02)
            if portfolio_risk_pct > max_single_risk:
                return False, f"单笔风险过高: {portfolio_risk_pct:.2%} > {max_single_risk:.2%}"
            
            return True, "风险验证通过"
            
        except Exception as e:
            logger.error(f"验证交易风险失败: {e}")
            return False, f"风险验证错误: {str(e)}"
    
    def calculate_dynamic_stop_loss(self,
                                  entry_price: float,
                                  current_price: float,
                                  atr: float,
                                  action: str) -> float:
        """
        计算动态止损价位（基于ATR）
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            atr: 平均真实波动范围
            action: 交易动作
            
        Returns:
            动态止损价位
        """
        try:
            # ATR倍数，可以配置
            atr_multiplier = self.risk_config.get('atr_stop_multiplier', 2.0)
            
            if action.upper() == 'BUY':
                # 买入：止损在当前价格下方
                dynamic_stop = current_price - (atr * atr_multiplier)
                # 确保不会比原始止损更差
                original_stop = entry_price * (1 - self.default_stop_loss_pct)
                return max(dynamic_stop, original_stop)
                
            elif action.upper() == 'SELL':
                # 卖出：止损在当前价格上方
                dynamic_stop = current_price + (atr * atr_multiplier)
                # 确保不会比原始止损更差
                original_stop = entry_price * (1 + self.default_stop_loss_pct)
                return min(dynamic_stop, original_stop)
                
            return entry_price
            
        except Exception as e:
            logger.error(f"计算动态止损失败: {e}")
            return entry_price
    
    def get_risk_summary(self, portfolio_risk: PortfolioRisk) -> Dict:
        """
        获取风险摘要报告
        
        Args:
            portfolio_risk: 投资组合风险
            
        Returns:
            风险摘要字典
        """
        return {
            'portfolio_value': portfolio_risk.total_value,
            'total_exposure': portfolio_risk.total_exposure,
            'exposure_percentage': portfolio_risk.exposure_pct,
            'available_cash': portfolio_risk.available_cash,
            'max_new_position': portfolio_risk.max_new_position,
            'risk_level': portfolio_risk.risk_level,
            'emergency_reserve': portfolio_risk.total_value * self.emergency_cash_reserve,
            'risk_capacity': self.max_total_exposure - portfolio_risk.exposure_pct,
            'recommendations': self._get_risk_recommendations(portfolio_risk)
        }
    
    def _get_risk_recommendations(self, portfolio_risk: PortfolioRisk) -> List[str]:
        """获取风险管理建议"""
        recommendations = []
        
        if portfolio_risk.risk_level == "CRITICAL":
            recommendations.append("⚠️ 投资组合风险极高，建议立即减仓")
            recommendations.append("🛑 暂停新的交易，专注于风险控制")
            
        elif portfolio_risk.risk_level == "HIGH":
            recommendations.append("⚡ 投资组合风险较高，谨慎开新仓")
            recommendations.append("📉 考虑部分获利了结")
            
        elif portfolio_risk.risk_level == "MEDIUM":
            recommendations.append("⚖️ 投资组合风险适中，可适度交易")
            recommendations.append("🎯 关注个股风险分散")
            
        else:
            recommendations.append("✅ 投资组合风险较低，可正常交易")
            recommendations.append("📈 可考虑增加仓位")
        
        if portfolio_risk.available_cash < portfolio_risk.total_value * 0.1:
            recommendations.append("💰 现金比例偏低，建议保留更多现金")
            
        return recommendations
    
    def calculate_volatility(self, price_series) -> float:
        """
        计算历史波动率
        
        Args:
            price_series: 价格序列
            
        Returns:
            年化波动率
        """
        try:
            import pandas as pd
            import numpy as np
            
            if isinstance(price_series, pd.Series):
                returns = price_series.pct_change().dropna()
            else:
                returns = pd.Series(price_series).pct_change().dropna()
            
            # 计算年化波动率（假设252个交易日）
            volatility = returns.std() * np.sqrt(252)
            return volatility
            
        except Exception as e:
            logger.error(f"计算波动率失败: {e}")
            return 0.0
    
    def calculate_max_drawdown(self, price_series) -> float:
        """
        计算最大回撤
        
        Args:
            price_series: 价格序列
            
        Returns:
            最大回撤（负值）
        """
        try:
            import pandas as pd
            import numpy as np
            
            if isinstance(price_series, pd.Series):
                prices = price_series
            else:
                prices = pd.Series(price_series)
            
            # 计算累计最高价
            peak = prices.expanding().max()
            
            # 计算回撤
            drawdown = (prices - peak) / peak
            
            # 返回最大回撤
            max_drawdown = drawdown.min()
            return max_drawdown
            
        except Exception as e:
            logger.error(f"计算最大回撤失败: {e}")
            return 0.0
    
    def calculate_var(self, price_series, confidence: float = 0.95) -> float:
        """
        计算风险价值(VaR)
        
        Args:
            price_series: 价格序列
            confidence: 置信度
            
        Returns:
            VaR值（负值表示损失）
        """
        try:
            import pandas as pd
            import numpy as np
            
            if isinstance(price_series, pd.Series):
                returns = price_series.pct_change().dropna()
            else:
                returns = pd.Series(price_series).pct_change().dropna()
            
            # 计算VaR
            var = np.percentile(returns, (1 - confidence) * 100)
            return var
            
        except Exception as e:
            logger.error(f"计算VaR失败: {e}")
            return 0.0
    
 