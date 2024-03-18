
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
    def __init__(self, message):
        super().__init__()
        self.originError = message
        
    def __str__(self):
        return f"Spider Will Retry Connection due to error: {self.originError}"
    
class HoldException(Exception):
    def __init__(self, message):
        super().__init__()
        self.originError = message
        
    def __str__(self):
        return f"Spider Will hold off until next connection due to error: {self.originError}"
