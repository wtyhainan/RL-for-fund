import os
import csv
import time
import datetime
from datetime import timedelta

import numpy as np
import pandas as pd

from config import proj_path


def load_fund_data(file, encoding='utf-8'):
    with open(file, 'r', encoding=encoding) as f:
        codes = []      # 基金代码
        names = []      # 基金名称
        rates = []
        ftypes = []     # 基金类型
        risks = []      # 基金风险
        fsizes = []     # 基金规模
        est_datas = []  # 基金成立日
        managers = []    # 基金经理
        corps = []      # 管理公司
        stocks = []     # 投资股票
        bonds = []      # 投资债券
        for line in f:
            info = line.strip(' \n').split('***')
            codes.append(info[0] + '-')
            names.append(info[1])
            rates.append(info[2])
            type_ = info[3].split('\xa0\xa0|\xa0\xa0')
            if type_:
                ftypes.append(type_[0])
                risks.append('~') if len(type_) == 1 else risks.append(type_[1])
            else:
                raise ValueError('error')
            fsizes.append(info[4])
            est_datas.append(switch_time2timstamp(info[5], fmt='%Y-%m-%d')) if info[5] != '--' else est_datas.append(info[5])
            managers.append(info[6])
            corps.append(info[7])
            stocks.append(info[8])
            bonds.append(info[9])

    return (codes, names, rates, ftypes, risks, fsizes, est_datas, managers, corps, stocks, bonds)


def save_to_csv(datas, columns=None, encoding='utf_8_sig'):
    df = pd.DataFrame(datas, columns=columns)
    df.to_csv('../data/fund_info.csv', index_label='index', encoding=encoding)


def switch_time2timstamp(t, fmt="%Y-%m-%d %H:%M:%S"):
    t = time.strptime(t, fmt)
    time_stamp = int(time.mktime(t))
    return time_stamp


def load_fund_profit(fscode, encoding='utf-8'):
    '''这里应该要用Pathlib来处理路径问题，这样就不会受平台影响'''
    file = os.path.join(proj_path, 'data\\worthTrend\\' + fscode+'.txt')
    with open(file, encoding=encoding) as f:
        data = f.read()
        data = data.strip(' ').split(' ')

    t, profit = [], []
    for point in data:
        if not point:
            continue
        (x, y) = point.split('-')
        t.append(int(x))    # 成立日这里只有到day，因此可以直接int，一般是要float之后才int
        profit.append(float(y))
    return (np.array(t), np.array(profit))


def to_timestamp(t, fmt='%Y-%m-%d'):
    # t: YYYY-mm-dd
    return time.mktime(time.strptime(t, fmt))


def to_time(timestamp, fmt='%Y-%m-%d'):
    return time.strftime(fmt, time.localtime(int(timestamp)))


def is_new_fund(est_date):
    '''成立超过一年就算是老基金'''
    if est_date == '--':
        return True
    est_t = time.localtime(int(est_date))
    est_t = time.strftime('%Y-%m-%d', est_t).split('-')
    est_t = datetime.date(year=int(est_t[0]), month=int(est_t[1]), day=int(est_t[2]))
    curtime = datetime.date.today()
    return (curtime - est_t).days < 365


if __name__ == '__main__':
    pass

