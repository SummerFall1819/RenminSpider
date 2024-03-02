import tkinter as tk
import base64

CODE_1 = "?"
# ddddocr

def GetCode(base64_img: bytes|str):
    window = tk.Tk()
    
    global CODE_1
    
    # pack the img in the window.
    im = tk.PhotoImage(data = base64_img)
    tk.Label(window, image = im).pack()
    
    # pack the input bar with Enter.
    entry = tk.Entry(window,width = 20)
    entry.pack()
    # bind the entry function.
    # the confirmation would close the window.
    def Confirm(event):
        code = entry.get()
        global CODE_1
        print(CODE_1)
        CODE_1 = code
        print(code, CODE_1)
        window.destroy()
        return 'break'
    entry.bind('<Return>',Confirm)
    flag = 1
    
    while flag:
        window.update()
        try:
            flag = window.winfo_exists()
        except:
            flag = 0
    # window.mainloop()
    return CODE_1


def OCRCODE(base_64_img: str):
    import muggle_ocr
    sdk = muggle_ocr.SDK(model_type=muggle_ocr.ModelType.Captcha)
    if type(base_64_img) == str:
        base_64_img = bytes(base_64_img, encoding = "utf-8")
    imgdata = base64.b64decode(base_64_img)
    text = sdk.predict(imgdata)
    
    return text

def OCRCODE(base64_img: str|bytes):
    from ddddocr import DdddOcr
    
    ocr = DdddOcr()
    if type(base_64_img) == str:
        base_64_img = bytes(base_64_img, encoding = "utf-8")
    imgdata = base64.b64decode(base_64_img)
    
    code = ocr.classification(imgdata)
    
    return code
    




