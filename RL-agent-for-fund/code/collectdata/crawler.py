import requests
import time
import execjs
from bs4 import BeautifulSoup
import numpy as np
from tqdm import tqdm

TIMELEN = 10


class FundInfo(object):
    def __init__(self, code, name, rate, ftype, fsize, date, manager, department, worthTrend, stockCodes, zqCodes):
        self.code = code    # 代码
        self.name = name    # 名称
        self.rate = rate    # 费率
        self.ftype = ftype  # 类型
        self.fsize = fsize  # 规模
        self.date = date    # 成立日
        self.manager = manager  # 基金经理
        self.department = department    # 基金所属部门
        self.worthTrend = worthTrend    # 单位净值
        self.stockCodes = stockCodes    # 前10股票持仓
        self.zqCodes = zqCodes  # 前10债券持仓

    def __str__(self):
        return f'code: {self.code}, \nname: {self.name}, \nrate: {self.rate}, \nftype: {self.ftype}, \nfsize: {self.fsize}, \ndate: {self.date}, \nmanager: {self.manager}, ' \
               f'\ndepartment: {self.department}, \nstockCodes: {self.stockCodes}, \nzqCodes: {self.zqCodes}, \nworthTrend: {self.worthTrend}'

    @property
    def baseinfo(self):
        info = []
        keys = []
        for k, v in self.__dict__.items():
            if k == 'worthTrend':
                continue
            info.append(v)
            keys.append(k)
        return keys, info

    @property
    def trend(self):
        return self.worthTrend


def get_fund_info(fscode):
    ''' ftype, fsize, fopt '''
    url = 'http://fund.eastmoney.com/' + fscode + '.html'
    res = requests.get(url)
    res.encoding = 'utf-8'
    page = res.text
    soup = BeautifulSoup(page, 'lxml', from_encoding='utf-8')

    info_tags = soup.find('div', attrs={'class': 'infoOfFund'}).find('table')
    info_tags = [i for i in info_tags if i.name is not None]
    ss = ''
    for tag in info_tags:
        childen = [i for i in tag.descendants if i.name is None]
        for child in childen:
            ss += child.string

    info = {'基金类型': None, '基金经理': None, '基金规模': None, '成 立 日': None, '管 理 人': None, '基金评级': None}
    valid_info = ['基金类型：', '基金规模：', '基金经理：', '成 立 日：', '管 理 人：', '基金评级：']
    key = None
    for v in valid_info:
        s = ss.strip(' ').split(v)
        ss = s[1]
        val = s[0].strip(' ')
        if key == None:
            key = v.split('：')[0]
            continue
        info[key] = val
        key = v.split('：')[0]
        val = s[0].strip(' ')
    return info


def getUrl(fscode):
    head = 'http://fund.eastmoney.com/pingzhongdata/'
    tail = '.js?v=' + time.strftime("%Y%m%d%H%M%S", time.localtime())
    return head + fscode + tail


def getTime(t):
    t = time.localtime(t)
    otherStyleTime = time.strftime("%Y-%m-%d", t)
    return otherStyleTime


def to_string(data: list, type_=' '):
    return type_.join(data)


def getWorth(fscode) -> FundInfo:
    # 用requests获取到对应的文件
    content = requests.get(getUrl(fscode))
    # 使用execjs获取到相应的数据
    jsContent = execjs.compile(content.text)
    name = jsContent.eval('fS_name')
    code = jsContent.eval('fS_code')

    fund_rate = jsContent.eval('fund_Rate') if jsContent.eval('fund_Rate') != '' else '0.0'     # 申购费率
    stockCodes = jsContent.eval('stockCodes') if jsContent.eval('stockCodes') != '' else '~'   # 持仓股票
    zqCodesNew = jsContent.eval('zqCodesNew') if jsContent.eval('zqCodesNew') != '' else '~'  # 持仓债券

    if len(stockCodes) == 0:
        stockCodes = '~~'
    if len(zqCodesNew) == 0:
        zqCodesNew = '~'

    if isinstance(stockCodes, str):
        stockCodes = [stockCodes]
    if isinstance(zqCodesNew, str):
        zqCodesNew = [zqCodesNew]

    stockCodes = [i[0:-1] for i in stockCodes]

    stockCodes = to_string(stockCodes)
    zqCodesNew = to_string(zqCodesNew)

    time.sleep(0.5)     # 暂停0.5秒，防止被禁

    fund_info = get_fund_info(fscode)   # 获取基金基本信息
    # 单位净值走势
    netWorthTrend = jsContent.eval('Data_netWorthTrend')
    netWorth_val = []
    for dayWorth in netWorthTrend:
        t = str(dayWorth['x'])[0:TIMELEN]
        ts = getTime(int(t))    # 测试时间转换是否正确
        y = t + '-' + str(dayWorth['y'])
        netWorth_val.append(y)

    netWorth_val = to_string(netWorth_val)

    info = FundInfo(code=code, name=name, rate=fund_rate,
                    ftype=fund_info['基金类型'], fsize=fund_info['基金规模'],
                    date=fund_info['成 立 日'], manager=fund_info['基金经理'],
                    department=fund_info['管 理 人'], worthTrend=netWorth_val, stockCodes=stockCodes, zqCodes=zqCodesNew)
    return info


def save_to_file(code, data):
    file = './data/worthTrend/' + code + '.txt'
    with open(file, 'w', encoding='utf-8') as f:
        f.write(data)


def crapper(fscodes):
    base_f = open('./data/fundsInfo.txt', 'a+', encoding='utf-8')
    error_f = open('./data/errorFundData.txt', 'a+', encoding='utf-8')
    right_f = open('./data/rightFundData.txt', 'a+', encoding='utf-8')

    funds_code = np.array(fscodes)

    for i in tqdm(range(len(funds_code))):
        fscode = funds_code[i]
        try:
            fund_info = getWorth(fscode)

            _, fund_base_info = fund_info.baseinfo
            base_f.write('***'.join(fund_base_info) + '\n')
            save_to_file(fscode, fund_info.worthTrend)  # 保存基金历史单位净值数据
            right_f.write(f'current number: {i}-fund code: {fscode} ** ')
            # print(f'fscode: {fscode} \n')

        except Exception as e:
            # error_f.write(f'current number: {i}-fund code: {fscode} ** ')
            print(f'error --------- fscode: {fscode}, e: {e} \n')
            continue

    base_f.close()
    error_f.close()
    right_f.close()


if __name__ == '__main__':

    # fscode = '980003'
    # info = getWorth(fscode)
    # worthTrend = info.worthTrend
    # keys, values = info.baseinfo
    # base_f = open('funds_info.txt', 'w', encoding='utf-8')
    # worth_f = open('funds_worth.txt', 'w', encoding='utf-8')
    #
    # values = '***'.join(values)
    #
    # save_to_file(fscode, worthTrend)
    # base_f.close()
    # worth_f.close()
    # # print(info.worthTrend)
    # print(info.baseinfo)

############################


    # base_f = open('./data/fundsInfo.txt', 'a+', encoding='utf-8')
    # error_f = open('./data/errorFundData.txt', 'a+', encoding='utf-8')
    # right_f = open('./data/rightFundData.txt', 'a+', encoding='utf-8')
    #
    # funds_code = []
    # with open('./data/fundsCode.txt', 'r', encoding='utf-8') as f:
    #     for line in f.readlines():
    #         res = line.split('   ')
    #         funds_code.append(res[0].strip('"'))
    #
    # funds_code = np.array(funds_code)
    #
    # for i in tqdm(range(len(funds_code))):
    #     if i < 12406:
    #         continue
    #     fscode = funds_code[i]
    #     if fscode != '970109':
    #         continue
    #     try:
    #         fund_info = getWorth(fscode)
    #
    #         _, fund_base_info = fund_info.baseinfo
    #         base_f.write('***'.join(fund_base_info) + '\n')
    # #         save_to_file(fscode, fund_info.worthTrend)  # 保存基金历史单位净值数据
    # #         right_f.write(f'current number: {i}-fund code: {fscode} ** ')
    #     except Exception as e:
    #         # error_f.write(f'current number: {i}-fund code: {fscode} ** ')
    #         print(e)
    #         continue
    #
    # base_f.close()
    # error_f.close()
    # right_f.close()
############################

    # with open('./data/errorFundData.txt', 'r', encoding='utf-8') as f:
    #     data = f.readline()
    #     errors = data.strip(' ').split('**')
    #
    # fscodes = []
    # for error in errors:
    #     if not error:
    #         continue
    #     res = error.strip(' ').split('-')
    #     fscode = res[1].strip(' ').split(':')[1].strip(' ')
    #     fscodes.append(fscode)
    #
    # fscodes = fscodes[::-1]
    # print(fscodes)
    # crapper(fscodes)

#########################

    from config import proj_path
    print(proj_path)

    # file = './data/worthTrend/000015.txt'
    # with open(file, 'r', encoding='utf-8') as f:
    #     data = f.readline()
    #     data = data.strip(' ').split(' ')
    # print(data)



