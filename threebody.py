#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

from api.okcoin import *
from api.btce import *
from api.tfoll import *

from config import accounts

import gevent.monkey
gevent.monkey.patch_socket()

from gevent.pool import Pool

class ThreeBody(object):

    TRADE_STATUS_NO = 0
    TRADE_STATUS_YES = 1
    TRADE_STATUS_LESS_CNY = 2
    TRADE_STATUS_LESS_LTC = 3
    TRADE_STATUS_LESS_DEPTH = 4

    def __init__(self):
        self.okcoin = OkcoinTrade(accounts.okcoin)
        #self.btce = BtceTrade(accounts.btce)
        self.tfoll = TfollTrade(accounts.tfoll)
        self._concurrency = 3

    def get_status(self, depth1, depth2, name1, name2):
        direct1 = '%s_%s' % (name2, name1)
        rate1 = 1.0 + (depth2['buy'][0] -  depth1['sell'][0]) * 1.0 / depth1['sell'][0]
        direct2 = '%s_%s' % (name1, name2)
        rate2 = 1.0 + (depth1['buy'][0] - depth2['sell'][0]) * 1.0 / depth2['sell'][0]

        if name1 == 'btce' or name2 == 'btce':
            rate1 = rate1 - 0.002
            rate2 = rate2 - 0.002

        if rate1 > rate2:
            res = {
                'direct' : direct1,
                'rate' : rate1,
            }
        else:
            res = {
                'direct' : direct2,
                'rate' : rate2
            }
        return res

    def get_okcoin_info(self):
        self.ok_info = self.okcoin.user_info()
        print 1
    def get_btce_info(self):
        self.btce_info = self.btce.user_info()
        print 2
    def get_tfoll_info(self):
        self.tfoll_info = self.tfoll.user_info()
        print 3

    def get_user_info(self):
        pool = Pool(self._concurrency)
        pool.spawn(self.get_tfoll_info)
        pool.spawn(self.get_okcoin_info)
        #pool.spawn(self.get_btce_info)
        pool.join()


    def check_trade(self, status):
        if status['rate'] < 1.001:
            status['can_trade'] = self.TRADE_STATUS_NO
            return
        src,dst = status['direct'].split("_")
        if getattr(self, '%s_depth' % src):
            pass
    def get_okcoin_depth(self):
        self.ok_depth = self.okcoin.depth(symbol='ltc_cny')
    def get_btce_depth(self):
        self.btce_depth = self.btce.depth(symbol='ltc_usd')
    def get_tfoll_depth(self):
        self.tfoll_depth = self.tfoll.depth(symbol='ltc_cny')

    def search(self):
        pool = Pool(self._concurrency)
        pool.spawn(self.get_okcoin_depth)
        pool.spawn(self.get_btce_depth)
        pool.spawn(self.get_tfoll_depth)
        pool.join()
        
        self.btce_depth['sell'][0] = self.btce_depth['sell'][0] * USD_TO_RMB
        self.btce_depth['buy'][0] = self.btce_depth['buy'][0] * USD_TO_RMB

        status_list = []
        #status_list.append(self.get_status(ok_depth, huobi_depth, 'ok', 'huobi'))
        status_list.append(self.get_status(self.ok_depth, self.btce_depth, 'ok', 'btce'))
        #status_list.append(self.get_status(btce_depth, huobi_depth, 'btce', 'huobi'))
        status_list.append(self.get_status(self.btce_depth, self.tfoll_depth, 'btce', 'tfoll'))
        status_list.append(self.get_status(self.ok_depth, self.tfoll_depth, 'ok', 'tfoll'))
        #status_list.append(self.get_status(huobi_depth, tfoll_depth, 'huobi', 'tfoll'))

        status_list.sort(lambda a, b: int((b['rate'] - a['rate']) * 10000))
        self.status_list = status_list

        for item in self.status_list:
            self.check_trade(item)

        logging.info('%s' % status_list)

        return status_list

    def run(self):
        pre = int(time.time())
        while True:
            cur = int(time.time())
            print '-----------------------%s-----------------------' % (cur - pre)
            self.get_user_info()
            #self.search()
            print getattr(self, 'ok_depth')
            pre = cur

if __name__ == '__main__':
    three_body = ThreeBody()
    three_body.run()
