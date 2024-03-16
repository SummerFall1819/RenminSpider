import tkinter as tk
import base64

from typing import ByteString, AnyStr, Union

CODE_1 = ""

def GetCode(base64_img: Union[ByteString,AnyStr]):
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
        CODE_1 = code
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

def OCRCODE(base64_img: Union[ByteString,AnyStr]):
    from ddddocr import DdddOcr
    
    # close the ads.
    ocr = DdddOcr()
    if type(base64_img) == str:
        base64_img = bytes(base64_img, encoding = "utf-8")
    imgdata = base64.b64decode(base64_img)
    code = ocr.classification(imgdata)
    return code
    




