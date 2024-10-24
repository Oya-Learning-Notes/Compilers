import sys
from loguru import logger, _defaults
from os import environ

from cfg.grammar_type import run_example_cases

# suppress default logger
logger.remove()

# custom logger format
# simplified for this program
fmt = (
    # "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level: <8}</level> | "
    # "<cyan>{name}</cyan>:"
    # "<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)

# add custom logger
logger.add(sys.stderr, format=fmt, level="DEBUG")

# set up file logger.
logger.add("./chomsky_type.log", format=fmt, level="DEBUG")

# run test cases
run_example_cases()

# success
logger.success("All cases executed")
