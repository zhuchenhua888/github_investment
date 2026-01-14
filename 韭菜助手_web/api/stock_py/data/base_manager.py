import os
import time
from datetime import datetime, timedelta

class BaseDataManager:
    def __init__(self):
        self.data = []
        # 使用绝对路径，确保在不同目录下运行都能正确找到缓存
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.cache_dir = os.path.join(base_dir, 'cache')
        self.last_update_time = 0
        self.update_interval = 3600 * 24  # 默认24小时更新一次
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def should_update(self) -> bool:
        """检查是否需要更新数据"""
        # 如果 last_update_time 是 0，说明还没初始化或者没有缓存文件，需要更新
        if self.last_update_time == 0:
            return True
        return (time.time() - self.last_update_time) > self.update_interval

    def update_last_update_time(self, cache_file: str):
        """从缓存文件更新最后更新时间"""
        if os.path.exists(cache_file):
            self.last_update_time = os.path.getmtime(cache_file)

    def format_date(self, date_obj: datetime) -> str:
        return date_obj.strftime('%Y-%m-%d')
    def get_yesterday_date(self) -> datetime:
        return datetime.now() - timedelta(days=1)
    def add_days(self, date_str: str, n: int) -> str:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        new_date = date_obj + timedelta(days=n)
        return self.format_date(new_date)
