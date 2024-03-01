class AbortException(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message
    
    def __str__(self):
        return f"Spider Will Abort for error: {self.message}"

class RetryException(Exception):
    def __init__(self, message, *args, **kwargs):
        super().__init__()
        self.message = message
        self.infos = kwargs
        
    def __str__(self):
        return f"Spider Will Retry Connection due to error: {self.message}"
    
    def GetParams(self):
        return self.infos
    
class HoldException(Exception):
    def __init__(self, message):
        super().__init__()
        self.message = message
        
    def __str__(self):
        return f"Spider Will hold off until next connection due to error: {self.message}"

class functionException(Exception):
    def __init__(self, message, code):
        super().__init__()
        self.message = message
        self.code = code
        
    def __str__(self):
        return f"Function Exception: {self.message} with code: {self.code}"
    
    def GetCode(self):
        return self.code
    

if __name__ == '__main__':
    
    try:
        raise functionException('Test', 123)
    except functionException as e:
        print(e.GetCode())