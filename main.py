
import re
import logging
from datetime import datetime
import json
import base64
import sys
import os
import re

from fake_useragent import UserAgent
import yaml
import requests
import schedule

from spiderexcep import *
from spiderlog import init_log,box_alert

MANUAL_CAPTCHA = False
INTERVAL = 300
MAX_RETRY_TIMES = 3

FORMAT_OUTPUT = \
"""
{lec_name}({lec_id}): {location}
{start_time} ~ {end_time}
{status}
quick_href: https://v.ruc.edu.cn//campus#/activity/partakedetail/{lec_id}/description

"""

pattern = re.compile(r'[a-zA-Z]{4}')


def request_response(is_json: bool           = True,
                    method  : str            = 'GET',
                    logger  : logging.Logger = None,
                    encoding: str            = 'utf-8',
                    verbose : bool           = True,
                    *args, **kwargs): 
    """
    Pack the request and do the error handling.

    Args:
        is_json (bool, optional): whether the result is an json or not. Defaults to True.
        method (str, optional): to use 'GET' method of 'POST' method. Defaults to 'GET'.
        logger (logging.Logger): the way to record error, if any.
        encoding (str): the encoding method.

    Raises:
        AbortException: Abort the program immediately.
        HoldException:  Skip this request and wait until next time.
        RetryException: Retry to connect.

    Returns:
        Dict|str: the results based on the is_json parameter.
    """
    
    arg = locals()
    
    response = None
    
    try:
        if method == 'GET':
            response = requests.get(timeout = 5, *args, **kwargs)
        elif method == 'POST':
            response = requests.post(timeout = 5, *args, **kwargs)
        else:
            raise ValueError("The method should be 'GET' or 'POST'.")
        
        response.encoding = encoding
    
        if is_json == True:
            return response.json()
        else:
            return response.text
    # 遭遇网络异常错误: 网络连接不通。
    except requests.exceptions.ConnectionError as e:
        if logger != None and verbose:
            logger.warning("CONNECTION: The connection is down.")
            logger.warning("Error Value {}".format(e))
        raise HoldException(str(e))

    # 响应时间过长。
    except requests.exceptions.Timeout as e:
        if logger != None and verbose:
            logger.warning("TIMEOUT: the connection took long.")
            logger.warning("Error value: {}".format(e))
        raise RetryException(str(e))
    
    except requests.exceptions.HTTPError as e:
        if logger != None and verbose:
            logger.warning("HTTPERROR: Request HTTP error. Error Code {}".format(response.status_code))
            logger.warning("Error value: {}".format(e))
        raise RetryException(str(e))
            
    except requests.exceptions.RequestException as e:
        if logger != None and verbose:
            logger.warning("Error value: {}".format(e))
        raise RetryException(str(e))
    
    except Exception as e:
        if logger != None and verbose:
            logger.warning("Unknown error. Error value: {}".format(e))
        
        raise HoldException(str(e))


class RUCSpider(object):
    def __init__(self,
                setting_file    : str  = "./setting.yml",
                window_alert    : bool = False,
                window_icon     : str  = "RUCWeb.ico",
                cookie_retrieve = None): 
        """
        The initialization of the class.

        Args:
            setting_file (str, optional): the file to restore the settings. Defaults to "./setting.yml".
            
        class Args:
        ua (fake_useragent.UserAgent): to give random headers.
        setting_file (str)           : the yaml file storing the settings.
        logger (logging.Logger)      : put some information on the screen.
        timestamp (float)            : record the timestamp of now.
        DELTA_TIME (int)             : the max time span that one cookie can live,
        infos (Dict)                 : the information in/retreived from the setting yaml file.
        """
        self.ua = UserAgent()
        self.setting_file = setting_file
        
        self.window_alert = window_alert
        
        if os.path.exists(window_icon):
            self.icon_path = window_icon
        else:
            self.icon_path = None
        
        self.logger = init_log('<RUCSpider>')
        
        self.timestamp = datetime.now().timestamp()
        self.DELTA_TIME = 18000
        self.manuals = False
        self.captcha_func = cookie_retrieve
        
        self.infos = self.CheckSettings()
        
        # 清空原本的 logger.
        with open("log.log","w",encoding='utf-8') as f:
            f.write("")
        
    
    def update(self):
        """
        Update current time, and retrieve cookie is needed.
        """
        self.timestamp = datetime.now().timestamp()
        self.infos = self.CheckSettings()
        self.logger.info("Data Updated.")
    
    def CheckSettings(self):
        """
        There are several settings to fill.
        username & password  : [MUST] fill in.
        token                : pull html to get one.
        cookies & expire_time: within login to get.
        interval_seconds     : default to 300 (5 minutes)
        Args:
            None
        
        Returns:
            Dict: a seemingly complete information table.
        
        Raises:
            ValueError: If the user didn't fill his username or password.
        """
        Update = False
        
        with open(self.setting_file, "r", encoding = 'utf-8') as f:
            info = yaml.load(f, Loader=yaml.FullLoader)
        
        if info['username'] == None:
            self.logger.critical('username is empty, please fill in your id in your setting file!')
            sys.exit(0)
            
        if info["password"] == None:
            self.logger.critical('password is empty, please fill in your password in your setting file!')
            sys.exit(0)

        if info["token"] == None:
            self.logger.info('Token empty, pulling html to get one token.')
            info["token"] = self._GetToken_()
            Update = True
            
        if info["cookies"] == None or info["expire_time"] == None or len(info["cookies"]) == 0:
            self.logger.info('Cookie Empty, trying to login to gain a cookie')
            info["cookies"], info["expire_time"] = self._GetCookie_(info,func = self.captcha_func)
            Update = True
            
        if self.timestamp > info["expire_time"]:
            self.logger.info('Cookie Expired, trying to login to gain a new cookie')
            info["cookies"], info["expire_time"] = self._GetCookie_(info,func = self.captcha_func)
            Update = True
            
        for k,v in info["cookies"].items():
            if v == None:
                self.logger.info('Cookie incomplete, trying to login to gain a cookie')
                info["cookies"], info["expire_time"] = self._GetCookie_(info,func = self.captcha_func)
                Update = True
                break
            
        self.manuals = info["manual"]
            
        if info["interval_seconds"] == None:
            self.logger.info('Interval Empty, setting to default value(300)')
            info["interval_seconds"] = 300
        else:
            global INTERVAL
            INTERVAL = info["interval_seconds"]
            Update = True
            
        if Update:
            self.logger.info("Updating information.")
            with open(self.setting_file, "w", encoding = 'utf-8') as f:
                yaml.dump(info, f)
            
        return info
    
    def _GetToken_ (self):
        """
        Get the one usable token.

        Returns:
            str: one usable token.
        """
        url = r"https://v.ruc.edu.cn/auth/login?&proxy=true&redirect_uri=https://v.ruc.edu.cn/oauth2/authorize?client_id=accounts.tiup.cn&redirect_uri=https://v.ruc.edu.cn/sso/callback?school_code=ruc&theme=schools&response_type=code&school_code=ruc&scope=all&state=jnTBbsfBumjuSrfZ&theme=schools&school_code=ruc"
        
        headers = {'user-Agent': self.ua.random}
        res_html = None
        
        try:
            res_html = request_response(is_json = False, method = 'GET', logger = self.logger, url = url,headers = headers)
        except (AbortException,HoldException) as e:
            self.logger.warning(str(e))
            exit(0)
        except RetryException as e:
            self.logger.debug("Token Retrive fail. Retrying.")
            
            for index in range(MAX_RETRY_TIMES):
                try:
                    res_html = request_response(is_json = False, method = 'GET', logger = self.logger, url = url,headers = headers, verbose= False)
                    break
                except:
                    self.logger.info("Retry No.{} Finished.".format(index + 1))
                    time.sleep(3)
                    continue
            
            if res_html == None:
                # raise AbortException("Token Retrive fail. Retry times exceed the limit.")
                self.logger.critical("Token Retrive fail. Retry times exceed the limit.")
                sys.exit(0)
        
        regex = re.compile(r'(?<=<input type="hidden" name="csrftoken" value=")([\S]+)(?=" id="csrftoken" \/>)')
        token = re.search(regex,res_html)[0]
        
        return token
    
    def _GetCookie_(self,info:dict,func = None):
        """
        Get the cookie by log in.
        Log in itself is not of a worth.
        
        Args:
            info: Dict[str:str] containing needed login information.

        Returns:
            Dict: the cookie dict.
            float: The expire timestamp.
        """
        from utils import GetCode,OCRCODE
        
        tgt_url = r"https://v.ruc.edu.cn/auth/login"
        params = {
        "username"          : "ruc:{id}",
        "password"          : "{pwd}",
        "code"              : "",
        "remember_me"       : "false",
        "redirect_url"      : "/",
        "twofactor_password": "",
        "twofactor_recovery": "",
        "token"             : "{token}",
        "captcha_id"        : ""}
        
        headers = {'user-Agent': self.ua.random}
        
        params["username"] = params["username"].format(id = info["username"])
        params["password"] = params["password"].format(pwd = info["password"])
        params["token"] = params["token"].format(token = info["token"])
        
        def Retrieve_captcha():
            captcha_url = r"https://v.ruc.edu.cn/auth/captcha"
            
            headers = {'user-Agent': self.ua.random}
            
            captcha_info = None
            
            try:
                captcha_info = request_response(logger = self.logger, url = captcha_url,headers = headers)
            except (HoldException,AbortException) as e:
                self.logger.error("Aborion with {}".format(str(e)))
                exit(0)
            except RetryException as e:
                self.logger.warning("Cookie retrieve fail. Retrying.")
                for index in range(MAX_RETRY_TIMES):
                    try:
                        captcha_info = request_response(logger = self.logger, url = captcha_url,headers = headers, verbose= False)
                        break
                    except:
                        self.logger.info("Retry No.{} Finished.".format(index + 1))
                        time.sleep(3)
                        continue
                    
                if captcha_info == None:
                    # raise AbortException("Cookie retrieve fail. Retry times exceed the limit.")
                    self.logger.critical("Cookie retrieve fail. Retry times exceed the limit.")
                    sys.exit(0)
            
            except Exception as e:
                self.logger.error("Aborion with {}".format(str(e)))
                exit(0)
            
            pattern = re.compile(r"(?<=data:image\/png;base64,)([\S]+)")
    
            b64_img = re.search(pattern,captcha_info["b64s"])[0]
            captcha_id = captcha_info["id"]
            
            if self.manuals:
                captcha_text = GetCode(b64_img)
                
            else:
                if func != None:
                    captcha_text = func(b64_img)
                else:
                    captcha_text = OCRCODE(b64_img)
            
            return captcha_text,captcha_id,bytes(b64_img,encoding="utf-8")
            
        code,id,img = Retrieve_captcha()
        while not re.match(r"[a-zA-Z0-9]{4}",code):
            self.logger.info("Captcha predict trival error. Try again.")
            code,id,img = Retrieve_captcha()
        params["captcha_id"] = id
        params["code"] = code
        
        session = requests.Session()
        cookie = None
        try:
            session.post(url = tgt_url, headers=headers, json = params)
            cookie = session.cookies.get_dict()
        except:
            # raise AbortException("Unable to keep a session.")
            self.logger.critical("Unable to keep a session.")
            sys.exit(0)
        
        if len(cookie) == 0:
            self.logger.critical("Unexpected error. Check username, password and captcha in 'error.txt' to ensure the login process is correct.")
            
            with open('error.txt','w',encoding='utf-8') as f:
                f.write("username:{}\n".format(params["username"][4:]))
                f.write("password:{}\n".format(params["password"]))
                f.write("code    :{}\n".format(params["code"]))
                
            imgdata = base64.b64decode(img)
            
            # remove any remaining png (if any)
            pngs = [fig for fig in os.listdir() if fig.endswith(".png")]
            for png in pngs:
                os.remove(png)
            
            with open("{}.png".format(params["captcha_id"]),"wb") as f:
                f.write(imgdata)
                
            sys.exit(0)

        return cookie,self.timestamp + self.DELTA_TIME
    
    def PullLecture(self, maxlen:int = 30,Condition:list = None, Query:str = "", filter = lambda x: True):
        """
        Pull the satisfied lecture.

        _extended_summary_

        Args:
            maxlen (int, optional): program will extract so many lectures. Defaults to 30.
            ? Condition (list[List[int]]]): the condition list, each condition is one list containing 3 options. Defaults to None.
            Condition (list[int]) the condition of three options. defaults to None
            Query (str, optional): the query text. Defaults to "".
            filter (Callable, optional): the function to do a detailed filter. Defaults to (SELECT ALL)

        Raises:
            AbortException: _description_
        """
        tgt_url = r"https://v.ruc.edu.cn/campus/v2/search"
        SAVE_FILES = "./res.json"
        
        with open("alias.json","r",encoding='utf-8') as f:
            mapping = json.load(f)
        
        params = {
        "perpage"      : maxlen,
        "page"         : 1,
        "typelevel1"   : mapping[Condition[0]],
        "typelevel2"   : mapping[Condition[1]],
        "typelevel3"   : mapping[Condition[2]],
        "applyscore"   : 0,
        "begintime"    : "",
        "location"     : "",
        "progress"     : 0,
        "owneruid"     : "",
        "sponsordeptid": "",
        "query"        : Query,
        "canregist"    : 0}
        
        headers = {'User-Agent': self.ua.random}
        
        new_lectures = []
        new_id = []
        response = None
            
        try:
            response = request_response(method='POST',logger = self.logger, url = tgt_url,headers = headers,json = params,cookies = self.infos["cookies"])
        except HoldException as e:
            self.logger.info("Holding pulling.")
            return
        
        except RetryException as e:
            # self.logger.debug("Detecting error as {}. Reloading cookies.".format(e))
            now_timestap = datetime.now().timestamp()
            if now_timestap > self.infos["expire_time"]:
                self.logger.info("Cookies expired. Reloading cookies.")
                self.update()
                #self._GetCookie_(self.infos,self.captcha_func)
            else:
                self.logger.info("Detecting error as e {}, Retry for {} times".format(str(e), MAX_RETRY_TIMES))
            for index in range(MAX_RETRY_TIMES):
                try:
                    response = request_response(method='POST',logger = self.logger, url = tgt_url,headers = headers,json = params,cookies = self.infos["cookies"],verbose=False)
                    break
                except:
                    self.logger.info("Retry No.{} Finished.".format(index + 1))
                    time.sleep(3)
                    continue
            
            if response == None:
                # raise HoldException("Can't reach lecture after reloading cookies. Retry times exceed the limit.")
                self.logger.warning("Can't reach lecture after reloading cookies. Retry times exceed the limit. This turn is skipped.")
                return
            
        except Exception as e:
            self.logger.warning(str(e))
            self.logger.info("Reloading cookies and try once.")
            self.update()
            #self._GetCookie_(self.infos,self.captcha_func)
            response = request_response(method='POST',logger = self.logger, url = tgt_url,headers = headers,json = params,cookies = self.infos["cookies"])
        
        if response == None: # skip this turn.
            self.logger.info("receive empty response, this turn is skipped. Check logger to locate the issue.")
            return
        
        results = response["data"]["data"]
        
        if os.path.exists(SAVE_FILES):
            with open(SAVE_FILES,"r",encoding = 'utf-8') as f:
                saves = json.load(f)
                
        else:
            saves = []
        
        if saves == []:
            saves = [res["aid"] for res in results]
            self.logger.debug("Empty result storage filled.")

        else:
            for lec in results:
                if lec["aid"] not in saves:
                    self.logger.warning("New lecture found!")
                    saves.append(lec["aid"])
                    new_lectures.append(lec)
        
        with open(SAVE_FILES,"w",encoding = 'utf-8') as f:
            json.dump(saves,f,ensure_ascii=False,separators=(',', ':'),indent = 4)
        
        new_id = [lec["aid"] for lec in new_lectures if filter(lec)]

        if len(new_id) != 0:
            self.logger.info("Trying register new lectures {}.".format(str(new_id)))
            outcome = self.register(new_id)
            with open("log.txt","a",encoding='utf-8') as f:
                for lec in new_lectures:
                    
                    result = FORMAT_OUTPUT.format(\
                        lec_name   = lec["aname"], 
                        lec_id     = lec["aid"], 
                        location   = lec["location"], 
                        start_time = lec["begintime"], 
                        end_time   = lec["endtime"], 
                        status     = outcome[lec["aid"]])
                    f.write(result)
            
        self.logger.info("Check complete.")
    
    def register(self,aid:list):
        tgt_url = r"https://v.ruc.edu.cn/campus/Regist/regist"
        
        def sub_reg(id:int):
            params = {"aid":id}
            headers = {'User-Agent': self.ua.random}
            
            results = request_response(method = 'POST',logger = self.logger, url = tgt_url, headers = headers, json = params, cookies = self.infos["cookies"])
            
            return results["msg"]
        
        result = dict()
        
        for id in aid:
            res = sub_reg(id)
            self.logger.info("Register id {:>6d}: {}".format(id,res))
            result[id] = res
        
        success_lec = [id for id,res in result.items() if res == "报名成功"]
        if self.window_alert:
            box_alert(title="Notice",msg="Lecture {} successfully registered.".format(str(success_lec)),icon_path=self.icon_path)
        
        return result

    @classmethod
    def FilterLecture(self,lect:dict,schedule:list):
        """
        Default selection method to select the new lecture.
        
        We only consider that whether the lecture fits in the schedule.

        Args:
            lect (dict): the information of the lecture.
            schedule (List[List[str,str]]) the available time. From Monday to Sunday(0 - 6 respectively).
        """
        
        begin_time = datetime.strptime(lect["begintime"], "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(lect["endtime"], "%Y-%m-%d %H:%M:%S")
        
        time_day = datetime(begin_time.year,begin_time.month,begin_time.day)
        
        weekday = time_day.weekday()
        time_day = time_day.strftime("%Y-%m-%d")
        
        for time_span in schedule[weekday]:
            b_t = datetime.strptime(time_day + ' '+ time_span[0], "%Y-%m-%d %H:%M:%S")
            e_t = datetime.strptime(time_day + ' '+ time_span[1], "%Y-%m-%d %H:%M:%S")
            
            if b_t < begin_time and end_time < e_t:
                return True
            
        return False

def packed(schedule_list:list):
    
    def new_filter(lec:dict):
        return RUCSpider.FilterLecture(lec,schedule_list)
    
    return new_filter

def main():
    
    CONDITION = ["素质拓展认证","形势与政策","形势与政策讲座"]
    
    spider = RUCSpider(window_alert = True)
    with open("schedule.yml","r",encoding="utf-8") as f:
        timespan = yaml.load(f,Loader=yaml.FullLoader)
        
    spider.PullLecture(maxlen = 30, Condition = CONDITION ,filter = packed(timespan))

    filt = packed(timespan)

    schedule.every(INTERVAL).seconds.do(spider.PullLecture,maxlen = 30, Condition = CONDITION)
    schedule.every(30).minutes.do(spider.update)
    
    while True:
        schedule.run_pending()

if __name__ == "__main__":
    main()


