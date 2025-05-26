"""
投资组合管理模块
负责跟踪持仓、现金余额、交易记录等
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """持仓数据类"""
    symbol: str
    shares: int
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pnl_pct: float
    last_updated: datetime
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        data = asdict(self)
        data['last_updated'] = self.last_updated.isoformat()
        return data


@dataclass
class Trade:
    """交易记录数据类"""
    timestamp: datetime
    symbol: str
    action: str  # BUY, SELL
    shares: int
    price: float
    total_value: float
    commission: float
    reason: str
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class Portfolio:
    """
    投资组合管理器
    跟踪现金、持仓、交易记录等
    """
    
    def __init__(self, initial_cash: float = 100000, data_file: str = "data/portfolio.json"):
        """
        初始化投资组合
        
        Args:
            initial_cash: 初始现金
            data_file: 数据文件路径
        """
        self.data_file = data_file
        self.cash = initial_cash
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        
        # 尝试加载已有数据
        self._load_data()
        
        logger.info(f"投资组合初始化完成 - 现金: ${self.cash:,.2f}")
    
    def _load_data(self):
        """从文件加载投资组合数据"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.cash = data.get('cash', self.cash)
                
                # 加载持仓
                positions_data = data.get('positions', {})
                for symbol, pos_data in positions_data.items():
                    pos_data['last_updated'] = datetime.fromisoformat(pos_data['last_updated'])
                    self.positions[symbol] = Position(**pos_data)
                
                # 加载交易记录
                trades_data = data.get('trades', [])
                for trade_data in trades_data:
                    trade_data['timestamp'] = datetime.fromisoformat(trade_data['timestamp'])
                    self.trades.append(Trade(**trade_data))
                
                logger.info(f"成功加载投资组合数据 - 持仓数: {len(self.positions)}, 交易记录: {len(self.trades)}")
                
        except Exception as e:
            logger.warning(f"加载投资组合数据失败: {e}, 使用默认设置")
    
    def _save_data(self):
        """保存投资组合数据到文件"""
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(self.data_file), exist_ok=True)
            
            data = {
                'cash': self.cash,
                'positions': {symbol: pos.to_dict() for symbol, pos in self.positions.items()},
                'trades': [trade.to_dict() for trade in self.trades],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.debug("投资组合数据已保存")
            
        except Exception as e:
            logger.error(f"保存投资组合数据失败: {e}")
    
    def buy_stock(self, symbol: str, shares: int, price: float, reason: str = "") -> bool:
        """
        买入股票
        
        Args:
            symbol: 股票代码
            shares: 股数
            price: 价格
            reason: 买入原因
            
        Returns:
            是否成功
        """
        try:
            total_cost = shares * price
            commission = total_cost * 0.001  # 假设0.1%手续费
            total_with_commission = total_cost + commission
            
            # 检查现金是否足够
            if total_with_commission > self.cash:
                logger.warning(f"现金不足 - 需要: ${total_with_commission:.2f}, 可用: ${self.cash:.2f}")
                return False
            
            # 扣除现金
            self.cash -= total_with_commission
            
            # 更新持仓
            if symbol in self.positions:
                # 已有持仓，计算新的平均成本
                pos = self.positions[symbol]
                total_shares = pos.shares + shares
                total_cost_basis = (pos.shares * pos.avg_cost) + total_cost
                new_avg_cost = total_cost_basis / total_shares
                
                pos.shares = total_shares
                pos.avg_cost = new_avg_cost
                pos.current_price = price
                pos.market_value = total_shares * price
                pos.unrealized_pnl = pos.market_value - total_cost_basis
                pos.unrealized_pnl_pct = pos.unrealized_pnl / total_cost_basis
                pos.last_updated = datetime.now()
            else:
                # 新建持仓
                self.positions[symbol] = Position(
                    symbol=symbol,
                    shares=shares,
                    avg_cost=price,
                    current_price=price,
                    market_value=shares * price,
                    unrealized_pnl=0,
                    unrealized_pnl_pct=0,
                    last_updated=datetime.now()
                )
            
            # 记录交易
            trade = Trade(
                timestamp=datetime.now(),
                symbol=symbol,
                action="BUY",
                shares=shares,
                price=price,
                total_value=total_cost,
                commission=commission,
                reason=reason
            )
            self.trades.append(trade)
            
            # 保存数据
            self._save_data()
            
            logger.info(f"买入成功 - {symbol}: {shares}股 @ ${price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"买入股票失败: {e}")
            return False
    
    def sell_stock(self, symbol: str, shares: int, price: float, reason: str = "") -> bool:
        """
        卖出股票
        
        Args:
            symbol: 股票代码
            shares: 股数
            price: 价格
            reason: 卖出原因
            
        Returns:
            是否成功
        """
        try:
            # 检查是否有足够持仓
            if symbol not in self.positions:
                logger.warning(f"没有{symbol}的持仓")
                return False
            
            pos = self.positions[symbol]
            if shares > pos.shares:
                logger.warning(f"持仓不足 - 持有: {pos.shares}, 卖出: {shares}")
                return False
            
            total_proceeds = shares * price
            commission = total_proceeds * 0.001  # 假设0.1%手续费
            net_proceeds = total_proceeds - commission
            
            # 增加现金
            self.cash += net_proceeds
            
            # 更新持仓
            if shares == pos.shares:
                # 全部卖出，删除持仓
                del self.positions[symbol]
            else:
                # 部分卖出，更新持仓
                pos.shares -= shares
                pos.current_price = price
                pos.market_value = pos.shares * price
                cost_basis = pos.shares * pos.avg_cost
                pos.unrealized_pnl = pos.market_value - cost_basis
                pos.unrealized_pnl_pct = pos.unrealized_pnl / cost_basis if cost_basis > 0 else 0
                pos.last_updated = datetime.now()
            
            # 记录交易
            trade = Trade(
                timestamp=datetime.now(),
                symbol=symbol,
                action="SELL",
                shares=shares,
                price=price,
                total_value=total_proceeds,
                commission=commission,
                reason=reason
            )
            self.trades.append(trade)
            
            # 保存数据
            self._save_data()
            
            logger.info(f"卖出成功 - {symbol}: {shares}股 @ ${price:.2f}")
            return True
            
        except Exception as e:
            logger.error(f"卖出股票失败: {e}")
            return False
    
    def update_prices(self, price_data: Dict[str, float]):
        """
        更新持仓股票的当前价格
        
        Args:
            price_data: {symbol: current_price} 字典
        """
        try:
            for symbol, current_price in price_data.items():
                if symbol in self.positions:
                    pos = self.positions[symbol]
                    pos.current_price = current_price
                    pos.market_value = pos.shares * current_price
                    cost_basis = pos.shares * pos.avg_cost
                    pos.unrealized_pnl = pos.market_value - cost_basis
                    pos.unrealized_pnl_pct = pos.unrealized_pnl / cost_basis if cost_basis > 0 else 0
                    pos.last_updated = datetime.now()
            
            # 保存更新后的数据
            self._save_data()
            
        except Exception as e:
            logger.error(f"更新价格失败: {e}")
    
    def get_total_value(self) -> float:
        """获取投资组合总价值"""
        total_position_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + total_position_value
    
    def get_positions_list(self) -> List[Dict]:
        """获取持仓列表"""
        return [pos.to_dict() for pos in self.positions.values()]
    
    def get_position(self, symbol: str) -> Optional[Position]:
        """获取特定股票的持仓"""
        return self.positions.get(symbol)
    
    def get_recent_trades(self, days: int = 7) -> List[Dict]:
        """获取最近的交易记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_trades = [
            trade.to_dict() for trade in self.trades 
            if trade.timestamp >= cutoff_date
        ]
        return sorted(recent_trades, key=lambda x: x['timestamp'], reverse=True)
    
    def get_portfolio_summary(self) -> Dict:
        """获取投资组合摘要"""
        total_value = self.get_total_value()
        total_position_value = sum(pos.market_value for pos in self.positions.values())
        total_unrealized_pnl = sum(pos.unrealized_pnl for pos in self.positions.values())
        
        return {
            'total_value': total_value,
            'cash': self.cash,
            'total_position_value': total_position_value,
            'total_unrealized_pnl': total_unrealized_pnl,
            'total_unrealized_pnl_pct': total_unrealized_pnl / (total_value - total_unrealized_pnl) if total_value > total_unrealized_pnl else 0,
            'cash_percentage': self.cash / total_value if total_value > 0 else 1,
            'position_count': len(self.positions),
            'trade_count': len(self.trades)
        }
    
    def reset_portfolio(self, initial_cash: float = 100000):
        """重置投资组合（用于测试）"""
        self.cash = initial_cash
        self.positions.clear()
        self.trades.clear()
        self._save_data()
        logger.info(f"投资组合已重置 - 初始现金: ${initial_cash:,.2f}")


# 导入缺失的模块
from datetime import timedelta 