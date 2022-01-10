import time


def getTime(t):
    t = time.localtime(int(t))
    otherStyleTime = time.strftime("%Y-%m-%d", t)
    return otherStyleTime


t = time.strptime('2020-1-1', '%Y-%m-%d')
time.mktime(t)

