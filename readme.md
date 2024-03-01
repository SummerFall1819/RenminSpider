# RUC 学务活动检测器

## 简介
本系统适用于 `windows` 下对中国人民大学为人大平台学务中心上的活动进行监视，并自动对新活动进行注册报名的行为，旨在帮助校友进行自动监察新活动并进行报名。

## 安装
首先，用户应当克隆项目到本地。
```bash
git clone git@github.com:SummerFall1819/RUCSpider.git
```

之后，项目应当安装必要的依赖，其中必须使用的依赖可以以如下命令安装。
```bash
cd RUCSpider
pip install -r requirements.txt
```

**注意**：为了识别中国人民大学登陆时必要的验证码信息，您需要以下三项之一：
1. 程序每次进行登录时，手动输入验证码信息，此方法无需其他依赖。您需要在启动项目前，将 `setting.yml` 文件中 `manual` 改为 `True`，程序会提供简洁的 `tkinker` GUI 等待输入。
2. 采取本仓库提供的 `muggle-ocr` 实现方式，需要安装额外的依赖。
**此种方式将会影响您的 `tensorflow` 库和 `keras` 库**， **强烈建议在虚拟环境下进行**。
    如果您没有 `tensorflow` 环境，应当先安装 `tensorflow`.:
    ```bash
    pip insall tensorflow
    ```
    在安装完 `tensorflow` 之后，安装 `muggle-ocr`
    ```bash
    pip install ./package/muggle-ocr-1.0.3.tar.gz
    ```
    因而完成依赖设置。
3. 自行配置 OCR 环境，并在 `utils.py` 中重写函数。
    您可以重写 `OCRCODE` 函数，该函数接受以 `base64` 编码的 `png` 图片，最终返回该验证码对应的文本。

以上步骤完成后，您的项目文件树应当如下所示。
```apache
RUCSpider
│  alias.json
│  main.py
│  readme.md
│  requirements.txt
│  schedule.yml
│  setting.yml
│  spiderexcep.py
│  utils.py
│  
├─package
│      muggle-ocr-1.0.3.tar.gz
```

## 使用
在正式使用之前，应当先配置 `setting.yml` 文件。
其中包含的内容如下：
- `cookies` 程序会使用 `cookie` 直接登录微人大。初次使用无需填写任何信息，程序会自动抓取。
- `expire_time`: 记录 `cookie` 的有效期限，并确保每次重启动时更新。
- `interval_seconds`: 记录监视微人大学务的间隔时间，按秒记录。
- `password`: **必填**， 用户的登陆密码。形式为 `password: xxxxxxxxx`
    **此程序已完全开源，并保证本地部署不会外传任何敏感信息，但用户在使用程序时仍应当注意防止泄露密码。** 
- `username`: **必填**， 用户的学号。形式为 `username: 20xxxxxxxx`
- `manual`: 是否使用手动输入验证码，如果在安装时决定采用方法 1, 请修改为 `True`.

在完成修改之后，(激活虚拟环境)，运行 `main.py` 即可。

## 其他细节
对于希望通过这个程序获取微人大其他信息的同学而言，以下是必要的网站结构信息。


## 其他
本程序尚未完全完成，但目前可以实现基本功能。在后期会逐步改进。
