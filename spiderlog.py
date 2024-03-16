import logging
import colorlog

log_colors_config = {
    'DEBUG': 'white',
    'INFO': 'cyan',
    'WARNING': 'purple',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

default_formats = {
    'color_format': '%(log_color)s[%(asctime)s %(levelname)8s]<line:%(lineno)4d>:%(message)s',
    'log_format': '[%(asctime)s]<line:%(lineno)4d>:%(message)s'
}

def init_log(name:str):
    log_level = logging.DEBUG  # 日志级别
    log_file = 'log.log'  # 日志文件名
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # cmd handler
    consolehandler = logging.StreamHandler()
    consolehandler.setLevel(log_level)
    consoleformatter = colorlog.ColoredFormatter(
        fmt = default_formats['color_format'],
        datefmt = "%Y-%m-%d %H:%M:%S",
        log_colors = log_colors_config
    )
    
    # file handler
    filehandler = logging.FileHandler(log_file, encoding='utf-8',mode = 'a')
    filehandler.setLevel(log_level)
    fileformatter = logging.Formatter(
        fmt = default_formats['log_format'],
        datefmt = "%Y-%m-%d %H:%M:%S"
    )
    
    consolehandler.setFormatter(consoleformatter)
    filehandler.setFormatter(fileformatter)
    if not logger.handlers:
        logger.addHandler(consolehandler)
        logger.addHandler(filehandler)
    
    return logger

if __name__ == '__main__':
    logger = init_log('test')
    logger.warning('test warning')
    logger.info('signs')
