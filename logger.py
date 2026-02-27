# logger.py

import logging


# Trades logger
trade_logger = logging.getLogger("trades")
trade_logger.setLevel(logging.INFO)
trade_logger.addHandler(logging.FileHandler("trades.log"))

# Error logger
error_logger = logging.getLogger("errors")
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(logging.FileHandler("errors.log"))

# Monitor logger
monitor_logger = logging.getLogger("monitor")
monitor_logger.setLevel(logging.INFO)
monitor_logger.addHandler(logging.FileHandler("monitor.log"))

# Format for all
formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
for logger in [trade_logger, error_logger, monitor_logger]:
    for handler in logger.handlers:
        handler.setFormatter(formatter)


def log(message, type="monitor"):
    print(message)
    if type == "trade":
        trade_logger.info(message)
    elif type == "error":
        error_logger.error(message)
    else:
        monitor_logger.info(message)