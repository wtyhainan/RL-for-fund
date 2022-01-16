import os
import time


proj_path = os.path.abspath(os.path.dirname(__file__))

NOW = "2022-1-9"    # 这里设置为2022-1-9日是因为基金数据是2022-1-9日爬取的

Crawler = {
    'TTJJ': {
        'fund': {
            'url_head': 'http://fund.eastmoney.com/pingzhongdata/',     # url头
            'url_tail': '.js?v=' + time.strftime("%Y%m%d%H%M%S", time.localtime()),     # url尾部
            'keys': {
                'fund_name': 'fS_name',         # 基金名称
                'fund_code': 'fS_code',         # 基金代码
                'fund_rate': 'fund_Rate',       # 基金费率
                'stock_codes': 'stockCodes',        # 持仓股票
                'zq_codes': 'zqCodesNew',           # 持仓债券
                'profit': 'Data_netWorthTrend',     # 历史收益
            }   # 这种以键值来解析JS文件的方式是否适用到大部分网站？
        },
        'stock': {}
    }
}


InvestType = {'radical': {'corp_w': [10, 8, 7, 7, 6, 5, 4, 2],
                          'corp_w_info': ['基金规模', '老基金规模占比', '总基金数', '老基金数占比', '一个月收益', '三个月收益', '六个月收益', '一年收益'],
                          'fund_w': [10, 7, 10, 5, 10],
                          'fund_w_info': ['最大回撤', '平均回撤', '累积收益', '平均收益', '收益方差']},

              'stable': {'corp_w': [10, 8, 7, 7, 6, 5, 4, 2],
                         'corp_w_info': ['基金规模', '老基金规模占比', '总基金数', '老基金数占比', '一个月收益', '三个月收益', '六个月收益', '一年收益'],
                         'fund_w': [10, 7, 10, 5, 3],
                         'fund_w_info': ['最大回撤', '平均回撤', '累积收益', '平均收益', '收益方差']},
              }





