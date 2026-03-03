import logging
import os
import sys
from logging.handlers import RotatingFileHandler

from rich.console import Console
from rich.logging import RichHandler


console = Console()


def setup_logger(name="smartsort", log_level=logging.INFO, log_file="data/smartsort.log"):
    """
    Configura um logger estruturado com suporte a console (Rich) e ficheiro.
    """
    logger = logging.getLogger(name)
    logger.setLevel(log_level)


    if logger.handlers:
        return logger


    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
    )


    rich_handler = RichHandler(
        console=console,
        rich_tracebacks=True,
        markup=True,
        show_path=False,
    )
    rich_handler.setLevel(log_level)
    logger.addHandler(rich_handler)


    try:
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(logging.DEBUG)
        logger.addHandler(file_handler)
    except Exception as e:

        print(f"Aviso: Não foi possível configurar o ficheiro de log: {e}", file=sys.stderr)

    return logger



logger = setup_logger()
