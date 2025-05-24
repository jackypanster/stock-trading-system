"""
数据获取模块
Data Fetcher Module

提供统一的股票数据获取接口，支持多数据源和缓存机制。
"""

import yfinance as yf
import pandas as pd
import numpy as np
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
import pickle
import hashlib

from ..utils.logger import get_data_logger
from ..core.config import get_config

logger = get_data_logger()


class DataFetchError(Exception):
    """数据获取错误"""
    pass


class StockDataFetcher:
    """
    股票数据获取器
    
    支持实时数据、历史数据获取，具备缓存和错误重试机制。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据获取器
        
        Args:
            config: 配置字典，如果为None则使用全局配置
        """
        self.config = config or get_config().get('data', {})
        self.cache_dir = Path("data/cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 缓存设置
        self.cache_ttl = {
            'price': self.config.get('cache', {}).get('price_ttl', 60),      # 60秒
            'history': self.config.get('cache', {}).get('history_ttl', 3600), # 1小时
            'info': self.config.get('cache', {}).get('info_ttl', 86400)       # 24小时
        }
        
        # API限制
        self.rate_limits = self.config.get('rate_limits', {})
        self.last_request_time = 0
        
        # 数据源配置
        self.primary_source = self.config.get('primary_source', 'yfinance')
        self.backup_sources = self.config.get('backup_sources', ['mock'])
        self.current_source = self.primary_source
        self.source_failures = {}  # 记录各数据源失败次数
        self.max_failures = 3  # 最大失败次数后切换
        
        logger.info(f"股票数据获取器初始化完成，主数据源: {self.primary_source}")
    
    def _enforce_rate_limit(self):
        """强制执行API请求频率限制"""
        min_interval = 60 / self.rate_limits.get('requests_per_minute', 300)
        
        elapsed = time.time() - self.last_request_time
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug(f"API限制等待: {sleep_time:.2f}秒")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _get_cache_key(self, symbol: str, data_type: str, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            symbol: 股票代码
            data_type: 数据类型
            **kwargs: 其他参数
            
        Returns:
            缓存键字符串
        """
        key_data = f"{symbol}_{data_type}_{str(sorted(kwargs.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{cache_key}.pkl"
    
    def _save_to_cache(self, cache_key: str, data: Any, data_type: str):
        """
        保存数据到缓存
        
        Args:
            cache_key: 缓存键
            data: 要缓存的数据
            data_type: 数据类型
        """
        try:
            cache_data = {
                'data': data,
                'timestamp': datetime.now(),
                'type': data_type
            }
            
            cache_path = self._get_cache_path(cache_key)
            with open(cache_path, 'wb') as f:
                pickle.dump(cache_data, f)
            
            logger.debug(f"数据已缓存: {cache_key}")
            
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")
    
    def _load_from_cache(self, cache_key: str, data_type: str) -> Optional[Any]:
        """
        从缓存加载数据
        
        Args:
            cache_key: 缓存键
            data_type: 数据类型
            
        Returns:
            缓存的数据或None
        """
        try:
            cache_path = self._get_cache_path(cache_key)
            if not cache_path.exists():
                return None
            
            with open(cache_path, 'rb') as f:
                cache_data = pickle.load(f)
            
            # 检查缓存是否过期
            cache_age = (datetime.now() - cache_data['timestamp']).total_seconds()
            ttl = self.cache_ttl.get(data_type, 3600)
            
            if cache_age > ttl:
                logger.debug(f"缓存已过期: {cache_key}")
                return None
            
            logger.debug(f"从缓存加载数据: {cache_key}")
            return cache_data['data']
            
        except Exception as e:
            logger.warning(f"缓存加载失败: {e}")
            return None
    
    def _should_use_backup(self, source: str) -> bool:
        """
        判断是否应该切换到备用数据源
        
        Args:
            source: 数据源名称
            
        Returns:
            是否切换到备用源
        """
        failure_count = self.source_failures.get(source, 0)
        return failure_count >= self.max_failures
    
    def _record_source_failure(self, source: str):
        """记录数据源失败"""
        self.source_failures[source] = self.source_failures.get(source, 0) + 1
        logger.warning(f"数据源 {source} 失败 {self.source_failures[source]} 次")
        
        # 如果主数据源失败太多次，切换到备用源
        if source == self.primary_source and self._should_use_backup(source):
            for backup in self.backup_sources:
                if not self._should_use_backup(backup):
                    logger.warning(f"主数据源失败过多，切换到备用数据源: {backup}")
                    self.current_source = backup
                    break
    
    def _record_source_success(self, source: str):
        """记录数据源成功，重置失败计数"""
        if source in self.source_failures:
            del self.source_failures[source]
    
    def _get_data_with_fallback(self, operation_name: str, primary_func, backup_func, *args, **kwargs):
        """
        使用备用机制获取数据
        
        Args:
            operation_name: 操作名称
            primary_func: 主数据源函数
            backup_func: 备用数据源函数
            *args, **kwargs: 传递给函数的参数
            
        Returns:
            数据结果
            
        Raises:
            DataFetchError: 所有数据源都失败
        """
        # 先尝试当前数据源
        try:
            if self.current_source == self.primary_source:
                result = primary_func(*args, **kwargs)
                self._record_source_success(self.current_source)
                return result
            else:
                # 当前使用备用源
                result = backup_func(*args, **kwargs)
                self._record_source_success(self.current_source)
                return result
                
        except Exception as e:
            logger.warning(f"{operation_name} 使用 {self.current_source} 失败: {e}")
            self._record_source_failure(self.current_source)
            
            # 如果当前是主数据源，尝试备用源
            if self.current_source == self.primary_source:
                for backup in self.backup_sources:
                    if not self._should_use_backup(backup):
                        try:
                            logger.info(f"{operation_name} 尝试备用数据源: {backup}")
                            if backup == 'mock':
                                # 创建临时的模拟数据获取器
                                mock_fetcher = MockDataFetcher(self.config)
                                if operation_name == '获取价格':
                                    result = mock_fetcher.get_current_price(*args, **kwargs)
                                elif operation_name == '获取历史数据':
                                    result = mock_fetcher.get_historical_data(*args, **kwargs)
                                elif operation_name == '获取股票信息':
                                    result = mock_fetcher.get_stock_info(*args, **kwargs)
                                else:
                                    result = backup_func(*args, **kwargs)
                            else:
                                result = backup_func(*args, **kwargs)
                            
                            self._record_source_success(backup)
                            self.current_source = backup
                            logger.info(f"{operation_name} 成功切换到备用数据源: {backup}")
                            return result
                            
                        except Exception as backup_error:
                            logger.warning(f"{operation_name} 备用数据源 {backup} 也失败: {backup_error}")
                            self._record_source_failure(backup)
                            continue
            
            # 所有数据源都失败
            raise DataFetchError(f"{operation_name} 失败：所有数据源不可用")
    
    def reset_sources(self):
        """重置数据源状态，回到主数据源"""
        self.current_source = self.primary_source
        self.source_failures.clear()
        logger.info("数据源状态已重置，回到主数据源")
    
    def get_source_status(self) -> Dict[str, Any]:
        """
        获取数据源状态信息
        
        Returns:
            数据源状态字典
        """
        return {
            'primary_source': self.primary_source,
            'current_source': self.current_source,
            'backup_sources': self.backup_sources,
            'source_failures': self.source_failures.copy(),
            'max_failures': self.max_failures
        }
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票当前价格
        
        Args:
            symbol: 股票代码
            
        Returns:
            包含价格信息的字典
            
        Raises:
            DataFetchError: 数据获取失败
        """
        # 检查缓存
        cache_key = self._get_cache_key(symbol, 'price')
        cached_data = self._load_from_cache(cache_key, 'price')
        if cached_data:
            return cached_data
        
        def _get_price_from_yfinance(symbol):
            """从yfinance获取价格"""
            logger.info(f"获取 {symbol} 当前价格 (yfinance)")
            
            # 强制执行频率限制
            self._enforce_rate_limit()
            
            # 使用yfinance获取数据
            ticker = yf.Ticker(symbol)
            
            # 首先尝试fast_info
            try:
                fast_info = ticker.fast_info
                
                # 提取关键价格信息
                price_data = {
                    'symbol': symbol.upper(),
                    'current_price': fast_info.get('lastPrice'),
                    'previous_close': fast_info.get('previousClose', fast_info.get('regularMarketPreviousClose')),
                    'open_price': fast_info.get('open'),
                    'day_high': fast_info.get('dayHigh'),
                    'day_low': fast_info.get('dayLow'),
                    'volume': fast_info.get('lastVolume'),
                    'market_cap': fast_info.get('marketCap'),
                    'timestamp': datetime.now(),
                    'currency': fast_info.get('currency', 'USD'),
                    'exchange': fast_info.get('exchange'),
                    'timezone': fast_info.get('timezone'),
                    'fifty_day_avg': fast_info.get('fiftyDayAverage'),
                    'two_hundred_day_avg': fast_info.get('twoHundredDayAverage'),
                    'year_high': fast_info.get('yearHigh'),
                    'year_low': fast_info.get('yearLow'),
                    'year_change': fast_info.get('yearChange')
                }
                
            except Exception as e:
                logger.warning(f"fast_info获取失败，尝试使用info: {e}")
                # 如果fast_info失败，回退到info
                info = ticker.info
                
                # 提取关键价格信息
                price_data = {
                    'symbol': symbol.upper(),
                    'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                    'previous_close': info.get('previousClose', info.get('regularMarketPreviousClose')),
                    'open_price': info.get('open', info.get('regularMarketOpen')),
                    'day_high': info.get('dayHigh', info.get('regularMarketDayHigh')),
                    'day_low': info.get('dayLow', info.get('regularMarketDayLow')),
                    'volume': info.get('volume', info.get('regularMarketVolume')),
                    'market_cap': info.get('marketCap'),
                    'timestamp': datetime.now(),
                    'currency': info.get('currency', 'USD'),
                    'exchange': info.get('exchange'),
                    'timezone': info.get('timeZoneFullName')
                }
            
            # 计算变化
            if price_data['current_price'] and price_data['previous_close']:
                price_data['change'] = price_data['current_price'] - price_data['previous_close']
                price_data['change_percent'] = (price_data['change'] / price_data['previous_close']) * 100
            
            return price_data
        
        def _get_price_from_mock(symbol):
            """从模拟数据源获取价格"""
            mock_fetcher = MockDataFetcher(self.config)
            return mock_fetcher.get_current_price(symbol)
        
        try:
            # 使用备用机制获取数据
            price_data = self._get_data_with_fallback(
                "获取价格",
                _get_price_from_yfinance,
                _get_price_from_mock,
                symbol
            )
            
            # 缓存数据
            self._save_to_cache(cache_key, price_data, 'price')
            
            logger.info(f"成功获取 {symbol} 价格: ${price_data['current_price']} (数据源: {self.current_source})")
            return price_data
            
        except Exception as e:
            error_msg = f"获取 {symbol} 价格失败: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
    
    def get_historical_data(self, symbol: str, period: str = "1mo", 
                          interval: str = "1d") -> pd.DataFrame:
        """
        获取历史数据
        
        Args:
            symbol: 股票代码
            period: 时间周期 (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
            interval: 数据间隔 (1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo, 3mo)
            
        Returns:
            历史数据DataFrame
            
        Raises:
            DataFetchError: 数据获取失败
        """
        # 检查缓存
        cache_key = self._get_cache_key(symbol, 'history', period=period, interval=interval)
        cached_data = self._load_from_cache(cache_key, 'history')
        if cached_data is not None:
            return cached_data
        
        try:
            logger.info(f"获取 {symbol} 历史数据: {period}, {interval}")
            
            # 强制执行频率限制
            self._enforce_rate_limit()
            
            # 使用yfinance获取数据
            ticker = yf.Ticker(symbol)
            hist_data = ticker.history(period=period, interval=interval)
            
            if hist_data.empty:
                raise DataFetchError(f"未获取到 {symbol} 的历史数据")
            
            # 添加一些有用的列
            hist_data['Symbol'] = symbol.upper()
            hist_data['Daily_Return'] = hist_data['Close'].pct_change()
            hist_data['Price_Range'] = hist_data['High'] - hist_data['Low']
            hist_data['Price_Range_Pct'] = (hist_data['Price_Range'] / hist_data['Close']) * 100
            
            # 缓存数据
            self._save_to_cache(cache_key, hist_data, 'history')
            
            logger.info(f"成功获取 {symbol} 历史数据: {len(hist_data)} 条记录")
            return hist_data
            
        except Exception as e:
            error_msg = f"获取 {symbol} 历史数据失败: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """
        获取股票详细信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            股票信息字典
            
        Raises:
            DataFetchError: 数据获取失败
        """
        # 检查缓存
        cache_key = self._get_cache_key(symbol, 'info')
        cached_data = self._load_from_cache(cache_key, 'info')
        if cached_data:
            return cached_data
        
        try:
            logger.info(f"获取 {symbol} 股票信息")
            
            # 强制执行频率限制
            self._enforce_rate_limit()
            
            # 使用yfinance获取数据
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            # 提取关键信息
            stock_info = {
                'symbol': symbol.upper(),
                'company_name': info.get('longName', info.get('shortName')),
                'sector': info.get('sector'),
                'industry': info.get('industry'),
                'country': info.get('country'),
                'website': info.get('website'),
                'business_summary': info.get('longBusinessSummary'),
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'price_to_book': info.get('priceToBook'),
                'dividend_yield': info.get('dividendYield'),
                'beta': info.get('beta'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                'average_volume': info.get('averageVolume'),
                'shares_outstanding': info.get('sharesOutstanding'),
                'float_shares': info.get('floatShares'),
                'timestamp': datetime.now()
            }
            
            # 缓存数据
            self._save_to_cache(cache_key, stock_info, 'info')
            
            logger.info(f"成功获取 {symbol} 股票信息")
            return stock_info
            
        except Exception as e:
            error_msg = f"获取 {symbol} 股票信息失败: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
    
    def get_multiple_quotes(self, symbols: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取多只股票的报价
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            以股票代码为键的报价字典
        """
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = self.get_current_price(symbol)
                # 添加小延迟避免频率限制
                time.sleep(0.1)
            except DataFetchError as e:
                logger.warning(f"获取 {symbol} 数据失败: {e}")
                results[symbol] = None
        
        return results
    
    def test_connection(self, symbol: str = "AAPL") -> bool:
        """
        测试数据源连接
        
        Args:
            symbol: 用于测试的股票代码
            
        Returns:
            连接是否成功
        """
        try:
            logger.info(f"测试数据源连接，使用股票: {symbol}")
            price_data = self.get_current_price(symbol)
            
            if price_data and price_data.get('current_price'):
                logger.info("数据源连接测试成功")
                return True
            else:
                logger.error("数据源连接测试失败：未获取到有效价格")
                return False
                
        except Exception as e:
            logger.error(f"数据源连接测试失败: {e}")
            return False
    
    def clear_cache(self, symbol: Optional[str] = None, data_type: Optional[str] = None):
        """
        清理缓存
        
        Args:
            symbol: 指定股票代码，None表示所有
            data_type: 指定数据类型，None表示所有
        """
        try:
            if symbol and data_type:
                # 清理特定缓存
                cache_key = self._get_cache_key(symbol, data_type)
                cache_path = self._get_cache_path(cache_key)
                if cache_path.exists():
                    cache_path.unlink()
                    logger.info(f"已清理缓存: {symbol} - {data_type}")
            else:
                # 清理所有缓存
                for cache_file in self.cache_dir.glob("*.pkl"):
                    cache_file.unlink()
                logger.info("已清理所有缓存")
                
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")


# 全局数据获取器实例
_global_fetcher: Optional[StockDataFetcher] = None


def get_fetcher() -> StockDataFetcher:
    """
    获取全局数据获取器实例
    
    Returns:
        StockDataFetcher实例
    """
    global _global_fetcher
    if _global_fetcher is None:
        _global_fetcher = StockDataFetcher()
    return _global_fetcher


# 便捷函数
def get_stock_price(symbol: str) -> Dict[str, Any]:
    """获取股票当前价格"""
    return get_fetcher().get_current_price(symbol)


def get_stock_history(symbol: str, period: str = "1mo") -> pd.DataFrame:
    """获取股票历史数据"""
    return get_fetcher().get_historical_data(symbol, period)


def get_stock_info(symbol: str) -> Dict[str, Any]:
    """获取股票信息"""
    return get_fetcher().get_stock_info(symbol)


class MockDataFetcher(StockDataFetcher):
    """
    模拟数据获取器
    
    用于演示和测试目的，生成模拟股票数据。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化模拟数据获取器"""
        super().__init__(config)
        logger.info("模拟数据获取器初始化完成")
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """获取模拟的股票当前价格"""
        # 检查缓存
        cache_key = self._get_cache_key(symbol, 'price')
        cached_data = self._load_from_cache(cache_key, 'price')
        if cached_data:
            return cached_data
        
        try:
            logger.info(f"获取 {symbol} 模拟价格数据")
            
            import random
            import time
            
            # 模拟网络延迟
            time.sleep(0.5)
            
            # 根据股票代码生成不同的基础价格
            base_prices = {
                'AAPL': 180.0,
                'TSLA': 250.0,
                'GOOGL': 140.0,
                'MSFT': 340.0,
                'NVDA': 450.0,
                'AMZN': 130.0,
                'META': 320.0
            }
            
            base_price = base_prices.get(symbol.upper(), 100.0)
            
            # 生成随机价格波动
            price_variation = random.uniform(-0.05, 0.05)  # ±5%
            current_price = base_price * (1 + price_variation)
            previous_close = base_price
            
            # 生成日内波动
            daily_range = base_price * 0.03  # 3%日内波动
            open_price = current_price + random.uniform(-daily_range/2, daily_range/2)
            day_high = current_price + random.uniform(0, daily_range)
            day_low = current_price - random.uniform(0, daily_range)
            
            # 确保价格逻辑正确
            day_high = max(day_high, current_price, open_price)
            day_low = min(day_low, current_price, open_price)
            
            price_data = {
                'symbol': symbol.upper(),
                'current_price': round(current_price, 2),
                'previous_close': round(previous_close, 2),
                'open_price': round(open_price, 2),
                'day_high': round(day_high, 2),
                'day_low': round(day_low, 2),
                'volume': random.randint(1000000, 50000000),
                'market_cap': random.randint(100000000000, 3000000000000),
                'timestamp': datetime.now(),
                'currency': 'USD',
                'exchange': 'NASDAQ',
                'timezone': 'America/New_York'
            }
            
            # 计算变化
            price_data['change'] = round(current_price - previous_close, 2)
            price_data['change_percent'] = round((price_data['change'] / previous_close) * 100, 2)
            
            # 缓存数据
            self._save_to_cache(cache_key, price_data, 'price')
            
            logger.info(f"成功生成 {symbol} 模拟价格: ${price_data['current_price']}")
            return price_data
            
        except Exception as e:
            error_msg = f"生成 {symbol} 模拟价格失败: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
    
    def get_historical_data(self, symbol: str, period: str = "1mo", 
                          interval: str = "1d") -> pd.DataFrame:
        """获取模拟历史数据"""
        # 检查缓存
        cache_key = self._get_cache_key(symbol, 'history', period=period, interval=interval)
        cached_data = self._load_from_cache(cache_key, 'history')
        if cached_data is not None:
            return cached_data
        
        try:
            logger.info(f"生成 {symbol} 模拟历史数据: {period}, {interval}")
            
            import random
            import time
            
            # 模拟网络延迟
            time.sleep(0.3)
            
            # 解析期间
            days_map = {
                '1d': 1, '2d': 2, '5d': 5, '10d': 10,
                '1mo': 30, '3mo': 90, '6mo': 180, '1y': 365
            }
            days = days_map.get(period, 30)
            
            # 生成日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            date_range = pd.date_range(start=start_date, end=end_date, freq='D')
            
            # 基础价格
            base_prices = {
                'AAPL': 180.0, 'TSLA': 250.0, 'GOOGL': 140.0,
                'MSFT': 340.0, 'NVDA': 450.0, 'AMZN': 130.0, 'META': 320.0
            }
            base_price = base_prices.get(symbol.upper(), 100.0)
            
            # 生成价格序列
            data = []
            current_price = base_price
            
            for date in date_range:
                # 只保留工作日
                if date.weekday() >= 5:  # 周六日跳过
                    continue
                
                # 随机日间波动
                daily_change = random.gauss(0, 0.02)  # 2%标准差
                current_price *= (1 + daily_change)
                
                # 确保价格不会太离谱
                current_price = max(base_price * 0.5, min(base_price * 1.5, current_price))
                
                # 生成OHLC
                daily_volatility = current_price * 0.03  # 3%日内波动
                open_price = current_price + random.uniform(-daily_volatility/2, daily_volatility/2)
                close_price = current_price
                high_price = max(open_price, close_price) + random.uniform(0, daily_volatility/2)
                low_price = min(open_price, close_price) - random.uniform(0, daily_volatility/2)
                volume = random.randint(1000000, 100000000)
                
                data.append({
                    'Open': round(open_price, 2),
                    'High': round(high_price, 2),
                    'Low': round(low_price, 2),
                    'Close': round(close_price, 2),
                    'Volume': volume
                })
            
            # 创建DataFrame
            hist_data = pd.DataFrame(data, index=date_range[:len(data)])
            hist_data.index.name = 'Date'
            
            # 添加额外列
            hist_data['Symbol'] = symbol.upper()
            hist_data['Daily_Return'] = hist_data['Close'].pct_change()
            hist_data['Price_Range'] = hist_data['High'] - hist_data['Low']
            hist_data['Price_Range_Pct'] = (hist_data['Price_Range'] / hist_data['Close']) * 100
            
            # 缓存数据
            self._save_to_cache(cache_key, hist_data, 'history')
            
            logger.info(f"成功生成 {symbol} 模拟历史数据: {len(hist_data)} 条记录")
            return hist_data
            
        except Exception as e:
            error_msg = f"生成 {symbol} 模拟历史数据失败: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
    
    def get_stock_info(self, symbol: str) -> Dict[str, Any]:
        """获取模拟股票信息"""
        # 检查缓存
        cache_key = self._get_cache_key(symbol, 'info')
        cached_data = self._load_from_cache(cache_key, 'info')
        if cached_data:
            return cached_data
        
        try:
            logger.info(f"生成 {symbol} 模拟股票信息")
            
            import random
            import time
            
            # 模拟网络延迟
            time.sleep(0.2)
            
            # 模拟公司信息
            company_info = {
                'AAPL': {'name': 'Apple Inc.', 'sector': 'Technology', 'industry': 'Consumer Electronics'},
                'TSLA': {'name': 'Tesla, Inc.', 'sector': 'Consumer Cyclical', 'industry': 'Auto Manufacturers'},
                'GOOGL': {'name': 'Alphabet Inc.', 'sector': 'Communication Services', 'industry': 'Internet Content & Information'},
                'MSFT': {'name': 'Microsoft Corporation', 'sector': 'Technology', 'industry': 'Software Infrastructure'},
                'NVDA': {'name': 'NVIDIA Corporation', 'sector': 'Technology', 'industry': 'Semiconductors'},
                'AMZN': {'name': 'Amazon.com, Inc.', 'sector': 'Consumer Cyclical', 'industry': 'Internet Retail'},
                'META': {'name': 'Meta Platforms, Inc.', 'sector': 'Communication Services', 'industry': 'Internet Content & Information'}
            }
            
            info = company_info.get(symbol.upper(), {
                'name': f'{symbol.upper()} Corporation',
                'sector': 'Technology',
                'industry': 'Software'
            })
            
            stock_info = {
                'symbol': symbol.upper(),
                'company_name': info['name'],
                'sector': info['sector'],
                'industry': info['industry'],
                'country': 'United States',
                'website': f'https://www.{symbol.lower()}.com',
                'business_summary': f'{info["name"]} operates in the {info["industry"]} industry.',
                'market_cap': random.randint(100000000000, 3000000000000),
                'enterprise_value': random.randint(150000000000, 3200000000000),
                'trailing_pe': round(random.uniform(15, 35), 2),
                'forward_pe': round(random.uniform(12, 30), 2),
                'price_to_book': round(random.uniform(1.5, 8.0), 2),
                'dividend_yield': round(random.uniform(0, 0.03), 4) if random.random() > 0.3 else None,
                'beta': round(random.uniform(0.8, 1.5), 2),
                '52_week_high': round(random.uniform(150, 500), 2),
                '52_week_low': round(random.uniform(80, 200), 2),
                'average_volume': random.randint(10000000, 100000000),
                'shares_outstanding': random.randint(1000000000, 20000000000),
                'float_shares': random.randint(900000000, 19000000000),
                'timestamp': datetime.now()
            }
            
            # 缓存数据
            self._save_to_cache(cache_key, stock_info, 'info')
            
            logger.info(f"成功生成 {symbol} 模拟股票信息")
            return stock_info
            
        except Exception as e:
            error_msg = f"生成 {symbol} 模拟股票信息失败: {e}"
            logger.error(error_msg)
            raise DataFetchError(error_msg)
    
    def test_connection(self, symbol: str = "AAPL") -> bool:
        """测试模拟数据源连接"""
        try:
            logger.info(f"测试模拟数据源连接，使用股票: {symbol}")
            price_data = self.get_current_price(symbol)
            
            if price_data and price_data.get('current_price'):
                logger.info("模拟数据源连接测试成功")
                return True
            else:
                logger.error("模拟数据源连接测试失败：未获取到有效价格")
                return False
                
        except Exception as e:
            logger.error(f"模拟数据源连接测试失败: {e}")
            return False


# 便捷函数：根据配置决定使用真实数据还是模拟数据
def get_fetcher(use_mock: bool = False) -> StockDataFetcher:
    """
    获取数据获取器实例
    
    Args:
        use_mock: 是否使用模拟数据获取器
        
    Returns:
        StockDataFetcher实例
    """
    global _global_fetcher
    
    # 从配置中检查是否使用模拟数据
    config = get_config()
    use_mock_from_config = config.get('data.use_mock_data', False)
    
    if use_mock or use_mock_from_config:
        if not isinstance(_global_fetcher, MockDataFetcher):
            _global_fetcher = MockDataFetcher()
    else:
        if not isinstance(_global_fetcher, StockDataFetcher) or isinstance(_global_fetcher, MockDataFetcher):
            _global_fetcher = StockDataFetcher()
    
    return _global_fetcher 


class FailingDataFetcher(StockDataFetcher):
    """
    故意失败的数据获取器
    
    用于测试备用数据源切换机制。
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, fail_after: int = 0):
        """
        初始化故意失败的数据获取器
        
        Args:
            config: 配置字典
            fail_after: 在第几次调用后开始失败（0表示立即失败）
        """
        super().__init__(config)
        self.fail_after = fail_after
        self.call_count = 0
        logger.info(f"故意失败的数据获取器初始化完成，将在第{fail_after}次调用后失败")
    
    def get_current_price(self, symbol: str) -> Dict[str, Any]:
        """模拟获取价格，在指定次数后失败"""
        self.call_count += 1
        
        if self.call_count > self.fail_after:
            logger.warning(f"模拟主数据源失败 (第{self.call_count}次调用)")
            raise DataFetchError("模拟的数据源失败")
        
        # 前几次成功
        logger.info(f"模拟主数据源成功 (第{self.call_count}次调用)")
        return {
            'symbol': symbol.upper(),
            'current_price': 100.0 + self.call_count,  # 简单的价格
            'previous_close': 100.0,
            'timestamp': datetime.now(),
            'currency': 'USD',
            'exchange': 'TEST'
        }


def create_test_fetcher_with_failing_primary() -> StockDataFetcher:
    """
    创建用于测试的数据获取器，主数据源会失败
    
    Returns:
        配置了故意失败主数据源的数据获取器
    """
    # 创建一个会失败的获取器
    failing_fetcher = FailingDataFetcher(fail_after=2)  # 前2次成功，之后失败
    
    # 重写其备用机制测试
    original_get_price = failing_fetcher.get_current_price
    
    def mock_yfinance_that_fails(symbol):
        """模拟yfinance失败"""
        failing_fetcher.call_count += 1
        if failing_fetcher.call_count > failing_fetcher.fail_after:
            raise DataFetchError("模拟yfinance失败")
        return original_get_price(symbol)
    
    def mock_backup_source(symbol):
        """模拟备用数据源（总是成功）"""
        mock_fetcher = MockDataFetcher()
        return mock_fetcher.get_current_price(symbol)
    
    # 重写_get_data_with_fallback来模拟失败
    def test_get_current_price(symbol: str):
        try:
            return failing_fetcher._get_data_with_fallback(
                "获取价格",
                mock_yfinance_that_fails,
                mock_backup_source,
                symbol
            )
        except Exception as e:
            logger.error(f"测试获取价格失败: {e}")
            raise DataFetchError(str(e))
    
    # 添加测试方法
    failing_fetcher.test_get_current_price = test_get_current_price
    
    return failing_fetcher 