import os
import time
import json

import futu as ft

import OrderAgent as OA


class OrderBookTest(ft.OrderBookHandlerBase):
    def __init__(self, logFolder):
        self.logFolder = logFolder

        self.trd_ctx = ft.OpenHKTradeContext(host='127.0.0.1', port=11111)
        self.trd_ctx.set_handler(OA.TradeOrderTest())
        self.trd_ctx.set_handler(OA.TradeDealTest())

        self.update_config()
        #self.trd_ctx.unlock_trade()



    def on_recv_rsp(self, rsp_str):
        ret_code, data = super(OrderBookTest,self).on_recv_rsp(rsp_str)
        if ret_code != ft.RET_OK:
            print("OrderBookTest: error, msg: %s" % data)
            return ft.RET_ERROR, data

        #print("OrderBookTest ", data) # OrderBookTest自己的处理逻辑
        data["timestamp"] = time.time()

        self.update_config()
        self.update_signal(data)
        self.update_price(data)
        self.trade_action(data)

        self.print_data_log(data)

        return ft.RET_OK, data


    def update_signal(self, data):
        return 0

    def update_price(self, data):
        return 0

    def trade_action(self, data):
        return 0

    def update_config(self):
        return 0


    def print_data_log(self, data):
        logFile = self.logFolder + data["code"]
        #print(logFile + ' writing ...')

        json_str = json.dumps(data)  # dumps
        # openfile = open(self.logFile, 'a')
        with open(logFile, 'a') as openfile:
            openfile.write(json_str)
            openfile.write('\n')
        # openfile.close()


class TickerTest(ft.TickerHandlerBase):
    def __init__(self, logFolder):
        self.logFolder = logFolder
        self.col_name = None

    def on_recv_rsp(self, rsp_str):
        ret_code, data = super(TickerTest,self).on_recv_rsp(rsp_str)
        if ret_code != ft.RET_OK:
            print("TickerTest: error, msg: %s" % data)
            return ft.RET_ERROR, data

        #print("TickerTest ", data) # TickerTest自己的处理逻辑
        if self.col_name is None:
            self.col_name = data.columns.tolist()
            self.col_name.insert(0, 'timestamp')
        data = data.reindex(columns=self.col_name)
        data = data.sort_values(by=['sequence'])
        data['timestamp'] = time.time()
        logFile = self.logFolder + data['code'].get(0)
        #print(logFile + ' writing ...')
        data.to_csv(logFile, sep=',', mode='a', index=False, header=False)

        return ft.RET_OK, data