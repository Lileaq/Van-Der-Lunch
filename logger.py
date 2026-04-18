import logging


logger = logging.getLogger("SimpleLogger")
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(message)s"
)
file_handler = logging.FileHandler("api.log")
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)