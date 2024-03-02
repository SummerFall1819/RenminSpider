
import re
import logging
from datetime import datetime
import json
import base64
import sys
import os

from fake_useragent import UserAgent
import yaml
import requests
import schedule

from spiderexcep import *

MANUAL_CAPTCHA = False
INTERVAL = 300

def request_response(is_json        : bool           = True,
                    method          : str            = 'GET',
                    logger          : logging.Logger = None,
                    encoding        : str            = 'utf-8',
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
    
    try:
        if method == 'GET':
            response = requests.get(*args, **kwargs)
        elif method == 'POST':
            response = requests.post(*args, **kwargs)
        else:
            raise ValueError("The method should be 'GET' or 'POST'.")
        
        response.encoding = encoding
    
        if is_json == True:
            return response.json()
        else:
            return response.text()
    
    except requests.exceptions.ConnectionError as e:
        if logger != None:
            logger.warning("The connection is down.\n")
            logger.warning("Error Value {}".format(e))
        raise HoldException(str(e))

    except requests.exceptions.Timeout as e:
        if logger != None:
            logger.warning("The connection is timeout.\n")
            logger.warning("Error value: {}".format(e))
        raise RetryException(str(e),arg)
            
    except requests.exceptions.RequestException as e:
        if logger != None:
            logger.warning("Request failed. Error Code {}".format(response.status_code))
            logger.warning("Error value: {}".format(e))
        raise RetryException(str(e),arg)
            
    except Exception as e:
        if logger != None:
            logger.warning("Unknown error. Error value: {}".format(e))
        
        raise HoldException(str(e))


class RUCSpider(object):
    def __init__(self,
                setting_file:str = "./setting.yml"):
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
        
        logging.basicConfig(
            format = '[%(asctime)s]  <%(levelname)s>: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            filename = './log.log',
            filemode = 'a'
        )
        self.logger = logging.getLogger('<RUCSpider>')
        
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        formatter = logging.Formatter('[%(asctime)s]  <%(levelname)s>: %(message)s')
        ch.setFormatter(formatter)
        
        self.logger.addHandler(ch)
        
        self.timestamp = datetime.now().timestamp()
        self.DELTA_TIME = 18000
        self.manuals = False
        
        self.infos = self.CheckSettings()
    
    
    def update(self):
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
            raise ValueError('username(Your ID) is empty, please fill in your id in your setting file!')
        
        if info["password"] == None:
            raise ValueError('password is empty, please fill in your password in your setting file!')
        
        if info["token"] == None:
            self.logger.info('Token empty, pulling html to get one token.')
            
            info["token"] = self._GetToken_()
            
            Update = True
            
        if info["cookies"] == None or info["expire_time"] == None or len(info["cookies"]) == 0:
            self.logger.info('Cookie Empty, trying to login to gain a cookie')
            
            info["cookies"], info["expire_time"] = self._GetCookie_(info)
            
            Update = True
            
        if self.timestamp > info["expire_time"]:
            self.logger.info('Cookie Expired, trying to login to gain a new cookie')
            
            info["cookies"], info["expire_time"] = self._GetCookie_(info)
            
            Update = True
            
        for k,v in info["cookies"].items():
            if v == None:
                self.logger.info('Cookie incomplete, trying to login to gain a cookie')
                info["cookies"], info["expire_time"] = self._GetCookie_(info)
                break
            
        self.manuals = info["manual"]
            
        if info["interval_seconds"] == None:
            self.logger.info('Interval Empty, setting to default value(300)')
            
            info["interval_seconds"] = 300
            
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
        
        try:
            res_html = request_response(is_json = False, method = 'GET', logger = self.logger, url = url,headers = headers)
        except (AbortException,HoldException) as e:
            self.logger.warning(str(e))
            exit(0)
        except RetryException as e:
            arg = e.GetParams()
            res_html = request_response(arg,kwargs=arg["kwargs"])
        
        # with open('xxx.html',"w",encoding='utf-8') as f:
        #     f.write(res_html)
        
        regex = re.compile(r'(?<=<input type="hidden" name="csrftoken" value=")([\S]+)(?=" id="csrftoken" \/>)')
        token = re.search(regex,res_html)[0]
        
        assert len(token) == 10, "Unexpected error. {}".format(token)
        
        return token
    
    def _GetCookie_(self,info:dict,func = None):
        """
        Get the cookie by log in.
        Log in itself is not of a worth.
        
        Args:
            info: Dict[str:str] containing needed login information.

        Returns:
            Dict: the cookie dict.
            float: The expire timestamp
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
            
            try:
                captcha_info = request_response(logger = self.logger, url = captcha_url,headers = headers)
            except (HoldException,AbortException) as e:
                exit(0)
            except RetryException as e:
                arg = e.GetParams()
                captcha_info = request_response(arg,kwargs = arg["kwargs"])
            
            pattern = re.compile(r"(?<=data:image\/png;base64,)([\S]+)")
    
            b64_img = re.search(pattern,captcha_info["b64s"])[0]
            captcha_id = captcha_info["id"]
            
            if func != None:
                captcha_text = func(b64_img)
            else:
                captcha_text = OCRCODE(b64_img)
            
            return captcha_text,captcha_id,bytes(b64_img,encoding="utf-8")
            
        code,id,img = Retrieve_captcha()
        params["captcha_id"] = id
        params["code"] = code
        
        session = requests.Session()
        session.post(url = tgt_url, headers=headers, json = params)
        cookie = session.cookies.get_dict()
        
        if len(cookie) == 0:
            self.logger.warning("Unexpected error. Check username, password and captcha in 'error.txt' to ensure the login process is correct.")
            
            with open('error.txt','w',encoding='utf-8') as f:
                f.write("username:{}\n".format(params["username"][4:]))
                f.write("password:{}\n".format(params["password"]))
                f.write("code    :{}\n".format(params["code"]))
                
            imgdata = base64.b64decode(img)
            
            with open("{}.png".format(params["captcha_id"]),"wb") as f:
                f.write(imgdata)

        return cookie,self.timestamp + self.DELTA_TIME
    
    def PullLecture(self, maxlen:int = 30,Condition:list = None, Query:str = None, filter = lambda x: True):
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
        "query"        : "",
        "canregist"    : 0}
        
        headers = {'User-Agent': self.ua.random}
        
        new_lectures = []
        new_id = []
        
        # try:
        #     response = requests.post(url = tgt_url, headers = headers, json = params, cookies = self.infos["cookies"])
        # except Exception as e:
        #     self.logger.warning(str(e))
        #     self.logger.warning("Trying reload to refresh the cookie.")
        #     self._GetCookie_(self.infos)
        #     response = requests.post(url = tgt_url, headers = headers, json = params, cookies = self.infos["cookies"])
            
        try:
            response = request_response(method='POST',logger = self.logger, url = tgt_url,headers = headers,json = params,cookies = self.infos["cookies"])
        except HoldException as e:
            return
        except RetryException as e:
            arg = e.GetParams()
            self._GetCookie_(self.infos)
            response = request_response(method='POST',logger = self.logger, url = tgt_url,headers = headers,json = params,cookies = self.infos["cookies"])
        except Exception as e:
            self.logger.warning(str(e))
            return
        
        # response.encoding = 'utf-8'
        
        # try:
        #     results = json.loads(response.text)["data"]["data"]
        # except:
        #     self.logger.warning("Unable to load json, check 'error.txt' to see the response. Error on line {}".format(sys._getframe().f_lineno))
        #     with open("error.txt","w",encoding="utf-8") as f:
        #         f.write(response.text)
        #         return
        
        results = response["data"]["data"]
        
        if os.path.exists(SAVE_FILES):

            with open(SAVE_FILES,"r",encoding = 'utf-8') as f:
                saves = json.load(f)
                
        else:
            saves = {}
        
        Update = False
        
        if saves == {}:
            Update = True
        else:
            for lec in results:
                if lec not in saves:
                    self.logger.warning("New lecture found!")
                    Update = True
                    new_lectures.append(lec)
                
        if Update:
            with open(SAVE_FILES,"w",encoding = 'utf-8') as f:
                json.dump(results,f,ensure_ascii=False,separators=(',', ':'),indent=4)
            self.logger.info("Get new lecture. Written in file.")
            with open("log.txt","a",encoding='utf-8') as f:
                for lec in new_lectures:
                    f.write(lec["aname"] + ':' + lec["location"] + '\n')
                    f.write(lec["begintime"] + '~' + lec["endtime"] + '\n')
                    f.write('\n')
        
        new_id = [lec["aid"] for lec in new_lectures if filter(lec)]

        if len(new_id) != 0:
            print("Start Register!")
            self.register(new_id)
            
        self.logger.info("Check complete.")
        print("Check complete.")
    
    def register(self,aid:list):
        tgt_url = r"https://v.ruc.edu.cn/campus/Regist/regist"
        
        def sub_reg(id:int):
            params = {"aid":id}
            headers = {'User-Agent': self.ua.random}
            # response = requests.post(url = tgt_url, headers = headers, json = params, cookies = self.infos["cookies"])
            # response.encoding = 'utf-8'
            # results = json.loads(response.text)
            
            results = request_response(method = 'POST',logger = self.logger, url = tgt_url, headers = headers, json = params, cookies = self.infos["cookies"])
            
            return results["msg"]

        for id in aid:
            res = sub_reg(id)
            print("Register id {}:{}".format(id,res))

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
    
    spider = RUCSpider()
    with open("schedule.yml","r",encoding="utf-8") as f:
        timespan = yaml.load(f,Loader=yaml.FullLoader)
        
    spider.PullLecture(maxlen = 30, Condition = ["素质拓展认证","形势与政策","形势与政策讲座"],filter = packed(timespan))

    filt = packed(timespan)

    schedule.every(INTERVAL).seconds.do(spider.PullLecture,maxlen = 30, Condition = ["素质拓展认证","形势与政策","形势与政策讲座"])
    schedule.every(30).minutes.do(spider.update)
    
    while True:
        schedule.run_pending()

if __name__ == "__main__":
    main()