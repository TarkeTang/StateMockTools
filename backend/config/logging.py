import os
import logging
from logging.handlers import RotatingFileHandler
from config.settings import settings


def setup_logging():
    """设置日志系统"""
    # 创建logs目录
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # 日志文件路径
    log_file = os.path.join(log_dir, settings.LOG_FILE)
    
    # 日志格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(filename)s:%(lineno)d | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 配置根日志
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    
    # 清除现有处理器
    for handler in root_logger.handlers:
        root_logger.removeHandler(handler)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    console_formatter = logging.Formatter(log_format, date_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器（带轮转）
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,  # 保留5个备份
        encoding="utf-8"
    )
    file_handler.setLevel(getattr(logging, settings.LOG_LEVEL))
    file_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler)
    
    # 配置uvicorn日志
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    for handler in uvicorn_logger.handlers:
        uvicorn_logger.removeHandler(handler)
    uvicorn_logger.addHandler(console_handler)
    uvicorn_logger.addHandler(file_handler)
    
    # 配置uvicorn.access日志
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    uvicorn_access_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    for handler in uvicorn_access_logger.handlers:
        uvicorn_access_logger.removeHandler(handler)
    uvicorn_access_logger.addHandler(console_handler)
    uvicorn_access_logger.addHandler(file_handler)
    
    # 配置fastapi日志
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(getattr(logging, settings.LOG_LEVEL))
    for handler in fastapi_logger.handlers:
        fastapi_logger.removeHandler(handler)
    fastapi_logger.addHandler(console_handler)
    fastapi_logger.addHandler(file_handler)
    
    return root_logger


# 创建日志实例
logger = setup_logging()
