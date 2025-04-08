import logging
import sys

logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(name)s - %(message)s")

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# # Обработчик для записи в файл (лог-файл создается в папке logs)
# log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
# os.makedirs(log_dir, exist_ok=True)
# file_handler = logging.FileHandler(os.path.join(log_dir, "app.log"))
# file_handler.setFormatter(formatter)
# logger.addHandler(file_handler)
