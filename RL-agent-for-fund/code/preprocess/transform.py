import os

import time
import datetime
from datetime import timedelta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False #用来正常显示负号

# from preprocess import utils as
from utils import is_new_fund, to_timestamp, to_time, load_fund_profit, binary_search
from utils import timestamp_delta
from config import proj_path, NOW


fund_info_file = '../data/fundsInfo.txt'


fund = {
        '基金代码': 'code',
        '基金名称': 'name',
        '申购费率': 'rate',
        '基金类型': 'type',
        '基金风险': 'risk',
        '基金规模': 'size',
        '成立日': 'date',
        '基金经理': 'manager',
        '基金公司': 'corp',
        '投资股票': 'stocks',
        '投资债券': 'bonds'}




# (codes, names, ftypes, risks, fsizes, est_datas, manager, corps, stocks, bonds) = utils.load_fund_info(fund_info_file)
#     datas = []
#     for i in zip(codes, names, ftypes, risks, fsizes, est_datas, manager, corps, stocks, bonds):
#         datas.append(i)
#     utils.save_to_csv(datas, columns=['基金代码', '基金名称', '基金类型', '基金风险', '基金规模',
#                                       '成立日', '基金经理', '基金公司', '投资股票', '投资债券'])

def clean_data(fund_df: pd.DataFrame):
    ''' 对每一列数据做清理操作。对于不存在的项，均以np.nan来代替 '''
    # 删除重复的基金
    fund_df.drop_duplicates('code', inplace=True)
    size_func = lambda s: s.split('亿元')[0] if s != '~' else '--'
    fund_df['size'] = fund_df['size'].apply(size_func).replace('--', 0.0).astype(np.float, copy=False)
    return fund_df


def get_all_fund_coprs(df):
    return df['corp'].unique()


def calc_fund_profit(fscode, now=NOW):
    '''
    :param fscode:基金代码
    :param now: 当前日期
    :return:
    '''

    ts_stamp, profits = load_fund_profit(fscode)     # 加载数据

    profit_info = [0.0] * 4

    if len(profits) <= 1 or timestamp_delta(ts_stamp[0], ts_stamp[-1]) < 30:     # 没有历史收益数据或者历史数据不超过一个月
        return profit_info

    if now is None:
        now = datetime.date.today()
    else:
        now = [int(i) for i in now.split('-')]
        now = datetime.date(now[0], now[1], now[2])

    mon_ago_tstamp = to_timestamp((now - timedelta(days=30)).strftime('%Y-%m-%d'))
    three_mon_ago_tstamp = to_timestamp((now - timedelta(days=90)).strftime('%Y-%m-%d'))
    six_mon_ago_tstamp = to_timestamp((now - timedelta(days=180)).strftime('%Y-%m-%d'))
    year_ago_tstamp = to_timestamp((now - timedelta(days=365)).strftime('%Y-%m-%d'))

    hist_timestamp = [mon_ago_tstamp, three_mon_ago_tstamp, six_mon_ago_tstamp, year_ago_tstamp]

    for i in range(4):
        idx = binary_search(ts_stamp, hist_timestamp[i])
        if idx:
            profit_info[i] = (profits[-1] - profits[idx]) / profits[idx] * 100
    return profit_info


def rename_column(df):
    df = df.rename(columns=fund)  # 列重命名
    return df


def corp_info(fund_df, corps_name=None):
    '''返回corps信息：
    1、规模
    2、旗下基金数量
    3、成立超过半年的基金数量
    4、成立超过半年基金占总基金数量
    5、旗下基金占比
    6、旗下基金风险
    7、近一年、近半年、近三个月的平均盈利水平
    '''
    fund_df = rename_column(fund_df)  # 重命名
    fund_df = clean_data(fund_df)   # 清理数据

    if corps_name is None:
        corps_name = get_all_fund_coprs(fund_df)
    # corps_name = corps_name[0:10]

    df = fund_df.set_index(keys='corp').loc[corps_name].reset_index()

    # 将时间戳转换为时间格式。调用time.strftime()将一个时间元组转换成时间格式。time.localtime(t)该函数将一个时间戳转换成时间元组
    df['new_time_fmt'] = df['date'].apply(
        lambda t: time.strftime("%Y-%m-%d", time.localtime(int(t))) if t != '--' else '00-00-00')
    df['is_new_fund'] = df['date'].apply(is_new_fund)  # 添加一列，

    # 定义一个空的corp_df，用于保存基金公司信息
    corp_info_df = pd.DataFrame()

    # 1、公司规模
    corp_info_df['size'] = df.groupby('corp')['size'].sum()
    # 2、公司旗下基金数
    corp_info_df['num_fund'] = df.groupby('corp')['code'].count()

    # 统计老基金信息
    ## 3.1 老基金数占比
    corp_info_df['num_old_fund_rate'] = (corp_info_df['num_fund'] - df.groupby('corp')['is_new_fund'].sum()) / corp_info_df['num_fund']

    ## 3.2 老基金与新基金规模比
    df['tmp'] = df.apply(lambda s: 0 if s['is_new_fund'] else s['size'], axis=1)
    corp_info_df['old_new_size_rate'] = df.groupby('corp')['tmp'].sum() / df.groupby('corp')['size'].sum()

    ## 3.3 计算基金公司老基金平均收益
    fund_profit_info = lambda s: (0, 0, 0, 0) if s['is_new_fund'] else calc_fund_profit(s['code'][0:-1])
    df[['mon_profit', 'three_mon_profit', 'six_mon_profit', 'year_profit']] = df.apply(fund_profit_info, axis=1, result_type='expand')
    corp_info_df[['mon_profit', 'three_mon_profit', 'six_mon_profit', 'year_profit']] = df.groupby('corp')[['mon_profit', 'three_mon_profit', 'six_mon_profit', 'year_profit']].mean()

    return corp_info_df.reset_index()


if __name__ == '__main__':
    df = pd.read_csv('../data/fundInfo.csv', encoding='utf_8')

    ts = time.time()
    corp_info_df = corp_info(df)
    print('consume time: s', time.time()-ts)

    save_file = os.path.join(proj_path, 'data\\corpInfo.csv')
    corp_info_df.to_csv(save_file, index=False, encoding='gbk')


