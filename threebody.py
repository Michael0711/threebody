#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

from api.okcoin import *
from api.btce import *
from api.tfoll import *

from config import accounts

class ThreeBody(object):
    def __init__(self):
        self.okcoin = OkcoinTrade(accounts.okcoin)
        self.btce = BtceTrade(accounts.btce)
        self.tfoll = TfollTrade(accounts.tfoll)

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

    def get_user_info(self):

    def search(self):
        ok_depth = self.okcoin.depth(symbol='ltc_cny')
        btce_depth = self.btce.depth(symbol='ltc_usd')
        tfoll_depth = self.tfoll.depth(symbol='ltc_cny')
        
        btce_depth['sell'][0] = btce_depth['sell'][0] * self.USD_TO_RMB
        btce_depth['buy'][0] = btce_depth['buy'][0] * self.USD_TO_RMB

        status_list = []
        #status_list.append(self.get_status(ok_depth, huobi_depth, 'ok', 'huobi'))
        status_list.append(self.get_status(ok_depth, btce_depth, 'ok', 'btce'))
        #status_list.append(self.get_status(btce_depth, huobi_depth, 'btce', 'huobi'))
        status_list.append(self.get_status(btce_depth, tfoll_depth, 'btce', 'tfoll'))
        status_list.append(self.get_status(ok_depth, tfoll_depth, 'ok', 'tfoll'))
        #status_list.append(self.get_status(huobi_depth, tfoll_depth, 'huobi', 'tfoll'))

        status_list.sort(lambda a, b: int((b['rate'] - a['rate']) * 10000))

        logging.info('%s' % status_list)

        return status_list

    def run(self):
        while True:
            self.get_user_info()
            self.status_list = self.search()

