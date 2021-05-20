

import os
import time
import pandas as pd

# 导入futu-api
import futu as ft

import Strategy

# 读取config文件
strCurDate = time.strftime("%Y%m%d", time.localtime())
#strCurDate = '20201006'

saveFilePath = 'D:/FutuQuant_Data/' + strCurDate
if not os.path.exists(saveFilePath):
    print(saveFilePath + ' make dir ...')
    os.makedirs(saveFilePath)

curTickerDataFolder = saveFilePath + '/TickData-' + strCurDate + '/'
curOrderBookDataFolder = saveFilePath + '/OrderBookData-' + strCurDate + '/'

if not os.path.exists(curTickerDataFolder):
    print(curTickerDataFolder + ' make dir ...')
    os.makedirs(curTickerDataFolder)

if not os.path.exists(curOrderBookDataFolder):
    print(curOrderBookDataFolder + ' make dir ...')
    os.makedirs(curOrderBookDataFolder)

'''
tdf_handle = open(curTickerDataFile, 'w')
obf_handle = open(curOrderBookDataFile, 'w')
'''

market = ft.Market.HK
code_list = ['HK_FUTURE.999010', 'HK_FUTURE.999030', 'HK_FUTURE.HSImain', 'HK_FUTURE.MHImain']

config_params_folder = './config_params/'
with open(config_params_folder+'HSI_constituent_basicinfo.txt', 'r', encoding='gb18030', errors='ignore') as f:
    data = f.readlines()  # txt中所有字符串读入data

    for line in data:
        odom = line.split(',')  # 将单个数据分隔开存好
        code_list.append(odom[0])


print(code_list)

# initialize
td_col_name = None
ob_col_name = None

# 实例化行情上下文对象
quote_ctx = ft.OpenQuoteContext(host="127.0.0.1", port=11111)

# 上下文控制
quote_ctx.start()              # 开启异步数据接收
quote_ctx.set_handler(Strategy.TickerTest(curTickerDataFolder))  # 设置用于异步处理数据的回调对象(可派生支持自定义)
quote_ctx.set_handler(Strategy.OrderBookTest(curOrderBookDataFolder))

str_endtime = strCurDate+'164000'

#转换成时间数组
endtimeArray = time.strptime(str_endtime, "%Y%m%d%H%M%S")
#转换成时间戳
endtimestamp = time.mktime(endtimeArray)

if True:
    print('subscribing ...')
    # 高频数据接口
    #ret, data = quote_ctx.subscribe(code_list, [ft.SubType.QUOTE, ft.SubType.TICKER, ft.SubType.K_DAY, ft.SubType.ORDER_BOOK, ft.SubType.RT_DATA, ft.SubType.BROKER])
    ret, data = quote_ctx.subscribe(code_list, [ft.SubType.TICKER, ft.SubType.ORDER_BOOK,ft.SubType.BROKER])
    if ret != ft.RET_OK:
        print("subscribe error: " + data)
    #ret, data = quote_ctx.get_rt_ticker(code)  # 获取逐笔

    ret, data = quote_ctx.query_subscription()
    if ret == ft.RET_OK:
        print(data)
    else:
        print('error: ', data)



while time.time() < endtimestamp:
    print('trading ...')
    time.sleep(600)
else:
    print('day end .')
    # 停止异步数据接收
    quote_ctx.stop()

    # 关闭对象
    quote_ctx.close()

    '''
    tdf_handle.close()
    obf_handle.close()
    '''


