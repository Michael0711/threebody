#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

from base import *
from config import accounts

import requests
import json
import logging
import settings
import re
import md5


class HuobiAPI(BaseTrade):

    def __init__(self, settings):
        BaseTrade.__init__(self, settings)

    def user_info(self):
        params = {
                'method': 'get_account_info',
                'access_key': self._access_key,
                'created' : int(time.time())
                }
        params['sign'] = md5.md5("access_key=%s&creted=%s&method=%s&secret_key=%s" % \
                                 (self._access_key, params['created'], params['method'], \
                                  self._secret_key)).hexdigest()
        data = requests.post(self._trade_host, data=params, headers=HEADER_DEFAULT, **HEADER_DEFAULT)

    def trade(self, type, rate, amount, symbol='ltc_cny'):
        params = {
            'method' : type,
            'access_key' : self._access_key,
            'coin_type' : symbol == 'ltc_cny' and 2 or 1,
            'price' : rate,
            'amount' : amount,
            'created' : int(time.time()),
        }
        url = 
        params['sign'] = md5.md5("access_key=%s&amount=%s&coin_type=%s&created=%s&method=%s&price=%s&secret_key=%s" % \
                                 (self._access_key, amount, params['coin_type'], params['created'], \
                                  params['method'], rate, self._secret_key)).hexdigest()
        data = requests.post(self._trade_host, data=params, headers=HEADER_DEFAULT, **HEADER_DEFAULT)


    def depth(self, symbol='ltc_cny') :
        DATA_REGEX = r"view_detail\((.*)\)"
        symbols = {
                'ltc_cny': 'detail_ltc.html',
                'btc_cny': 'detail.html'
                }
        url = 'https://market.huobi.com/staticmarket/%s' % symbols[symbol]
        try:
            data = requests.get(url, **HTTP_ARGS).text
            data = re.match(DATA_REGEX, data).group(1)
            data = json.loads(data)
            return {
                    'buy': [float(data['buys'][0]['price']), float(data['buys'][0]['amount'])],
                    'sell': [float(data['sells'][0]['price']), float(data['sells'][0]['amount'])]
                    }
        except Exception, e:
            logging.warn("get depth data fail[%s]" % e)
            return False

if __name__ == '__main__':
    while True:
        print json.dumps(huobi.depth())



