import logging
import os
from datetime import datetime, timedelta
import hashlib
import hmac
import time
import base64
from functools import wraps

# 默认配置
DEFAULT_MODEL = "deepseek-chat"
SUPPORTED_MODELS = {
    "deepseek-chat": "DeepSeek Chat",
}

def setup_logger():
    """设置日志记录器"""
    # 创建logs目录
    os.makedirs('logs', exist_ok=True)
    
    # 获取当前日期作为日志文件名
    log_file = os.path.join('logs', f"{time.strftime('%Y-%m-%d')}.log")
    
    # 配置日志记录器
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def is_original_repo():
    """检查是否为原始仓库"""
    try:
        repo = os.getenv('GITHUB_REPOSITORY', '')
        return repo == '2404589803/hf-daily-paper-newsletter-chinese'
    except:
        return False

def validate_api_key(api_key):
    """验证API Key是否有效"""
    if not api_key or len(api_key) < 32:  # 简单的长度检查
        return False
    return True

def get_model_name():
    """获取要使用的模型名称"""
    return DEFAULT_MODEL  # 直接返回默认模型

def require_auth(func):
    """验证装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_key = os.getenv('DEEPSEEK_API_KEY')
        if not api_key:
            raise ValueError("未设置 DEEPSEEK_API_KEY 环境变量。如果这是一个fork的仓库，请在仓库的Settings->Secrets->Actions中设置您自己的DEEPSEEK_API_KEY。")
        
        # 验证API Key
        if not validate_api_key(api_key):
            raise ValueError("无效的 API Key 格式")
        
        # 如果是原始仓库，直接允许访问
        if is_original_repo():
            return func(*args, **kwargs)
        
        # 如果是fork的仓库，确保使用的是自己的API Key
        if api_key.startswith('sk-'):  # 假设这是一个新的API Key
            return func(*args, **kwargs)
        else:
            raise ValueError("Fork仓库必须使用自己的API Key。请在仓库的Settings->Secrets->Actions中设置您自己的DEEPSEEK_API_KEY。")
        
    return wrapper

def get_logger():
    """获取日志记录器"""
    return logging.getLogger('HF-daily-paper')


def get_last_week_range(reference_date=None, tz_name='Asia/Shanghai'):
    """
    计算「上周一」至「上周日」的日期范围（含首尾）。
    以 reference_date 所在周的周一为基准；未指定时使用北京时间当天。
    """
    import pytz

    tz = pytz.timezone(tz_name)
    if reference_date is None:
        today = datetime.now(tz).date()
    elif isinstance(reference_date, str):
        today = datetime.strptime(reference_date, '%Y-%m-%d').date()
    else:
        today = reference_date

    this_monday = today - timedelta(days=today.weekday())
    last_monday = this_monday - timedelta(days=7)
    last_sunday = this_monday - timedelta(days=1)
    return last_monday.strftime('%Y-%m-%d'), last_sunday.strftime('%Y-%m-%d')


def weekly_basename(start_date, end_date):
    """生成周报文件基名，例如 2026-05-26_to_2026-06-01"""
    return f"{start_date}_to_{end_date}"


def iter_date_range(start_date, end_date):
    """遍历 [start_date, end_date] 内的每一天（YYYY-MM-DD 字符串）。"""
    current = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    while current <= end:
        yield current.strftime('%Y-%m-%d')
        current += timedelta(days=1) 