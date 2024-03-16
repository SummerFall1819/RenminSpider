
import time
# Spider will abort for this kind of exceptions.
class AbortException(Exception):
    def __init__(self, message):
        super().__init__()
        self.originError = message
    
    def __str__(self):
        return f"Spider Will Abort for error: {self.originError}"

# Spider will retry connection for this kind of exceptions.
class RetryException(Exception):
    def __init__(self, message, func = None, wait_time_seconds:int = 1, Retry_times:int = 5, *args, **kwargs):
        super().__init__()
        self.originError = message
        self.waitTime = wait_time_seconds
        self.Retry_time = Retry_times
        self.func = func
        self.params = kwargs
        
    def __str__(self):
        return f"Spider Will Retry Connection due to error: {self.originError}"
    
    def GetParams(self):
        return self.params
    
    def retry(self):
        for __ in range(self.Retry_time):
            time.sleep(self.waitTime)
            try:
                return self.func(self.params)
            except:
                pass
        raise AbortException("Exceed Max Retry times on function {}".format(getattr(self.func,'__name__')))
    
class HoldException(Exception):
    def __init__(self, message):
        super().__init__()
        self.originError = message
        
    def __str__(self):
        return f"Spider Will hold off until next connection due to error: {self.originError}"
