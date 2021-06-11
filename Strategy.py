import os
import time
import datetime
import json
import numpy as np
import scipy.io as scio

import futu as ft

import OrderAgent as OA
import factor_lib as fl


class OrderBookTest(ft.OrderBookHandlerBase):
    # 因为要在OA里面变更inv、inv_pend，所以定义一个类变量
    _inv = 0
    _inv_pend = 0

    def __init__(self, logFolder):
        self.logFolder = logFolder

        self.trd_ctx = ft.OpenHKTradeContext(host='127.0.0.1', port=11111)
        self.trd_ctx.set_handler(OA.TradeOrderTest())
        self.trd_ctx.set_handler(OA.TradeDealTest())

        #self.update_config()
        #self.trd_ctx.unlock_trade()

        str_stt_time = time.strftime("%Y%m%d",time.localtime()) + '093000'
        self.stt_time = time.mktime(datetime.datetime.strptime(str_stt_time, '%Y%m%d%H%M%S').timetuple())

        self.mybid = 0
        self.myask = 40000
        self.inv = 0
        self.inv_pend = 0

        self.final_ind = 0
        self.testind1 = 0
        self.testind2 = 0
        self.testind4 = 0
        self.nnind1 = 0
        self.nnind2 = 0

        self.midprice = 0
        self.baprice1 = 0
        self.ask1 = 0
        self.bid1 = 0
        self.asize1 = 0
        self.bsize1 = 0
        self.timestamp = 0
        self.nTick = 0

        self.prev_midprice = 0
        self.prev_baprice1 = 0
        self.prev_ask1 = 0
        self.prev_bid1 = 0
        self.prev_timestamp = 0
        self.daystt_timestamp = 0
        self.prev_dataMatrix = np.zeros([100, 12], dtype=float, order='C')


    def on_recv_rsp(self, rsp_str):
        ret_code, data = super(OrderBookTest,self).on_recv_rsp(rsp_str)
        if ret_code != ft.RET_OK:
            print("OrderBookTest: error, msg: %s" % data)
            return ft.RET_ERROR, data

        #print("OrderBookTest ", data) # OrderBookTest自己的处理逻辑
        data["timestamp"] = time.time()

        if data["code"] == "HK.999030" and data["timestamp"] >= self.stt_time:
            self.timestamp = data["timestamp"]
            if self.nTick == 0:
                self.daystt_timestamp = data["timestamp"]

            self.nTick += 1

            self.update_config()
            self.update_signal(data)
            self.update_inventory()
            self.update_price(data)

            if self.nTick >= 100:
                self.trade_action(data)

            self.prepare_data(data)

        self.print_data_log(data)

        return ft.RET_OK, data


    def update_signal(self, data):
        self.final_ind = 0

        self.bid1 = data['Bid'][0][0]
        self.bsize1 = data['Bid'][0][1]
        bn1 = data['Bid'][0][2]
        self.ask1 = data['Ask'][0][0]
        self.asize1 = data['Ask'][0][1]
        an1 = data['Ask'][0][2]

        self.midprice = (self.bid1 + self.ask1)/2
        self.baspread = self.ask1 - self.bid1
        self.baprice1 = (self.bid1 * self.asize1 + self.ask1 * self.bsize1) / (self.bsize1+self.asize1)
        criterian1 = (self.bid1 == self.prev_bid1 and self.ask1 == self.prev_ask1)

        if self.beta[3] > 0 or self.beta[4] > 0:
            nnInput = np.zeros([1208, 1], dtype=float, order='C')

        if self.beta[0] > 0:
            self.testind1 = fl.getTestind1(self.midprice, self.baprice1, self.baspread)
            self.final_ind += self.testind1*self.beta[0]

        if self.beta[1] > 0:
            self.testind2 = fl.getTestind2(self.testind2, self.baprice1-self.baprice1, self.baspread, criterian1)
            self.final_ind += self.testind2 * self.beta[1]

        if self.beta[2] > 0:
            self.testind4 = fl.getTestind4(self.testind4, self.midprice-self.prev_midprice, criterian1)
            self.final_ind += self.testind4 * self.beta[2]

        if self.beta[3] > 0:
            self.nnind1 = fl.getNNind1(self.nnModel_1jump, nnInput)
            self.final_ind += self.nnind1 * self.beta[3]

        if self.beta[4] > 0:
            self.nnind2 = fl.getNNind1(self.nnModel_wider, nnInput)
            self.final_ind += self.nnind2 * self.beta[4]

    def update_inventory(self):
        self.inv = OrderBookTest._inv
        self.inv_pend = OrderBookTest._inv_pend

    def update_price(self, data):
        self.mybid = self.midprice + self.final_ind - self.pos_penalty * (self.inv+self.inv_pend) - self.entry_level - self.fix_comm - self.float_comm*self.ask1
        self.myask = self.midprice + self.final_ind - self.pos_penalty * (self.inv+self.inv_pend) + self.entry_level + self.fix_comm + self.float_comm*self.bid1

    def trade_action(self, data):
        trade_log_file = "./trade_log/trade_log.txt"
        if self.mybid >= self.ask1 and self.baspread <= self.spread_limit:
            tradesize = min(self.asize1, self.max_trade_size*self.min_unit, self.max_long_pos*self.min_unit - self.inv - self.inv_pend)
            if tradesize > 0:
                ret, ret_data = self.trd_ctx.place_order(price=self.ask1, qty=tradesize, code=data["code"], trd_side=ft.TrdSide.BUY, order_type=ft.OrderType.SPECIAL_LIMIT, trd_env=ft.TrdEnv.SIMULATE)
                if ret == ft.RET_OK:
                    self.inv_pend += tradesize
                    OrderBookTest._inv_pend += tradesize

                    tfile = open(trade_log_file, 'a')
                    tfile.write(time.time())
                    tfile.write(" ", ret_data.to_string())
                    tfile.close()

                else:
                    tfile = open(trade_log_file, 'a')
                    tfile.write(time.time())
                    tfile.write(" place_order error: ", ret_data)
                    tfile.close()

        if self.myask <= self.bid1 and self.baspread <= self.spread_limit:
            tradesize = min(self.bsize1, self.max_trade_size*self.min_unit, self.max_short_pos*self.min_unit + self.inv + self.inv_pend)
            if tradesize > 0:
                ret, ret_data = self.trd_ctx.place_order(price=self.bid1, qty=tradesize, code=data["code"], trd_side=ft.TrdSide.SELL, order_type=ft.OrderType.SPECIAL_LIMIT, trd_env=ft.TrdEnv.SIMULATE)
                if ret == ft.RET_OK:
                    self.inv_pend -= tradesize
                    OrderBookTest._inv_pend -= tradesize

                    tfile = open(trade_log_file, 'a')
                    tfile.write(time.time())
                    tfile.write(" ", ret_data.to_string())
                    tfile.close()

                else:
                    tfile = open(trade_log_file, 'a')
                    tfile.write(time.time())
                    tfile.write(" place_order error: ", ret_data)
                    tfile.close()

    def prepare_data(self, data):
        self.prev_midprice = self.midprice
        self.prev_baprice1 = self.baprice1
        self.prev_ask1 = self.ask1
        self.prev_bid1 = self.bid1
        self.prev_timestamp = self.timestamp

    def update_config(self):
        update_flag_file = "./config/update_flag"
        trade_param_file = "./config/trade_params"
        with open(update_flag_file, 'r') as f:
            for line in f:
                k = line.split("=")[0]
                v = line.split("=")[1]
                if v == 1:
                    # update config params
                    with open(trade_param_file, 'r') as f2:
                        for line in f2:
                            param_key = line.split("=")[0]
                            param_value = line.split("=")[1]
                            if param_key == "fix_comm":
                                self.fix_comm = param_value
                            if param_key == "float_comm":
                                self.float_comm = param_value
                            if param_key == "min_unit":
                                self.min_unit = param_value
                            if param_key == "max_trade_size":
                                self.max_trade_size = param_value
                            if param_key == "max_long_pos":
                                self.max_long_pos = param_value
                            if param_key == "max_short_pos":
                                self.max_short_pos = param_value
                            if param_key == "entry_level":
                                self.entry_level = param_value
                            if param_key == "spread_limit":
                                self.spread_limit = param_value
                            if param_key == "pos_penalty":
                                self.pos_penalty = param_value
                            if param_key == "half_spread":
                                self.half_spread = param_value

                    # update nnModel weight
                    nnMatFile = "./config/nnModel_1jump.mat"
                    data = scio.loadmat(nnMatFile)
                    W = data['nnModel']['W'][0][0][0]
                    self.nnModel_1jump.w1 = W[0]
                    self.nnModel_1jump.w2 = W[1]
                    self.nnModel_1jump.w3 = W[2]
                    self.nnModel_1jump.w4 = W[3]

                    nnMatFile = "./config/nnModel_wider.mat"
                    data = scio.loadmat(nnMatFile)
                    W = data['nnModel']['W'][0][0][0]
                    self.nnModel_wider.w1 = W[0]
                    self.nnModel_wider.w2 = W[1]
                    self.nnModel_wider.w3 = W[2]
                    self.nnModel_wider.w4 = W[3]

                    betaFile = "./config/beta.txt"
                    self.beta = np.loadtxt(betaFile)



        if v == 1:
            with open(update_flag_file, 'w') as f:
                f.write(k + "=0")






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