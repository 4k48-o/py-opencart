"""
Configuration management for OpenCart FastAPI application
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# 加载 .env 文件
# 优先加载 python/.env，如果没有则加载项目根目录的 .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    # 尝试加载项目根目录的 .env 文件
    root_env_path = Path(__file__).parent.parent.parent / ".env"
    if root_env_path.exists():
        load_dotenv(root_env_path, override=True)
    
    # 如果都没有，尝试加载 .env.test（用于开发环境）
    test_env_path = Path(__file__).parent.parent / ".env.test"
    if test_env_path.exists():
        load_dotenv(test_env_path, override=True)


class Settings:
    """Application settings"""
    
    # Database settings
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "3306"))
    db_user: str = os.getenv("DB_USER", "root")
    db_password: str = os.getenv("DB_PASSWORD", "")
    db_name: str = os.getenv("DB_NAME", "opencart")
    db_prefix: str = os.getenv("DB_PREFIX", "oc_")
    
    # Application settings
    app_name: str = "OpenCart API"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Security settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-minimum-32-characters")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
    refresh_token_expire_days: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # Redis settings
    redis_host: str = os.getenv("REDIS_HOST", "localhost")
    redis_port: int = int(os.getenv("REDIS_PORT", "6379"))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD", None)
    redis_db: int = int(os.getenv("REDIS_DB", "0"))
    redis_decode_responses: bool = True
    
    def __init__(self):
        """Initialize settings from environment variables"""
        # Database settings
        self.db_host = os.getenv("DB_HOST", "localhost")
        self.db_port = int(os.getenv("DB_PORT", "3306"))
        self.db_user = os.getenv("DB_USER", "root")
        self.db_password = os.getenv("DB_PASSWORD", "")
        self.db_name = os.getenv("DB_NAME", "opencart")
        self.db_prefix = os.getenv("DB_PREFIX", "oc_")
        
        # Application settings
        self.app_name = "OpenCart API"
        self.app_version = "1.0.0"
        self.debug = os.getenv("DEBUG", "False").lower() == "true"
        
        # Security settings
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production-minimum-32-characters")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Redis settings
        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD", None)
        self.redis_db = int(os.getenv("REDIS_DB", "0"))
        self.redis_decode_responses = True


settings = Settings()

