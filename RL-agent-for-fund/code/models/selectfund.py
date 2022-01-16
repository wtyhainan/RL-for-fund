# -*- coding: utf-8 -*-

'''
date: 2022/1/11
function: 挑选合适基金
'''
import warnings
import time
import datetime
from datetime import timedelta

import pandas as pd
import numpy as np

from preprocess import transform
from utils import is_new_fund, load_fund_profit, to_timestamp, to_time, load_fund_data, binary_search, timestamp_delta
from config import InvestType, NOW

warnings.filterwarnings('ignore')


radical_invest_type = InvestType['radical']


class BaseFundAgent(object):
    def __init__(self):
        pass

    def policy(self):
        raise Exception('you must rewrite policy function')

    def __call__(self, fund_df: pd.DataFrame, corp_df=None, w=[10, 8, 7, 6, 5, 4, 2]):
        return self.policy(fund_df, corp_df, w)


class FundSelectAgent(BaseFundAgent):

    def __int__(self):
        super(FundSelectAgent, self).__init__()

    def _get_delta_time(self, days):
        now = [int(i) for i in NOW.split('-')]
        cur = datetime.date(now[0], now[1], now[2])
        delta_t = (cur - timedelta(days=days)).strftime('%Y-%m-%d')
        delta_t = to_timestamp(delta_t, fmt='%Y-%m-%d')
        return delta_t

    def _hist_profit_info(self, fscode, time_w=[10, 7, 5, 2]):
        '''
        :param w：不同时期指标的权重
        w[0]: 最近一个月的收益信息权重
        w[1]: 最近三个月的收益信息权重
        w[2]: 最近半年的收益信息权重
        w[3]: 最近1年的收益信息权重
        :param invest_type=radical或者stable
        :return:
        '''

        time_w = np.array(time_w) / np.sum(time_w)  # 归一化

        def calc_risk_profit(ts, profits, delta_days=30):
            idx = binary_search(ts, self._get_delta_time(days=delta_days))
            if idx is None: return np.zeros(shape=(5, ))
            if timestamp_delta(ts[idx], ts[-1]) < delta_days * 0.6:
                return np.zeros(shape=(5, ))

            profits_ = profits[idx:]
            profits_d = (profits_[1:] - profits_[0:-1]) / profits_[0:-1] * 100
            max_retracement = np.min(profits_d)
            # 找到所有小于0的值
            neg_idx = np.where(profits_d < 0)[0]
            mean_retracement = np.mean(profits_d[neg_idx])
            # 累积收益
            acc_profit = (profits_[-1] - profits_[0]) / profits_[0]
            # 平均收益
            mean_profit = np.mean(profits_d)
            std_profit = np.std(profits_d)
            # 最大回撤、平均回撤、累积收益、平均收益、收益方差
            return np.array([max_retracement, mean_retracement, acc_profit, mean_profit, std_profit])
        ts, profits = load_fund_profit(fscode)
        if len(profits) <= 1 or timestamp_delta(ts[0], ts[-1]) < 30:
            return np.zeros(shape=(5, ))

        one_mon_profit_info = calc_risk_profit(ts, profits, delta_days=30)
        three_mon_profit_info = calc_risk_profit(ts, profits, delta_days=90)
        six_mon_profit_info = calc_risk_profit(ts, profits, delta_days=180)
        year_profit_info = calc_risk_profit(ts, profits, delta_days=365)
        profit_info = time_w[0] * one_mon_profit_info + time_w[1] * three_mon_profit_info + time_w[2] * six_mon_profit_info + time_w[3] * year_profit_info
        return profit_info

    def _get_target_corp(self, corp_df, w, top=10):
        w = np.array(w) / np.sum(w)  # 权重归一化

        df = corp_df.set_index(keys='corp')
        df_ = df[['size', 'old_new_size_rate', 'num_fund', 'num_old_fund_rate', 'mon_profit', 'three_mon_profit', 'six_mon_profit', 'year_profit']]

        df_ = (df_ - df_.min()) / (df_.max() - df_.min())  # 数据归一化
        nd_df = df_.to_numpy()
        corp_score = []
        for info in nd_df:
            score = info * w
            corp_score.append(np.sum(score))
        df_['score'] = corp_score
        df_ = df_.sort_values('score', ascending=False)
        return df_.index[0:top]

    def _get_target_fund_from_corps(self, fund_df, corps_name, w, top=10):

        w = np.array(w) / np.sum(w)  # 权重归一化
        fund_df = transform.rename_column(fund_df)
        fund_df = transform.clean_data(fund_df)

        fund_df = fund_df.set_index(keys='corp').loc[corps_name]    # 保留corps_name对应的项
        df = fund_df.reset_index()

        # 保留老基金
        df['is_new_fund'] = df['date'].apply(is_new_fund)

        df = df.set_index(keys='is_new_fund').loc[False].reset_index()

        # 计算每支基金的评分
        df[['max_retrace', 'mean_retrace', 'acc_profit', 'mean_profit', 'std_profit']] = \
            df.apply(lambda s: self._hist_profit_info(s['code'][0:-1]), axis=1, result_type='expand')

        def calc_fund_rank(s):
            return np.sum(s.values * w)
        score = df[['max_retrace', 'mean_retrace', 'acc_profit', 'mean_profit', 'std_profit']]
        score = (score - score.min()) / (score.max() - score.min())
        df['score'] = score.apply(calc_fund_rank, axis=1)
        return df.sort_values('score', ascending=False).iloc[0:top]

    def policy(self, fund_df, corp_df=None, w=[10, 8, 7, 6, 5, 4, 2]):
        '''
        :param: w = [w0, w1, w2, w3, w4, w5, w6]。w0: 基金规模；w1: 老基金规模占比；w1: 老基金规模占比；w2: 一个月收益占比；
                w3: 三个月收益占比；w4: 六个月收益占比；w5: 一年收益占比；w6: 老基金数与基金总数比值
        :param: preprocess。是否要对数据做转换。
        '''
        if corp_df is None:
            corp_df = transform.corp_info(fund_df)
        w = np.array(w) / np.sum(w)     # 权重归一化
        # # 返回前10个最优的基金公司
        top_10_corps = self._get_target_corp(corp_df, w=radical_invest_type['corp_w'], top=10)

        # # 收集最优基金公司旗下拥有的老基金，从中选出最优的10支基金。
        top_10_funds = self._get_target_fund_from_corps(fund_df, top_10_corps.values, w=radical_invest_type['fund_w'], top=100)
        print(top_10_funds)


if __name__ == '__main__':
    pass

