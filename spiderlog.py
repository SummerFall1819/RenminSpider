import logging
import colorlog
import sys

import requests
from rich.logging import RichHandler
from plyer import notification

HTML_CONTENT_HEADER = \
r'''
<style>
h1 {
    align: center;
    
}

a {
    text-decoration: underline;
    color:red;
}
</style>

'''

HTML_CONTENT_ITEMS = \
'''
<ol>
<li> <a href = https://v.ruc.edu.cn//campus#/activity/partakedetail/{aid}/description target = "_blank">{aname}</a>
<li> 起止时间: {begintime} 至 {endtime}
<li> 活动地点: {location}
</ol>
'''

ICON_PATH = "./RUCWeb.ico"

NOTIFIER = dict()

def voidfunc(lectures):
    return

NOTIFIER["none"] = voidfunc

LOG_COLORS_CONFIG = {
    'DEBUG': 'white',
    'INFO': 'cyan',
    'WARNING': 'purple',
    'ERROR': 'red',
    'CRITICAL': 'bold_red',
}

DEFAULT_FORMATS = {
    'color_format': '%(log_color)s[%(asctime)s %(levelname)8s]<line:%(lineno)4d>:%(message)s',
    'log_format': '[%(asctime)s]<line:%(lineno)4d>:%(message)s',
    'rich_format': '[purple]%(message)s'
}

def init_log(name:str):
    log_level = logging.DEBUG  # 日志级别
    log_file = 'log.log'  # 日志文件名
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # cmd handler
    consolehandler = RichHandler(rich_tracebacks=True, markup=True)
    consolehandler.setLevel(log_level)
    consoleformatter = logging.Formatter(
        fmt = DEFAULT_FORMATS['rich_format'],
        datefmt = "%Y-%m-%d %H:%M:%S",
    )
    
    # consolehandler = logging.StreamHandler(sys.stdout)
    # consoleformatter = colorlog.ColoredFormatter(
    #     # fmt = default_formats['color_format'],
    #     datefmt = "%Y-%m-%d %H:%M:%S",
    #     # log_colors = log_colors_config
    # )
    
    # file handler
    filehandler = logging.FileHandler(log_file, encoding='utf-8',mode = 'a')
    filehandler.setLevel(log_level)
    fileformatter = logging.Formatter(
        fmt = DEFAULT_FORMATS['log_format'],
        datefmt = "%Y-%m-%d %H:%M:%S"
    )
    
    consolehandler.setFormatter(consoleformatter)
    filehandler.setFormatter(fileformatter)
    if not logger.handlers:
        logger.addHandler(consolehandler)
        logger.addHandler(filehandler)
    
    return logger

def box_alert(lectures:list, *args, **kwargs):
    notification.notify(title = "Notice", msg = "Lecture {} successfully registered.".format(str(lectures)),icon_path = ICON_PATH)
    
def box_alert_wrapped(*args, **kwargs):
    def alert(lectures:list):
        return box_alert(lectures = lectures)
    return alert

NOTIFIER["toast"] = box_alert_wrapped

def wx_notify(lectures:list, app_token:str,uid:list,logger):
    html = HTML_CONTENT_HEADER
    if len(lectures) == 1:
        html += "<h1>{aname}</h1>".format(lectures[0]["aname"])
    else:
        html += "<h1>新的 {} 场讲座</h1>".format(len(lectures))
    for lec in lectures:
        html += "\n" + HTML_CONTENT_ITEMS.format(**lec)
        
    res = requests.post(
        url = 'https://wxpusher.zjiecode.com/api/send/message',
        json = \
        {
            "appToken":app_token,
            "content":html,
            "summary":"会议报名成功提醒",
            "contentType":2,
            "uids":uid,
        }
    )
    # print(res,res.json(),res.text)
    if res.json()["success"]:
        logger.info("Message sent.")
    else:
        logger.critical(res.json()["code"],res.json()["msg"])
        
def init_wx_notify(apptoken, uid, logger, *args, **kwargs):
    def notify(lectures:list):
        return wx_notify(lectures = lectures,app_token = apptoken, uid = uid, logger = logger)
    
    return notify

NOTIFIER["wx"] = init_wx_notify

if __name__ == '__main__':
    logger = init_log('test')
    logger.warning('test warning')
    logger.info('signs')
    logger.critical("Critical Fail")
