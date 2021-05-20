import futu as ft

class TradeOrderTest(ft.TradeOrderHandlerBase):
  """ order update push"""
  def on_recv_rsp(self, rsp_pb):
      ret, content = super(TradeOrderTest, self).on_recv_rsp(rsp_pb)

      if ret == ft.RET_OK:
          print("* TradeOrderTest content={}\n".format(content))

      return ret, content


class TradeDealTest(ft.TradeDealHandlerBase):
  """ order update push"""
  def on_recv_rsp(self, rsp_pb):
      ret, content = super(TradeDealTest, self).on_recv_rsp(rsp_pb)

      if ret == ft.RET_OK:
          print("TradeDealTest content={}".format(content))

      return ret, content