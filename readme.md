# RUC 学务活动检测器

## 简介
本系统适用于 `windows` 下对中国人民大学为人大平台学务中心上的活动进行监视，并自动对新活动进行注册报名的行为，旨在帮助校友进行自动监察新活动并进行报名。

## 安装
首先，用户应当克隆项目到本地。
```bash
git clone git@github.com:SummerFall1819/RenminSpider.git
```

之后，项目应当安装必要的依赖，其中必须使用的依赖可以以如下命令安装。
```bash
cd RUCSpider
pip install -r requirements.txt
```

**注意**：为了识别中国人民大学登陆时必要的验证码信息，您需要以下三项之一：
1. 程序每次进行登录时，手动输入验证码信息，此方法无需其他依赖。您需要在启动项目前，将 `setting.yml` 文件中 `manual` 改为 `True`，程序会提供简洁的 `tkinker` GUI 等待输入。
2. 采取本仓库提供的 `ddddocr` 实现方式。额外的依赖已经在 `requirements.txt` 中列出并安装。
    - **注意**：由于 `ddddocr` 使用 `PIL.image` 中已经在 `10.0.0` 弃用的方法 `Image.ANTIALIAS`. 因此需要对 `Pillow` 降级以避免此错误。或者，修改 `ddddocr` 的 `_init_.py` 文件，将其中的 `ANTIALIAS` 替换为新方法 `LANCZOS`. 出于自动配置的需要，这里使用了 `Pillow` 降级的方式。
    对应错误：
        ```bash
        image = image.resize((int(image.size[0] * (64 / image.size[1])), 64), Image.ANTIALIAS).convert('L')
        ```
    - 程序会根据会话返回判断是否是验证码有误导致的登陆失败，早期版本中会以 `error.txt` 记录错误信息，现在已经删除。

3. 自行配置 OCR 环境，并在 `utils.py` 中重写函数。
    您可以重写 `OCRCODE` 函数，该函数接受以 `base64` 编码的 `png` 图片，最终返回该验证码对应的文本。

以上步骤完成后，您的项目文件树应当如下所示。
```apache
RUCSpider
    alias.json          # record the alias of the classification.
    main.py             
    readme.md           
    requirements.txt
    RUCWeb.ico          # the icon of the toast reminder.
    schedule.yml        # (optional) The schedule of the week.
    setting.yml         # relative settings about this program.
    spiderexcep.py
    spiderlog.py
    utils.py            
```

## 使用
在正式使用之前，应当先配置 `setting.yml` 文件。
其中包含的内容如下：
- `cookies` 程序会使用 `cookie` 直接登录微人大。初次使用无需填写任何信息，程序会自动抓取。
- `expire_time`: 记录 `cookie` 的有效期限，并确保每次重启动时更新。
- `interval_seconds`: 记录监视微人大学务的间隔时间，按秒记录。
- `password`: 用户的登陆密码。形式为 `password: xxxxxxxxx`
    如果不希望将其以明文存储，检测为空时，程序将通过控制台获取密码。
- `username`:  用户的学号。形式为 `username: 20xxxxxxxx`
    如果不希望将其以明文存储，检测为空时，程序将通过控制台获取学号。
- `manual`: 是否使用手动输入验证码，如果在安装时决定采用方法 1, 请修改为 `True`.
- `notify` 可选为 `none/toast/wx`。其中：

    - `none` 不进行除了日志记录之外的其他提醒行为。
    - `toast` 会在报名成功后弹出窗口进行提示。
    - `wx` 会在报名成功后进行微信推送。

如果采用 `wx` 方式，需要一并填写 `apptoken` 和 `uid` 信息，参考请见 **其他细节-wxpush使用** 部分。

在完成修改之后，(激活虚拟环境)，运行 `main.py` 即可。

使用者应当注意，对于提示“报名成功”的活动，并不一定具有参与资格。活动可能取消或延期，请及时登陆微人大查看参会信息。


## 其他细节

### wxpush 使用

[wxPusher(微信推送活动)](https://github.com/wxpusher/wxpusher-sdk-java/) 由 @zjiecode 提供。 在此略过诸多细节，仅说明如何操作使程序可运行。

- 首先，请 [依指令注册并创建一个应用](https://wxpusher.zjiecode.com/admin/)。在此过程中，用户将获得一个唯一的 `app_token`. 请将此 `app_token` 作为 `apptoken` 填入 `setting.yml` 文件。
- 创建应用之后，进入分享页面，通过二维码或链接关注此应用。
- 获取自己的 `uid`.
    - 关注公众号：wxpusher，然后点击「我的」-「我的UID」查询到UID；

获取自己的 `uid` 并填入 `setting.yml` 文件。


### 基于本程序的其他改进
**以防有人想不到，可以通过增加** `schedule.every(INTERVAL).seconds.do(spider.PullLecture,maxlen = 30, Condition = <CONDITION>, filter = filt)` **来进行多个条件的同时筛选**。


#### 筛选器
本程序提供了一个 `filter` 接口，以协助进行必要的讲座条件检查。默认不进行筛选，但仍旧实现了一个简单的筛选器：其根据你给出的空闲时间区间检查讲座是否在空闲时间区间内。如果用户希望使用这个筛选器，应当修改 `schedule.yml` 下列出的七天的信息。阅读 `yaml` 文件在此不作赘述。时间从星期一到星期天。修改完 `schedule.yml` 后，在 `main.py` 下 `schedule.every(INTERVAL).seconds.do` 函数处增加参数 `filter = filt` 即可。

如果希望自定义一个筛选器，其筛选器函数要求如下：
```python
def func(lec:dict):
    """
    This function take excatly one lecture information, and check if it satisfy the restrictions.

    Args:
        lec (dict): lecture information.
    Returns:
        bool: True if the lecture satisfy the restrictions, false otherwise.
    """
    
    # your code here.
```

你可以通过 `python` 的柯里化引入更多参数。

#### OCR 接入
除开重写 `OCR` 之外，你也可以定义自己的方式来获取验证码，并在 `main.py`, `RUCSpider` 初始化处加入 `captcha_func = [Callable]` 加入函数要求如下
```python
def captcha_func(base_64_img:str|bytes):
    """
    This function load in a base64 encoded image, and return the captcha code.
    
    Args:
        base_64_img (str|bytes): base64 encoded image.
    
    Returns:
        str: captcha code.
    """

    # Your code here.
```
这种函数是不限于 `OCR` 方式的，你可以自主设计任何的方式，只要能从中获得验证码即可。

#### 讲座类型筛选
本程序默认是处于筛选形势与政策讲座而设计的，在 `alias.json` 下保存了少量的条件筛选内容。如果您希望进行其他讲座的监看，请修改 `main.py` 下 `CONDITION`, 其元素数目为三个，分别对应活动大类、活动小类、小类子类的筛选。
(活动状态和组织单位的实现与监看的初衷冲突，故未实现)，如果希望查找活动名称，那么在 `PullLecture` 下加入 `Query` 为关键词即可。
**注意**：有些小类子类名称与活动小类重复，这种情况请将小类子类更改为 “不限”，即可实现内容。

#### 提示内容处理
如果，用户希望实现类似于 `toast` 和 `wx` 对应的提示方式。请在 `spiderlog.py` 中完成一个自己的实现。
```python
def NotificationFunc(lectures: list):
    """
    This function would notify the contetn of the lectures in the way you desire.

    Hint: You may want to use curry to add more parameters.
    """
    # code.
```

并将其注册在 `NOTIFIER` 中。从而可以在 `setting.yml` 中使用自己注册的方法进行提醒。



### 程序实现细节
在 `PullLecture` 中获得的会议信息 `json` 存储形式如下：
```json
{
    "aid":<lecture ID>,
    "aname":<lecture name>,
    "abstract":<lecture abstract>,
    "typelevel2":<small class>,
    "typelevel3":<subclass>,
    "begintime":<begin time>,
    "endtime":<end time>,
    "location":<lecure location>,
    "sponsordeptids": <>,
    "contacts":<联系人>,
    "publishrange":<>,
    "publishrangeid":<>,
    "ispublic":<>,
    "needregist":<>,
    "allowednum":<allow register number>,
    "waitlistnum":<>,
    "registbegintime":<>,
    "registendtime":<>,
    "filterconf":<>,
    "registnotice":<>,
    "partakemode":<>,
    "uploadendtime":<>,
    "uploadrules":<>,
    "allowcomment":<>,
    "logo":<>,
    "poster":<url of the post>,
    "description":<>,
    "activity_show":<>,
    "prizesetting":<>,
    "attentions":<>,
    "applyscore":<>,
    "organizescore":<>,
    "partakescore":<the score of this lecture>,
    "prizescore":<>,
    "verifieruid":<>,
    "status":<>,
    "verifystatus":<>,
    "version":<>,
    "schoolid":<>,
    "ctime":<>,
    "mtime":<>,
    "ascore":<>,
    "progress":<>,
    "scorestatus":<>,
    "vtime":<>,
    "tags":<>,
    "allowsignin":<>,
    "partakescorestatus":<>,
    "themeid":<>,
    "codechangetime":<>,
    "signaction":<>,
    "departmentid":<>,
    "typelevel1":<big class>,
    "yxbmxs":<>,
    "yxbmdwmax":<>,
    "mzdysmin":<>,
    "mzdysmax":<>,
    "teacher":<>,
    "field":"[
        {\"id\":<>,
        \"uid\":<>,
        \"type1\":<>,
        \"type2\":<>,
        \"type3\":<>,
        \"field\":<>,
        \"is_necessary\":<>,
        \"created_at\":<>,
        \"updated_at\":<>,
        \"$$hashKey\":<>,
        \"value\":<>,
        {\"id\":<>,
        \"uid\":<>,
        \"type1\":<>,
        \"type2\":<>,
        \"type3\":<>,
        \"field\":<>,
        \"is_necessary\":<>,
        \"created_at\":<>,
        \"updated_at\":<>,
        \"$$hashKey\":<>,
        \"value\":<>}]",
    "custom_poster":<>,
    "partakemodename":<>,
    "statusname":<>,
    "verifystatusname":<>,
    "progressname":<报名中/未开始/已结束>,
    "scorestatusname":<>,
    "sfyxtdbm":<>,
    "username":<>,
    "registname":<>
},


```

## 其他
本程序尚未完全完成，但目前可以实现基本功能。在后期会逐步改进。

TODO:
- 增加时间选项，在长期之后打开会进行相应的处理。