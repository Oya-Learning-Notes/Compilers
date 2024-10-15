import sys
from loguru import logger, _defaults
from os import environ

from cfg.grammar_type import run_example_cases

logger.remove()
fmt = (
    # "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    # "<cyan>{name}</cyan>:"
    "<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
)

logger.add(sys.stderr, format=fmt, level="DEBUG")


run_example_cases()

logger.success("All cases executed")
