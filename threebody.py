#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-
import gevent.monkey
gevent.monkey.patch_socket()
gevent.monkey.patch_ssl()
from gevent.pool import Pool

from api.okcoin import *
from api.btce import *
from api.tfoll import *
from lib.log import *

from config import accounts

class ThreeBody(object):

    TRADE_STATUS_NO = 0
    TRADE_STATUS_YES = 1
    TRADE_STATUS_LESS_CNY = 2
    TRADE_STATUS_LESS_LTC = 3
    TRADE_STATUS_LESS_DEPTH = 4
    trade_status = {
    }

    def __init__(self):
        self.okcoin = OkcoinTrade(accounts.okcoin)
        self.btce = BtceTrade(accounts.btce)
        self.tfoll = TfollTrade(accounts.tfoll)
        self.account_list = ['okcoin', 'btce', 'tfoll']
        self._concurrency = 10

    def set_trade_status(self, trade_name, status=False):
        self.trade_status[trade_name] = status

    def get_trade_status(self, trade_name):
        return self.trade_status[trade_name]

    def get_status(self, depth1, depth2, name1, name2):
        direct1 = '%s_%s' % (name2, name1)
        rate1 = 1.0 + (depth2['buy'][0] -  depth1['sell'][0]) * 1.0 / depth1['sell'][0]
        ltc_amount1 = min(depth2['buy'][1], depth1['sell'][1])
        direct2 = '%s_%s' % (name1, name2)
        rate2 = 1.0 + (depth1['buy'][0] - depth2['sell'][0]) * 1.0 / depth2['sell'][0]
        ltc_amount2 = min(depth1['buy'][1], depth2['sell'][1])
        if name1 == 'btce' or name2 == 'btce':
            rate1 = rate1 - 0.002
            rate2 = rate2 - 0.002
        if rate1 > rate2:
            res = {
                'direct' : direct1,
                'rate' : rate1,
                'ltc_amount' : ltc_amount1,
            }
        else:
            res = {
                'direct' : direct2,
                'rate' : rate2,
                'ltc_amount' : ltc_amount2,
            }
        return res

    def get_okcoin_info(self):
        self.okcoin_info = self.okcoin.user_info()
        self.okcoin_info['funds']['free']['ltc'] = float(self.okcoin_info['funds']['free']['ltc'])
        self.okcoin_info['funds']['free']['btc'] = float(self.okcoin_info['funds']['free']['btc'])
        self.okcoin_info['funds']['free']['cny'] = float(self.okcoin_info['funds']['free']['cny'])

    def get_btce_info(self):
        self.btce_info = self.btce.user_info()
        self.btce_info['funds']['free']['ltc'] = float(self.btce_info['funds']['free']['ltc'])
        self.btce_info['funds']['free']['btc'] = float(self.btce_info['funds']['free']['btc'])
        self.btce_info['funds']['free']['usd'] = float(self.btce_info['funds']['free']['usd'])
        self.btce_info['funds']['free']['cny'] = self.btce_info['funds']['free']['usd'] * USD_TO_RMB

    def get_tfoll_info(self):
        self.tfoll_info = self.tfoll.user_info()
        self.tfoll_info['funds']['free']['ltc'] = float(self.tfoll_info['funds']['free']['ltc'])
        self.tfoll_info['funds']['free']['btc'] = float(self.tfoll_info['funds']['free']['btc'])
        self.tfoll_info['funds']['free']['cny'] = float(self.tfoll_info['funds']['free']['cny'])

    def get_okcoin_depth(self):
        self.okcoin_depth = self.okcoin.depth(symbol='ltc_cny')
        self.okcoin_depth['sell'][0] = float(self.okcoin_depth['sell'][0])
        self.okcoin_depth['sell'][1] = float(self.okcoin_depth['sell'][1])
        self.okcoin_depth['buy'][0] = float(self.okcoin_depth['buy'][0])
        self.okcoin_depth['buy'][1] = float(self.okcoin_depth['buy'][1])

    def get_btce_depth(self):
        self.btce_depth = self.btce.depth(symbol='ltc_usd')
        self.btce_depth['sell'][0] = float(self.btce_depth['sell'][0])
        self.btce_depth['sell'][1] = float(self.btce_depth['sell'][1])
        self.btce_depth['buy'][0] = float(self.btce_depth['buy'][0])
        self.btce_depth['buy'][1] = float(self.btce_depth['buy'][1])

        self.btce_depth['sell'][0] = self.btce_depth['sell'][0] * USD_TO_RMB
        self.btce_depth['buy'][0] = self.btce_depth['buy'][0] * USD_TO_RMB

    def get_tfoll_depth(self):
        self.tfoll_depth = self.tfoll.depth(symbol='ltc_cny')
        self.tfoll_depth['sell'][0] = float(self.tfoll_depth['sell'][0])
        self.tfoll_depth['sell'][1] = float(self.tfoll_depth['sell'][1])
        self.tfoll_depth['buy'][0] = float(self.tfoll_depth['buy'][0])
        self.tfoll_depth['buy'][1] = float(self.tfoll_depth['buy'][1])

    def clear_depth_and_info(self):
        self.okcoin_depth = None
        self.btce_depth = None
        self.tfoll_depth = None
        self.okcoin_info = None
        self.btce_info = None
        self.tfoll_info = None

    def check_depth_and_info(self):
        if self.okcoin_depth == None or self.okcoin_info == None:
            self.set_trade_status('okcoin', False)
        else:
            self.set_trade_status('okcoin', True)
        if self.btce_depth == None or self.btce_info == None:
            self.set_trade_status('btce', False)
        else:
            self.set_trade_status('btce', True)
        if self.tfoll_depth == None or self.tfoll_info == None:
            self.set_trade_status('tfoll', False)
        else:
            self.set_trade_status('tfoll', True)

    def check_trade(self, status):
        src,dst = status['direct'].split("_")
        src_depth = getattr(self, '%s_depth' % src)
        src_info = getattr(self, "%s_info" % src)
        dst_depth = getattr(self, "%s_depth" % dst) 
        dst_info = getattr(self, "%s_info" % dst) 
        SMALL_LTC = 0.11
        if status['rate'] < 1.001:
            status['can_trade'] = self.TRADE_STATUS_NO
            return
        if src_info['funds']['free']['ltc'] < SMALL_LTC:
            status['can_trade'] = self.TRADE_STATUS_LESS_LTC
            return
        if dst_info['funds']['free']['cny'] < dst_depth['sell'][0] * SMALL_LTC:
            status['can_trade'] = self.TRADE_STATUS_LESS_CNY
            return
        if status['ltc_amount'] < SMALL_LTC:
            status['can_trade'] = self.TRADE_STATUS_LESS_DEPTH
            return
        status['can_trade'] = self.TRADE_STATUS_YES

    def sync(self):
        self.clear_depth_and_info()
        pool = Pool(self._concurrency)
        pool.spawn(self.get_tfoll_info)
        pool.spawn(self.get_okcoin_info)
        pool.spawn(self.get_btce_info)
        pool.spawn(self.get_okcoin_depth)
        pool.spawn(self.get_btce_depth)
        pool.spawn(self.get_tfoll_depth)
        pool.join()
        self.check_depth_and_info()

    def info_status(self):
        total_cny = 0
        total_ltc = 0
        total_btc = 0
        log_str = ''
        for account_name in self.account_list:
            if self.get_trade_status(account_name):
                info = getattr(self, "%s_info" % account_name)
                total_cny = total_cny + info['funds']['free']['cny']
                total_ltc = total_ltc + info['funds']['free']['ltc']
                total_btc = total_btc + info['funds']['free']['btc']
                log_str = '%s[%s,%s,%s] %s' % (account_name, info['funds']['free']['cny'],\
                                            info['funds']['free']['ltc'],\
                                            info['funds']['free']['btc'],\
                                            log_str)
        log_str = '[%s,%s,%s] %s' % (Log.green(total_cny), total_ltc, total_btc, log_str)
        Log.info(log_str)

    def search(self):
        self.status_list = []
        if self.get_trade_status('okcoin') and self.get_trade_status('btce'):
            self.status_list.append(self.get_status(self.okcoin_depth, self.btce_depth, 'okcoin', 'btce'))
        if self.get_trade_status("btce") and self.get_trade_status("tfoll"):
            self.status_list.append(self.get_status(self.btce_depth, self.tfoll_depth, 'btce', 'tfoll'))
        if self.get_trade_status("okcoin") and self.get_trade_status("tfoll"):
            self.status_list.append(self.get_status(self.okcoin_depth, self.tfoll_depth, 'okcoin', 'tfoll'))
        self.status_list.sort(lambda a, b: int((b['rate'] - a['rate']) * 10000))

        for item in self.status_list:
            self.check_trade(item)
        
        def status_log(status, text):
            if status == self.TRADE_STATUS_LESS_LTC:
                return Log.red(text)
            if status == self.TRADE_STATUS_LESS_DEPTH:
                return Log.blue(text)
            if status == self.TRADE_STATUS_LESS_CNY:
                return Log.yellow(text)
            if status == self.TRADE_STATUS_YES:
                return Log.green(text)
            return text

        log_str = ''
        for item in self.status_list:
            item_log = "%s[%s]" % (item['direct'],  status_log(item['can_trade'], item['rate']))
            log_str = "%s %s" % (log_str, item_log)
        Log.info(log_str)

    def trade(self):
        for item in self.status_list:
            if item['can_trade'] == self.TRADE_STATUS_YES:
                src,dst = item['direct'].split("_")
                src_depth = getattr(self, "%s_depth" % src)
                dst_depth = getattr(self, "%s_depth" % dst)
                src_info = getattr(self, "%s_info" % src)
                dst_info = getattr(self, "%s_info" % dst)
                src_trade = getattr(self, src)
                dst_trade = getattr(self, dst)
                amount = 2
                amount = min(amount, item['ltc_amount'])
                amount = min(amount, src_info['funds']['free']['ltc'])
                amount = min(amount, dst_info['funds']['free']['cny'] / dst_depth['sell'][0])

                if src == 'btce':
                    src_trade.trade(type='sell', rate=src_depth['buy'][0]  / USD_TO_RMB * 0.9, \
                                    amount=amount, symbol='ltc_usd')
                else:
                    src_trade.trade(type='sell', rate=src_depth['buy'][0] * 0.9, \
                                    amount=amount, symbol='ltc_cny')
                if dst == 'btce':
                    dst_trade.trade(type='buy', rate=dst_depth['sell'][0]  / USD_TO_RMB * 1.1, \
                                    amount=amount * 1.002, symbol='ltc_usd')
                else:
                    dst_trade.trade(type='buy', rate=dst_depth['sell'][0] * 1.1, \
                                    amount=amount, symbol='ltc_cny')

                Log.info("trade[%s %s] src_depth[%s] dst_depth[%s]" % (item['direct'], amount, src_depth, dst_depth))
                break
            else:
                continue



    def run(self):
        Log.init()
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
            except Exception as e:
                Log.error(e)

if __name__ == '__main__':
    three_body = ThreeBody()
    three_body.run()
