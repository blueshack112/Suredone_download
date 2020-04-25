import sys
import traceback

def uncaughtExceptionLogger(exctype, value, tb):
    print ('My Error Information')
    print ('Type:', exctype)
    print ('Value:', value)
    print ('Traceback:', )
    
    for i in traceback.format_list(traceback.extract_tb(tb)):
        print (i)



sys.excepthook = uncaughtExceptionLogger

def raiseError():
    raise FileExistsError

def raiseError2():
    raiseError()
raiseError2()