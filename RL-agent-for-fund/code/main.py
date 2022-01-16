# -*- coding: utf-8 -*-
import os

import pandas as pd

from models.selectfund import FundSelectAgent
from config import proj_path


def load_df(file, encoding='utf_8', index_col=None):
    df = pd.read_csv(file, encoding=encoding, index_col=index_col)
    return df


if __name__ == '__main__':
    file = os.path.join(proj_path, 'data\\corpInfo.csv')
    corp_df = load_df(file, encoding='gbk')

    # corp_name = ['易方达基金', '广发基金', '华夏基金', '博时基金', '南方基金', '富国基金', '招商基金', '汇添富基金',
    #    '鹏华基金', '工银瑞信基金', '中欧基金']
    #
    # corp_df = corp_df.set_index(keys='corp')
    # # print(corp_df.index)
    #
    # print(corp_df.loc[corp_name])

    fund_df = load_df(os.path.join(proj_path, 'data\\fundInfo.csv'), encoding='utf_8', index_col='index')
    agent = FundSelectAgent()
    agent(fund_df, corp_df)

