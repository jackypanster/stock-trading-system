# 运维指南

## 1. 系统运维概述

### 1.1 架构特点
- **单体应用**：所有功能在一个进程中运行
- **本地部署**：个人电脑本地运行，无需复杂部署
- **SQLite数据库**：文件形式存储，易于备份和迁移
- **最小依赖**：减少运维复杂度

### 1.2 运维目标
- 确保系统稳定运行
- 数据安全和备份
- 性能监控和优化
- 故障快速恢复

## 2. 日常运维

### 2.1 系统启动和停止

**启动系统**
```bash
# 激活虚拟环境
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 启动应用
python main.py --mode daemon

# 或指定配置文件
python main.py --config custom_config.yaml
```

**停止系统**
```bash
# 优雅停止
python main.py --stop

# 或使用进程信号
kill -TERM <pid>

# 强制停止（不推荐）
kill -KILL <pid>
```

**重启系统**
```bash
python main.py --restart
```

### 2.2 状态检查

**系统健康检查**
```bash
# 检查系统状态
python main.py --health

# 检查数据库连接
python main.py --check-db

# 检查API连接
python main.py --check-api
```

**性能监控**
```bash
# 查看系统资源使用
python main.py --stats

# 查看最近的信号统计
python main.py --signal-stats --days 7

# 查看交易统计
python main.py --trade-stats --days 30
```

### 2.3 日志管理

**查看日志**
```bash
# 查看实时日志
tail -f logs/trading_assistant.log

# 查看错误日志
grep "ERROR" logs/trading_assistant.log

# 查看最近24小时日志
grep "$(date +'%Y-%m-%d')" logs/trading_assistant.log
```

**日志轮转**
```bash
# 压缩旧日志（每月执行）
cd logs
gzip trading_assistant.log.1
gzip trading_assistant.log.2

# 清理超过30天的日志
find logs/ -name "*.gz" -mtime +30 -delete
```

## 3. 数据备份和恢复

### 3.1 数据备份策略

**每日自动备份**
```bash
#!/bin/bash
# scripts/backup_daily.sh
DATE=$(date +%Y%m%d)
BACKUP_DIR="backups/daily"

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据库
cp data/trading_assistant.db $BACKUP_DIR/trading_assistant_$DATE.db

# 备份配置文件
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# 保留最近7天的备份
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup completed: $DATE"
```

**每周完整备份**
```bash
#!/bin/bash
# scripts/backup_weekly.sh
DATE=$(date +%Y%m%d)
BACKUP_DIR="backups/weekly"

mkdir -p $BACKUP_DIR

# 备份整个数据目录
tar -czf $BACKUP_DIR/full_backup_$DATE.tar.gz data/ config/ logs/

# 保留最近4周的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +28 -delete

echo "Weekly backup completed: $DATE"
```

### 3.2 数据恢复

**恢复数据库**
```bash
# 停止系统
python main.py --stop

# 恢复数据库文件
cp backups/daily/trading_assistant_20231201.db data/trading_assistant.db

# 重启系统
python main.py --restart
```

**恢复配置文件**
```bash
# 备份当前配置
cp -r config config_backup_$(date +%Y%m%d)

# 恢复配置
tar -xzf backups/daily/config_20231201.tar.gz

# 验证配置
python main.py --validate-config
```

## 4. 性能优化

### 4.1 性能监控指标

**关键性能指标**
- 单股票分析响应时间：< 2秒
- 内存使用：< 500MB
- 数据库查询时间：< 100ms
- API调用成功率：> 99%

**性能监控脚本**
```python
# scripts/performance_monitor.py
import psutil
import time
import sqlite3

def monitor_performance():
    # CPU使用率
    cpu_percent = psutil.cpu_percent(interval=1)
    
    # 内存使用
    memory = psutil.virtual_memory()
    
    # 磁盘IO
    disk_io = psutil.disk_io_counters()
    
    print(f"CPU: {cpu_percent}%")
    print(f"Memory: {memory.percent}%")
    print(f"Available Memory: {memory.available / 1024 / 1024:.1f} MB")
```

### 4.2 性能优化建议

**数据库优化**
```sql
-- 为常用查询添加索引
CREATE INDEX idx_signals_timestamp ON signals(timestamp);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- 定期清理旧数据
DELETE FROM signals WHERE timestamp < date('now', '-90 days');
```

**缓存优化**
```python
# 价格数据缓存时间调整
PRICE_CACHE_TTL = 60  # 1分钟缓存

# 技术指标缓存
INDICATOR_CACHE_TTL = 300  # 5分钟缓存
```

## 5. 故障处理

### 5.1 常见故障及解决方案

**1. 数据源连接失败**
```bash
# 症状：获取价格数据失败
# 解决：检查网络连接和API配额

# 检查API状态
python main.py --check-api

# 切换备用数据源
export BACKUP_DATA_SOURCE=true
python main.py --restart
```

**2. 数据库锁定**
```bash
# 症状：数据库操作超时
# 解决：检查数据库连接

# 检查数据库状态
sqlite3 data/trading_assistant.db ".timeout 10000" ".tables"

# 修复数据库
sqlite3 data/trading_assistant.db "VACUUM;"
```

**3. 内存泄漏**
```bash
# 症状：内存使用持续增长
# 解决：重启应用和调试

# 监控内存使用
python scripts/performance_monitor.py

# 强制垃圾回收
python main.py --gc

# 重启应用
python main.py --restart
```

### 5.2 故障恢复流程

**故障恢复SOP**
1. **识别故障**：检查日志和系统状态
2. **评估影响**：确定故障影响范围
3. **临时措施**：快速恢复服务
4. **根因分析**：查找故障原因
5. **永久修复**：实施解决方案
6. **验证修复**：确认问题解决
7. **文档更新**：更新运维文档

## 6. 安全管理

### 6.1 API密钥管理

**密钥轮换**
```bash
# 更新API密钥
echo "ALPHA_VANTAGE_API_KEY=new_key" >> .env

# 验证新密钥
python main.py --check-api

# 删除旧密钥记录
sed -i '/old_key/d' .env
```

### 6.2 数据安全

**敏感数据处理**
- API密钥存储在环境变量中
- 数据库文件权限设置为600
- 备份文件加密存储
- 定期检查配置文件权限

**权限设置**
```bash
# 设置文件权限
chmod 600 .env
chmod 600 data/trading_assistant.db
chmod 700 backups/
```

## 7. 升级和维护

### 7.1 版本升级流程

**升级前准备**
```bash
# 1. 创建完整备份
./scripts/backup_weekly.sh

# 2. 验证当前版本
python main.py --version

# 3. 停止服务
python main.py --stop
```

**升级过程**
```bash
# 4. 更新代码
git pull origin main

# 5. 更新依赖
pip install -r requirements.txt

# 6. 运行迁移脚本（如有）
python scripts/migrate.py

# 7. 验证配置
python main.py --validate-config

# 8. 启动服务
python main.py --start
```

**升级后验证**
```bash
# 9. 健康检查
python main.py --health

# 10. 功能测试
python main.py --test

# 11. 监控运行状态
tail -f logs/trading_assistant.log
```

### 7.2 回滚方案

**快速回滚**
```bash
# 停止服务
python main.py --stop

# 回滚代码
git checkout <previous_version>

# 恢复数据库
cp backups/daily/trading_assistant_backup.db data/trading_assistant.db

# 启动服务
python main.py --start
```

## 8. 监控和告警

### 8.1 监控脚本

**系统监控**
```bash
#!/bin/bash
# scripts/health_check.sh

# 检查进程状态
if pgrep -f "main.py" > /dev/null; then
    echo "Service is running"
else
    echo "Service is down - attempting restart"
    python main.py --start
fi

# 检查磁盘空间
DISK_USAGE=$(df -h | grep "/$" | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 90 ]; then
    echo "Warning: Disk usage is $DISK_USAGE%"
fi

# 检查内存使用
MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
echo "Memory usage: $MEMORY_USAGE%"
```

### 8.2 定时任务

**Crontab设置**
```bash
# 编辑定时任务
crontab -e

# 添加以下任务：
# 每5分钟健康检查
*/5 * * * * /path/to/scripts/health_check.sh

# 每日凌晨备份
0 2 * * * /path/to/scripts/backup_daily.sh

# 每周日完整备份
0 1 * * 0 /path/to/scripts/backup_weekly.sh

# 每月清理日志
0 3 1 * * find /path/to/logs -name "*.log.*" -mtime +30 -delete
```

## 9. 运维最佳实践

### 9.1 日常运维检查清单

**每日检查**
- [ ] 系统运行状态
- [ ] 错误日志检查
- [ ] 数据备份状态
- [ ] API调用状态
- [ ] 磁盘空间检查

**每周检查**
- [ ] 性能指标审查
- [ ] 完整备份验证
- [ ] 配置文件检查
- [ ] 安全更新检查

**每月检查**
- [ ] 日志清理
- [ ] 数据库优化
- [ ] 依赖更新检查
- [ ] 运维文档更新

### 9.2 文档维护

**运维日志**
- 记录所有运维操作
- 故障处理记录
- 性能优化记录
- 配置变更记录

**知识库更新**
- 新故障解决方案
- 性能优化经验
- 最佳实践总结
- 常见问题FAQ

---
