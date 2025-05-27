"""
定时数据获取调度器
Scheduled Data Fetcher

在美股交易时间内定时获取股票数据，避免API频率限制。
"""

import time
import threading
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Callable
import pytz
from pathlib import Path
import json
import logging

from ..utils.logger import get_data_logger
from ..core.config import get_config
from .fetcher import get_fetcher, DataFetchError

logger = get_data_logger()


class MarketTimeChecker:
    """美股交易时间检测器"""
    
    def __init__(self):
        self.eastern = pytz.timezone('America/New_York')
        self.market_open = "09:30"
        self.market_close = "16:00"
        
    def is_market_open(self, dt: Optional[datetime] = None) -> bool:
        """
        检查当前是否为美股交易时间
        
        Args:
            dt: 检查的时间，默认为当前时间
            
        Returns:
            是否为交易时间
        """
        if dt is None:
            dt = datetime.now()
        
        # 转换为美东时间
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        eastern_time = dt.astimezone(self.eastern)
        
        # 检查是否为工作日
        if eastern_time.weekday() >= 5:  # 周六、周日
            return False
        
        # 检查时间范围
        market_open_time = eastern_time.replace(
            hour=9, minute=30, second=0, microsecond=0
        )
        market_close_time = eastern_time.replace(
            hour=16, minute=0, second=0, microsecond=0
        )
        
        return market_open_time <= eastern_time <= market_close_time
    
    def get_next_market_open(self, dt: Optional[datetime] = None) -> datetime:
        """获取下一个开盘时间"""
        if dt is None:
            dt = datetime.now()
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        eastern_time = dt.astimezone(self.eastern)
        
        # 如果是工作日且在开盘前
        if eastern_time.weekday() < 5:
            market_open = eastern_time.replace(
                hour=9, minute=30, second=0, microsecond=0
            )
            if eastern_time < market_open:
                return market_open
        
        # 找到下一个工作日
        days_ahead = 1
        while True:
            next_day = eastern_time + timedelta(days=days_ahead)
            if next_day.weekday() < 5:  # 工作日
                return next_day.replace(
                    hour=9, minute=30, second=0, microsecond=0
                )
            days_ahead += 1
    
    def get_market_close_today(self, dt: Optional[datetime] = None) -> datetime:
        """获取今日收盘时间"""
        if dt is None:
            dt = datetime.now()
        
        if dt.tzinfo is None:
            dt = pytz.utc.localize(dt)
        
        eastern_time = dt.astimezone(self.eastern)
        
        return eastern_time.replace(
            hour=16, minute=0, second=0, microsecond=0
        )


class DataScheduler:
    """定时数据获取调度器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化调度器
        
        Args:
            config: 配置字典
        """
        self.config = config or get_config()
        self.market_checker = MarketTimeChecker()
        self.fetcher = None
        self.is_running = False
        self.scheduler_thread = None
        
        # 调度配置
        scheduler_config = self.config.get('scheduler', {})
        self.update_interval = scheduler_config.get('update_interval', 300)  # 5分钟
        self.max_daily_calls = scheduler_config.get('max_daily_calls', 7000)  # Yahoo Finance限制8000/天
        self.max_hourly_calls = scheduler_config.get('max_hourly_calls', 300)  # Yahoo Finance限制360/小时
        self.max_minute_calls = scheduler_config.get('max_minute_calls', 50)   # Yahoo Finance限制60/分钟
        self.watchlist = scheduler_config.get('watchlist', ['AMD', 'PONY'])
        
        # 状态跟踪
        self.daily_calls = 0
        self.hourly_calls = 0
        self.minute_calls = 0
        self.last_reset_date = datetime.now().date()
        self.last_reset_hour = datetime.now().hour
        self.last_reset_minute = datetime.now().minute
        self.call_history = []
        
        # 数据存储
        self.data_dir = Path("data/scheduled")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"数据调度器初始化完成，监控股票: {self.watchlist}")
        logger.info(f"更新间隔: {self.update_interval}秒")
        logger.info(f"API限制: {self.max_daily_calls}次/天, {self.max_hourly_calls}次/小时, {self.max_minute_calls}次/分钟")
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return
        
        self.is_running = True
        self.fetcher = get_fetcher(use_mock=False)
        
        # 清空之前的调度任务
        schedule.clear()
        
        # 设置定时任务
        schedule.every(self.update_interval).seconds.do(self._scheduled_fetch)
        
        # 启动调度线程
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        logger.info("数据调度器已启动")
    
    def stop(self):
        """停止调度器"""
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        logger.info("数据调度器已停止")
    
    def _run_scheduler(self):
        """运行调度器主循环"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(1)
            except Exception as e:
                logger.error(f"调度器运行错误: {e}")
                time.sleep(5)
    
    def _scheduled_fetch(self):
        """定时数据获取任务"""
        try:
            # 重置计数器
            self._reset_counters_if_needed()
            
            # 检查是否为交易时间
            if not self.market_checker.is_market_open():
                logger.debug("非交易时间，跳过数据获取")
                return
            
            # 检查API调用限制
            if self.daily_calls >= self.max_daily_calls:
                logger.warning(f"已达到每日API调用限制 ({self.max_daily_calls})")
                return
            
            if self.hourly_calls >= self.max_hourly_calls:
                logger.warning(f"已达到每小时API调用限制 ({self.max_hourly_calls})")
                return
                
            if self.minute_calls >= self.max_minute_calls:
                logger.warning(f"已达到每分钟API调用限制 ({self.max_minute_calls})")
                return
            
            # 获取数据
            self._fetch_watchlist_data()
            
        except Exception as e:
            logger.error(f"定时数据获取失败: {e}")
    
    def _reset_counters_if_needed(self):
        """如果需要，重置计数器"""
        now = datetime.now()
        today = now.date()
        current_hour = now.hour
        current_minute = now.minute
        
        # 重置每日计数器
        if today != self.last_reset_date:
            self.daily_calls = 0
            self.hourly_calls = 0
            self.minute_calls = 0
            self.last_reset_date = today
            self.last_reset_hour = current_hour
            self.last_reset_minute = current_minute
            self.call_history = []
            logger.info(f"重置每日API调用计数器: {today}")
        
        # 重置每小时计数器
        elif current_hour != self.last_reset_hour:
            self.hourly_calls = 0
            self.minute_calls = 0
            self.last_reset_hour = current_hour
            self.last_reset_minute = current_minute
            logger.debug(f"重置每小时API调用计数器: {current_hour}:00")
        
        # 重置每分钟计数器
        elif current_minute != self.last_reset_minute:
            self.minute_calls = 0
            self.last_reset_minute = current_minute
            logger.debug(f"重置每分钟API调用计数器: {current_hour}:{current_minute:02d}")
    
    def _fetch_watchlist_data(self):
        """获取监控列表数据"""
        success_count = 0
        
        for symbol in self.watchlist:
            try:
                # 获取当前价格
                price_data = self.fetcher.get_current_price(symbol)
                
                # 保存数据
                self._save_price_data(symbol, price_data)
                
                # 更新统计
                self.daily_calls += 1
                self.hourly_calls += 1
                self.minute_calls += 1
                self.call_history.append({
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'success': True
                })
                
                success_count += 1
                logger.info(f"成功获取 {symbol} 数据: ${price_data['current_price']}")
                
                # 添加延迟避免频率限制
                time.sleep(1)
                
            except DataFetchError as e:
                logger.error(f"获取 {symbol} 数据失败: {e}")
                self.call_history.append({
                    'symbol': symbol,
                    'timestamp': datetime.now(),
                    'success': False,
                    'error': str(e)
                })
            
            # 检查是否超过每日限制
            if self.daily_calls >= self.max_daily_calls:
                logger.warning("达到每日API调用限制，停止获取")
                break
        
        logger.info(f"本次获取完成: {success_count}/{len(self.watchlist)} 成功")
        logger.info(f"API调用统计: 今日{self.daily_calls}/{self.max_daily_calls}, 本小时{self.hourly_calls}/{self.max_hourly_calls}, 本分钟{self.minute_calls}/{self.max_minute_calls}")
    
    def _save_price_data(self, symbol: str, price_data: Dict[str, Any]):
        """保存价格数据到本地"""
        try:
            # 创建日期目录
            today = datetime.now().strftime("%Y-%m-%d")
            date_dir = self.data_dir / today
            date_dir.mkdir(exist_ok=True)
            
            # 保存数据
            timestamp = datetime.now().strftime("%H-%M-%S")
            filename = f"{symbol}_{timestamp}.json"
            filepath = date_dir / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(price_data, f, indent=2, default=str, ensure_ascii=False)
            
            logger.debug(f"保存 {symbol} 数据到: {filepath}")
            
        except Exception as e:
            logger.error(f"保存 {symbol} 数据失败: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            'is_running': self.is_running,
            'market_open': self.market_checker.is_market_open(),
            'daily_calls': self.daily_calls,
            'hourly_calls': self.hourly_calls,
            'minute_calls': self.minute_calls,
            'max_daily_calls': self.max_daily_calls,
            'max_hourly_calls': self.max_hourly_calls,
            'max_minute_calls': self.max_minute_calls,
            'watchlist': self.watchlist,
            'update_interval': self.update_interval,
            'last_reset_date': self.last_reset_date.isoformat(),
            'call_history_count': len(self.call_history)
        }
    
    def get_call_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取调用历史"""
        return self.call_history[-limit:]
    
    def add_to_watchlist(self, symbol: str):
        """添加股票到监控列表"""
        if symbol.upper() not in self.watchlist:
            self.watchlist.append(symbol.upper())
            logger.info(f"添加 {symbol.upper()} 到监控列表")
    
    def remove_from_watchlist(self, symbol: str):
        """从监控列表移除股票"""
        if symbol.upper() in self.watchlist:
            self.watchlist.remove(symbol.upper())
            logger.info(f"从监控列表移除 {symbol.upper()}")
    
    def force_fetch(self, symbol: Optional[str] = None):
        """强制获取数据（忽略时间和频率限制）"""
        if not self.fetcher:
            self.fetcher = get_fetcher(use_mock=False)
        
        symbols = [symbol.upper()] if symbol else self.watchlist
        
        for sym in symbols:
            try:
                price_data = self.fetcher.get_current_price(sym)
                self._save_price_data(sym, price_data)
                logger.info(f"强制获取 {sym} 数据成功: ${price_data['current_price']}")
            except DataFetchError as e:
                logger.error(f"强制获取 {sym} 数据失败: {e}")


# 全局调度器实例
_scheduler_instance = None


def get_scheduler(config: Optional[Dict[str, Any]] = None) -> DataScheduler:
    """获取全局调度器实例"""
    global _scheduler_instance
    
    if _scheduler_instance is None:
        _scheduler_instance = DataScheduler(config)
    
    return _scheduler_instance


def start_scheduler(config: Optional[Dict[str, Any]] = None):
    """启动全局调度器"""
    scheduler = get_scheduler(config)
    scheduler.start()
    return scheduler


def stop_scheduler():
    """停止全局调度器"""
    global _scheduler_instance
    
    if _scheduler_instance:
        _scheduler_instance.stop() 