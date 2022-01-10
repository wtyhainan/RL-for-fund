import time
import datetime
from datetime import timedelta

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei'] #用来正常显示中文标签
plt.rcParams['axes.unicode_minus'] = False #用来正常显示负号

from analysisdata import utils
import utils_


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


def to_timestamp(t):
    # t: YYYY-mm-dd
    return time.mktime(time.strptime(t, '%Y-%m-%d'))


def calc_fund_profit(fscode):
    '''
    :param fscode:基金代码
    :return:
    '''
    now = datetime.date.today()     # 当前时间
    mon_ago_tstamp = to_timestamp((now - timedelta(days=30)).strftime('%Y-%m-%d'))
    three_mon_ago_tstamp = to_timestamp((now - timedelta(days=90)).strftime('%Y-%m-%d'))
    six_mon_ago_tstamp = to_timestamp((now - timedelta(days=180)).strftime('%Y-%m-%d'))
    year_ago_tstamp = to_timestamp((now - timedelta(days=365)).strftime('%Y-%m-%d'))

    ts_stamp, profit = utils.load_fund_profit(fscode)
    if not len(profit):
        return 0.0, 0.0, 0.0, 0.0

    mon_ago_profits, three_mon_ago_profits, six_mon_ago_profits, year_ago_profits = [], [], [], []

    for idx, t in enumerate(ts_stamp):
        int_t = int(t)
        if int_t >= mon_ago_tstamp:
            mon_ago_profits.append(float(profit[idx]))
        if int_t >= three_mon_ago_tstamp:
            three_mon_ago_profits.append(float(profit[idx]))
        if int_t >= six_mon_ago_tstamp:
            six_mon_ago_profits.append(float(profit[idx]))
        if int_t >= year_ago_tstamp:
            year_ago_profits.append(float(profit[idx]))

    if len(mon_ago_profits) <= 1:
        mon_ago_profit = 0
    else:
        mon_ago_profit = (np.mean(mon_ago_profits) - mon_ago_profits[0]) / mon_ago_profits[0]

    if len(three_mon_ago_profits) <= 1:
        three_mon_ago_profit = 0
    else:
        three_mon_ago_profit = (np.mean(three_mon_ago_profits) - three_mon_ago_profits[0]) / three_mon_ago_profits[0]

    if len(six_mon_ago_profits) <= 1:
        six_mon_ago_profit = 0
    else:
        six_mon_ago_profit = (np.mean(six_mon_ago_profits) - six_mon_ago_profits[0]) / six_mon_ago_profits[0]

    if len(year_ago_profits) <= 1:
        year_ago_profit = 0
    else:
        year_ago_profit = (np.mean(year_ago_profits) - year_ago_profits[0]) / year_ago_profits[0]

    return (mon_ago_profit, three_mon_ago_profit, six_mon_ago_profit, year_ago_profit)


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
    if corps_name is None:
        corps_name = get_all_fund_coprs(fund_df)

    df = fund_df.set_index(keys='corp').loc[corps_name].reset_index()

    # 定义一个空的corp_df
    corp_info_df = pd.DataFrame()

    # 1、规模
    corps_fund_size = df.groupby('corp')['size'].sum()
    corp_info_df['size'] = corps_fund_size

    # 2、旗下基金数
    corp_funds = df.groupby('corp')['code'].count()
    corp_info_df['num_fund'] = corp_funds

    # 将时间戳转换为时间格式。调用time.strftime()将一个时间元组转换成时间格式。time.localtime(t)该函数将一个时间戳转换成时间元组
    df['new_time_fmt'] = df['date'].apply(lambda t: time.strftime("%Y-%m-%d", time.localtime(int(t))) if t != '--' else '00-00-00')

    # 3、老基金信息。（老基金数，老基金规模， 老基金规模占比，老基金收益）
    ## 3.1 找到新成立基金
    def is_new_fund(est_date):
        '''成立超过一年就算是老基金'''
        if est_date == '--':
            return False
        est_t = time.localtime(int(est_date))
        est_t = time.strftime('%Y-%m-%d', est_t).split('-')
        est_t = datetime.date(year=int(est_t[0]), month=int(est_t[1]), day=int(est_t[2]))
        curtime = datetime.date.today()
        return (curtime - est_t).days < 365

    df['is_new_fund'] = df['date'].apply(is_new_fund)    # 添加一列，

    ## 3.2 计算老基金数及规模
    corp_old_fund_size = df.groupby(['corp', 'is_new_fund'])['size'].sum().filter(like='False')

    corp_info_df['old_num_fund'] = corp_info_df['num_fund'] - df.groupby('corp')['is_new_fund'].sum()  # 老基金数

    df_ = pd.merge(corp_old_fund_size, corps_fund_size, on='corp', suffixes=("_old", "_all"))

    corp_info_df['size_rate'] = df_['size_old'] / df_['size_all']   # 老基金规模

    ## 3.3 计算老基金收益
    def filter_new_fund(group):
        return not group.name[1]

    def calc_corp_profit(s):
        fn = lambda x: x[0:-1]
        s = s.apply(fn)
        profits = s.apply(calc_fund_profit).values
        mon_profit, three_profit, six_profit, year_profit = 0, 0, 0, 0

        for a, b, c, d in profits:
            mon_profit += a
            three_profit += b
            six_profit += c
            year_profit += d
        len_ = len(profits)
        return [mon_profit / len_, three_profit/len_, six_profit/len_, year_profit/len_]

    df_ = df.groupby(['corp', 'is_new_fund']).filter(filter_new_fund).groupby('corp')['code'].apply(calc_corp_profit)  # apply函数返回值一定与index相同，无论返回的值是list还是tuple都会当作一个值对待

    profit_df = pd.DataFrame()
    profit_df['corp'] = df_.index

    # 在filter_new_fund之后，会有一部分基金公司旗下没有基金，这回导致企业数不一致，这时候应该采用merge来处理。
    mon_profits, three_profits, six_profits, year_profits = [], [], [], []
    for profits in df_:
        mon_profits.append(profits[0])
        three_profits.append(profits[1])
        six_profits.append(profits[2])
        year_profits.append(profits[3])

    profit_df['mon_profit'] = mon_profits
    profit_df['three_profit'] = three_profits
    profit_df['six_profit'] = six_profits
    profit_df['year_profit'] = year_profits
    corp_info_df = corp_info_df.merge(profit_df, how='outer', on='corp')
    return corp_info_df


    # ### 3.3.1 删除新基金
    # index = df['is_new_fund'].index
    # tmp_df = df.drop(index)
    # # help(df.drop)
    # print(tmp_df)
    # print(df)

    # 计算corp整体收益水平
    # df.groupby(['corp', 'is_old_fund'])['code'].filter(like='True').transform(calc_corp_profit)     # 这里也不是只计算老基金的收益
    # old_fund_df = df.drop(df['is_old_fund'].iloc!df['is_old_fund'])

    # # 统计原始的信息（基金公司规模，基金公司旗下基金总数）
    # # 1、找出想要查看的基金公司
    # fund_df = fund_df.set_index(keys='corp').loc[corps_name].reset_index()
    # fund_df['new_date'] = fund_df['date'].apply(lambda t: time.strftime('%Y-%m-%d', time.localtime(int(t))) if t != '--' else '00-00-00')
    #
    # print(f'fund_df shape: {fund_df.shape}')
    #
    # # 规模
    # corp_fund_size = fund_df.groupby('corp')['size'].sum()
    # # 旗下基金数量
    # corp_nfund = fund_df.groupby('corp')['code'].count()
    #
    # # 判断是否是新成立基金
    # def is_new_fund(x, ft='2021-1-1'):
    #     ft = time.strptime(ft, "%Y-%m-%d")
    #     t = time.mktime(ft)
    #     return x.apply(lambda z: int(z) > t if z != '--' else False)
    #
    # # 删除新成立基金
    # old_fund_df = fund_df.drop(fund_df[is_new_fund(fund_df['date'], ft='2013-03-08')].index)
    #
    # print(old_fund_df.shape)
    #
    # # # 计算老基金的基本信息
    # # o_fund_size = old_fund_df.groupby('corp')['size'].sum()   # corp中老基金的规模
    # # # 将两个数据做合并，然后求比例
    # # fund_rate_df = pd.merge(corp_fund_size, o_fund_size, how='left', on='corp').fillna(0.0)
    # # fund_rate_df['rate'] = fund_rate_df['size_y'] / fund_rate_df['size_x']  # 得到每家基金公司老基金规模占整体规模比
    # #
    # # # 计算老基金的收益（最近一年收益，最近半年收益，最近三个月收益，最近一个月的收益）
    # # def calc_profit(s: pd.Series):
    # #     s = s.transform(lambda x: x[0:-1])
    # #     return s.apply(calc_fund_profit)
    # #
    # # print(old_fund_df.groupby('corp')['code'].transform(calc_profit))


if __name__ == '__main__':

    df = pd.read_csv('../data/fundInfo.csv', encoding='utf_8')
    df = df.rename(columns=fund)    # 列重命名
    df = clean_data(df)
    df = df[['code', 'name', 'size', 'corp', 'date']]
    ts = time.time()
    corp_info_df = corp_info(df)
    # print('consume time: s', time.time()-ts)
    corp_info_df.to_csv('test.csv', encoding='gbk')




