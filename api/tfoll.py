#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

from base import *
from config.constant import * 
from config import accounts

import requests
import json
import logging

class TfollTrade(BaseTrade):

    def __init__(self, settings):
        BaseTrade.__init__(self, settings)

    def depth(self, symbol):
        symbol = symbol == 'btc_cny' and 1 or 0
        url = self._host + "/api/depth/depth.html?type=%s" % symbol
        try:
            resp = requests.get(url, **HTTP_ARGS).json()
            res = {
                'buy' : resp['bids'][0]
                'sell' : resp['asks'][0]
            }
            return res
        except Exception as e:
            raise DepthFailedException('tfoll get depth failed [%s]' % e)

if __name__ == "__main__":
    tfoll = TfollTrade(accounts.tfoll)
    tfoll.depth('ltc_cny')
