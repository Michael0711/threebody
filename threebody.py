#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-
import gevent.monkey
#gevent.monkey.patch_socket()
#gevent.monkey.patch_ssl()
gevent.monkey.patch_all()
from gevent.pool import Pool
import gevent

from api.okcoin import *
from api.btce import *
from api.tfoll import *
from api.base import *
from api.btcchina import *
from api.huobi import *
from lib.log import *

from config import accounts

class ThreeBody(object):

    TRADE_STATUS_NO = 0
    TRADE_STATUS_YES = 1
    TRADE_STATUS_LESS_CNY = 2
    TRADE_STATUS_LESS_COIN = 3
    TRADE_STATUS_LESS_DEPTH = 4
    TRADE_STATUS_TAKE_IT_EASY = 5
    trade_ltc_status = {
    }
    trade_btc_status = {
    }
    def __init__(self):
        self.okcoin = OkcoinTrade(accounts.okcoin)
        self.btce = BtceTrade(accounts.btce)
        self.tfoll = TfollTrade(accounts.tfoll)
        self.btcchina = BtcchinaTrade(accounts.btcchina)
        self.huobi = HuobiTrade(accounts.huobi)
        self.ticker = 0

        def _get_depth(name, type):
            def _wrap():
                if name == 'btce':
                    _depth = getattr(self, name).depth(symbol='%s_usd' % type)
                else:
                    _depth = getattr(self, name).depth(symbol='%s_cny' % type)
                setattr(self, "%s_%s_depth" % (name, type), _depth)
            return _wrap

        def _get_info(name):
            def _wrap():
                _info = getattr(self, name).user_info()
                setattr(self, "%s_info" % name, _info)
            return _wrap

        self.account_list = ['okcoin', 'btce', 'tfoll', 'btcchina', 'huobi']
        for account_name in self.account_list:
            setattr(self, "get_%s_ltc_depth" % account_name, _get_depth(account_name, 'ltc'))
            setattr(self, "get_%s_btc_depth" % account_name, _get_depth(account_name, 'btc'))
            setattr(self, "get_%s_info" % account_name, _get_info(account_name))

        self._concurrency = 100

    def set_trade_status(self, trade_name, type, status=False):
        getattr(self, "trade_%s_status" % type)[trade_name] = status

    def get_trade_status(self, trade_name, type):
        return getattr(self, "trade_%s_status" % type).get(trade_name, False)

    def get_status(self, depth1, depth2, name1, name2, type):
        direct1 = '%s_%s' % (name2, name1)
        rate1 = 1.0 + (depth2['buy'][0] -  depth1['sell'][0]) * 1.0 / depth1['sell'][0]
        amount1 = min(depth2['buy'][1], depth1['sell'][1])
        direct2 = '%s_%s' % (name1, name2)
        rate2 = 1.0 + (depth1['buy'][0] - depth2['sell'][0]) * 1.0 / depth2['sell'][0]
        amount2 = min(depth1['buy'][1], depth2['sell'][1])
        if name1 == 'btce' or name2 == 'btce':
            rate1 = rate1 - 0.002
            rate2 = rate2 - 0.002
        if rate1 > rate2:
            res = {
                'direct' : direct1,
                'rate' : int(rate1 * 1000) / 1000.0,
                'amount' : amount1,
                'type' : type
            }
        else:
            res = {
                'direct' : direct2,
                'rate' : int(rate2 * 1000) / 1000.0,
                'amount' : amount2,
                'type' : type
            }
        return res

    def clear_depth_and_info(self):
        for account_name in self.account_list:
            setattr(self, "%s_ltc_depth" % account_name, None)
            setattr(self, "%s_btc_depth" % account_name, None)
            setattr(self, "%s_info" % account_name, None)

    def check_depth_and_info(self):
        for account_name in self.account_list:
            ltc_depth = getattr(self, "%s_ltc_depth" % account_name)
            btc_depth = getattr(self, "%s_btc_depth" % account_name)
            info = getattr(self, "%s_info" % account_name)
            if ltc_depth == None or info == None:
                self.set_trade_status(account_name, 'ltc', False)
            else:
                self.set_trade_status(account_name, 'ltc', True)
            if btc_depth == None or info == None:
                self.set_trade_status(account_name, 'btc', False)
            else:
                self.set_trade_status(account_name, 'btc', True)

    def _get_flow_control(self, type):
        if type == 'ltc':
            return FLOW_CONTROL_LTC
        return FLOW_CONTROL_BTC 

    def check_trade(self, status):
        def _small(type):
            type_map = {
                'ltc' : 0.11,
                'btc' : 0.01
            }
            return type_map[type]
        src,dst = status['direct'].split("_")
        src_info = getattr(self, "%s_info" % src)
        dst_info = getattr(self, "%s_info" % dst) 
        type = status['type']
        dst_depth = getattr(self, "%s_%s_depth" % (dst, type)) 
        src_depth = getattr(self, '%s_%s_depth' % (src, type))
        flow_control = self._get_flow_control(type)
        flow_low = flow_control.get(status['direct'], None)

        if status['rate'] < flow_control['default'][0]:
            status['can_trade'] = self.TRADE_STATUS_NO
            return

        if flow_low and status['rate'] < flow_low[0]:
            status['can_trade'] = self.TRADE_STATUS_TAKE_IT_EASY
            return

        if src_info['funds']['free'][type] < _small(type):
            status['can_trade'] = self.TRADE_STATUS_LESS_COIN
            return
        if dst_info['funds']['free']['cny'] < dst_depth['sell'][0] * _small(type):
            status['can_trade'] = self.TRADE_STATUS_LESS_CNY
            return
        if status['amount'] < _small(type):
            status['can_trade'] = self.TRADE_STATUS_LESS_DEPTH
            return
        status['can_trade'] = self.TRADE_STATUS_YES

    def sync(self):
        self.ticker = self.ticker + 1
        self.clear_depth_and_info()
        pool1 = Pool(self._concurrency)
        for account_name in self.account_list:
            pool1.spawn(getattr(self, "get_%s_info" % account_name))
        pool1.join()
        pool2 = Pool(self._concurrency)
        for account_name in self.account_list:
            if self.ticker % 2 == 1:
                pool2.spawn(getattr(self, "get_%s_ltc_depth" % account_name))
            else:
                if account_name == 'tfoll':
                    continue
                pool2.spawn(getattr(self, "get_%s_btc_depth" % account_name))
        pool2.join()
        self.check_depth_and_info()

    def info_status(self):
        total_cny = 0
        total_ltc = 0
        total_btc = 0
        log_str = ''
        for account_name in self.account_list:
            
            if self.get_trade_status(account_name,'ltc') or \
               self.get_trade_status(account_name,'btc'):
                info = getattr(self, "%s_info" % account_name)
                trade = getattr(self, account_name)
                total_cny = total_cny + info['funds']['free']['cny']
                total_ltc = total_ltc + info['funds']['free']['ltc']
                total_btc = total_btc + info['funds']['free']['btc']
                if trade.stop:
                    log_str = '%s[%s %s %s stop] %s' % (account_name, int(info['funds']['free']['cny']),\
                                                Log.green(int(info['funds']['free']['ltc'])),\
                                                Log.green("%.3f" % info['funds']['free']['btc']),\
                                                log_str)
                else:
                    log_str = '%s[%s %s %s] %s' % (account_name, int(info['funds']['free']['cny']),\
                                                Log.green(int(info['funds']['free']['ltc'])),\
                                                Log.green("%.3f" % info['funds']['free']['btc']),\
                                                log_str)
        log_str = '[%s %s %s] %s' % (Log.green("%.1f" % total_cny), "%.1f" % total_ltc, "%.3f" % total_btc, log_str)
        Log.info(log_str)

    def search(self):
        self.status_list = []

        for i in xrange(len(self.account_list)):
            for j in xrange(len(self.account_list)):
                if j > i:
                    account1 = self.account_list[i]
                    account2 = self.account_list[j]
                    if self.get_trade_status(account1, 'ltc') and self.get_trade_status(account2, 'ltc'):
                        self.status_list.append(self.get_status(getattr(self, "%s_ltc_depth" % account1), \
                                                                getattr(self, "%s_ltc_depth" % account2), \
                                                                account1, account2, 'ltc'))
                    if self.get_trade_status(account1, 'btc') and self.get_trade_status(account2, 'btc'):
                        self.status_list.append(self.get_status(getattr(self, "%s_btc_depth" % account1), \
                                                                getattr(self, "%s_btc_depth" % account2), \
                                                                account1, account2, 'btc'))

        self.status_list.sort(lambda a, b: int((b['rate'] - a['rate']) * 10000))

        for item in self.status_list:
            self.check_trade(item)
        
        def status_log(status, text):
            if status == self.TRADE_STATUS_LESS_COIN:
                return Log.red(text)
            if status == self.TRADE_STATUS_LESS_DEPTH:
                return Log.blue(text)
            if status == self.TRADE_STATUS_LESS_CNY:
                return Log.yellow(text)
            if status == self.TRADE_STATUS_YES:
                return Log.green(text)
            return text

        btc_log_str = ''
        ltc_log_str = ''
        for item in self.status_list:
            if item['type'] == 'btc':
                item_log = "%s[%s]" % (item['direct'],  status_log(item['can_trade'], item['rate']))
                btc_log_str = "%s %s" % (btc_log_str, item_log)
            if item['type'] == 'ltc':
                item_log = "%s[%s]" % (item['direct'],  status_log(item['can_trade'], item['rate']))
                ltc_log_str = "%s %s" % (ltc_log_str, item_log)

        if ltc_log_str != '':
            Log.info("%s %s" % (Log.green('ltc'), ltc_log_str))
        if btc_log_str != '':
            Log.info("%s %s" % (Log.green("btc"), btc_log_str))

    def sell(self, trader, rate, amount, trade_name, type, time=0):
        try:
            if time == 5:
                Log.error("SeriousErrorException timeout[%s], trade_name[%s], rate[%s], amount[%s], type[%s]" % (time, trade_name, rate, amount, type))
                raise SeriousErrorException("timeout[%s], trade_name[%s], rate[%s], amount[%s], type[%s]" % (time, trade_name, rate, amount, type))
            Log.info("start sell trade[%s %s] rate[%s] amount[%s] trade[%s]" % (time, type, rate, amount, trade_name))
            if trade_name == 'btce':
                trader.trade(type='sell', rate=int(rate * 10) / 10.0, \
                                amount=amount, symbol='%s_usd' % type)
            else:
                trader.trade(type='sell', rate=int(rate * 10) / 10.0, \
                                amount=amount, symbol='%s_cny' % type)
        except SeriousErrorException as e:
            trader.set_stop(True)
        except TradeFailedException, e:
            if str(e).find("timed out") != -1:
                Log.error("TradeFailedException timeout[%s], trade_name[%s], rate[%s], amount[%s], type[%s]" % (time, trade_name, rate, amount, type))
                gevent.sleep(0.5)
                self.sell(trader, rate, amount, trade_name, type, time=time+1)
            else:
                Log.error("TradeFailedException error[%s]" % e)

    def buy(self, trader, rate, amount, trade_name, type, time=0):
        try:
            if time == 5:
                Log.error("SeriousErrorException timeout[%s], trade_name[%s], rate[%s], amount[%s], type[%s]" % (time, trade_name, rate, amount, type))
                raise SeriousErrorException("timeout[%s], trade_name[%s], rate[%s], amount[%s], type[%s]" % (time, trade_name, rate, amount, type))
            Log.info("start buy trade[%s %s] rate[%s] amount[%s] trade[%s]" % (time, type, rate, amount, trade_name))
            if trade_name == 'btce':
                trader.trade(type='buy', rate=int(rate * 10) / 10.0, \
                                amount=amount * 1.002, symbol='%s_usd' % type)
            else:
                trader.trade(type='buy', rate=int(rate * 10) / 10.0, \
                                amount=amount, symbol='%s_cny' % type)
        except SeriousErrorException as e:
            trader.set_stop(True)
        except TradeFailedException, e:
            if str(e).find("timed out") != -1:
                Log.error("TradeFailedException timeout[%s], trade_name[%s], rate[%s], amount[%s], type[%s]" % (time, trade_name, rate, amount, type))
                gevent.sleep(0.5)
                self.buy(trader, rate, amount, trade_name, type, time=time+1)
            else:
                Log.error("TradeFailedException error[%s]" % e)


    def trade(self):
        MORE = 1.04
        LESS = 0.96
        for item in self.status_list:
            if item['can_trade'] == self.TRADE_STATUS_YES:
                src,dst = item['direct'].split("_")
                type = item['type']
                src_depth = getattr(self, "%s_%s_depth" % (src, type))
                dst_depth = getattr(self, "%s_%s_depth" % (dst, type))
                src_info = getattr(self, "%s_info" % src)
                dst_info = getattr(self, "%s_info" % dst)
                src_trade = getattr(self, src)
                dst_trade = getattr(self, dst)
            
                flow_control = self._get_flow_control(type)
                flow_low = flow_control.get(item['direct'], None)
                amount = flow_low and flow_low[1] or flow_control['default'][1]

                amount = min(amount, item['amount'])
                amount = min(amount, src_info['funds']['free'][type])
                amount = min(amount, dst_info['funds']['free']['cny'] / (dst_depth['sell'][0] * MORE) )

                if type == 'ltc':
                    amount = int(amount * 10) / 10.0
                else:
                    amount = int(amount * 100) / 100.0

                if src_trade.stop or dst_trade.stop:
                    continue

                Log.info("trade[%s %s %s] src_depth[%s] dst_depth[%s]" % (type, item['direct'], amount, src_depth, dst_depth))

                pool = Pool(self._concurrency)
                pool.spawn(self.sell, src_trade, src_depth['buy'][0] * LESS, amount, src, type)
                pool.spawn(self.buy, dst_trade, dst_depth['sell'][0] * MORE, amount, dst, type)
                pool.join()

                if src == 'tfoll' or dst == 'tfoll':
                    time.sleep(0.5)
                break

            else:
                continue



    def run(self):
        Log.init("threebody.log")
        pre = int(time.time())
        while True:
            try:
                Log.reset_id('threebody')
                cur = int(time.time())
                print '-----------------------%s-----------------------' % (cur - pre)
                self.sync()
                self.info_status()
                self.search()
                self.trade()
                pre = cur
            except SeriousErrorException as e:
                Log.error(e)
                break
            except Exception as e:
                Log.error(e)

if __name__ == '__main__':
    three_body = ThreeBody()
    three_body.run()

    #btcchina = BtcchinaTrade(accounts.btcchina)
    #print btcchina.user_info()
    #print btcchina.depth(symbol='ltc_cny')
   # pool = Pool(2)
   # pool.spawn(btcchina.user_info)
   # pool.spawn(btcchina.depth, 'ltc_cny')
   # pool.join()
