"""
Logging Configuration — CyberTrace AI
"""
import sys
import logging
from app.core.config import settings

try:
    from loguru import logger
    HAS_LOGURU = True
except ImportError:
    HAS_LOGURU = False
    logger = logging.getLogger("cybertrace")


def setup_logging():
    """Configure application logging with loguru or standard logging fallback."""
    if HAS_LOGURU:
        # Remove default handler
        logger.remove()

        # Console handler
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="DEBUG" if settings.DEBUG else "INFO",
            colorize=True,
        )

        # File handler
        logger.add(
            "logs/cybertrace_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level="INFO",
        )

        # Intercept standard logging
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                try:
                    level = logger.level(record.levelname).name
                except ValueError:
                    level = record.levelno
                frame, depth = sys._getframe(6), 6
                while frame.f_code.co_filename == logging.__file__:
                    frame = frame.f_back
                    depth += 1
                logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())

        logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
        logger.info(f"Logging initialized | env={settings.APP_ENV} | debug={settings.DEBUG}")
    else:
        log_level = logging.DEBUG if settings.DEBUG else logging.INFO
        logging.basicConfig(
            level=log_level,
            format="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)]
        )
        logger.info(f"Standard logging initialized | env={settings.APP_ENV} | debug={settings.DEBUG}")

