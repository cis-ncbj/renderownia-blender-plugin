# protocol = 'http'
# server = 'https://httpbin.org/post'

import logging
import logging.handlers
import tempfile
import os

# USER SETTINGS
log_level = logging.DEBUG
# END

formatter = logging.Formatter("== %(levelname)7s %(asctime)s [%(filename)s:%(lineno)s - %(funcName)s()] :\n%(message)s")

enviroment = 'production'
log_file = os.path.join(tempfile.gettempdir(), "renderownia.log")
logger = logging.getLogger(enviroment)

logger.handlers[:] = []

logger.setLevel(log_level)
ch = logging.handlers.RotatingFileHandler(log_file, maxBytes=52428800, backupCount=2)
ch.setFormatter(formatter)
ch.setLevel(log_level)
logger.addHandler(ch)


server = 'http://localhost:5000/job'
