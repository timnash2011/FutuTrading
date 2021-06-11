import futu as ft
import time
import Strategy

class TradeOrderTest(ft.TradeOrderHandlerBase):
    """ order update push"""
    def on_recv_rsp(self, rsp_pb):
        ret, content = super(TradeOrderTest, self).on_recv_rsp(rsp_pb)

        trade_log_file = "./trade_log/trade_log.txt"
        if ret == ft.RET_OK:
            Strategy.OrderBookTest._inv_pend
            tfile = open(trade_log_file, 'a')
            tfile.write(time.time())
            tfile.write(" ", content.to_string())
            tfile.close()
        else:
            tfile = open(trade_log_file, 'a')
            tfile.write(time.time())
            tfile.write(" TradeOrderTest error: ", content)
            tfile.close()

        return ret, content


class TradeDealTest(ft.TradeDealHandlerBase):
  """ order update push"""
  def on_recv_rsp(self, rsp_pb):
      ret, content = super(TradeDealTest, self).on_recv_rsp(rsp_pb)

      trade_log_file = "./trade_log/trade_log.txt"
      if ret == ft.RET_OK:
          tfile = open(trade_log_file, 'a')
          tfile.write(time.time())
          tfile.write(" ", content.to_string())
          tfile.close()
      else:
          tfile = open(trade_log_file, 'a')
          tfile.write(time.time())
          tfile.write(" TradeOrderTest error: ", content)
          tfile.close()

      return ret, content