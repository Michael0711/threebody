#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

import sys,os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from exceptions import NotImplementedError

class WebLoginException(Exception):
    pass

class DepthFailedException(Exception):
    pass

class UserInfoFailedException(Exception):
    pass

class TradeFailedException(Exception):
    pass

class WithdrawException(Exception):
    pass

class PasswordErrorException(Exception):
    pass

class SeriousErrorException(Exception):
    pass

class BaseTrade(object):
    def __init__(self, settings):
        self._stop = False
        for key in settings:
            setattr(self, '_%s' % key, settings[key])

    def depth(self, symbol='ltc_cny'):
        NotImplementedError("please implement depth api")

    @property
    def can_withdrow(self):
        return False

    def set_stop(self, val):
        self._stop = val

    @property
    def stop(self):
        return self._stop

    def web_login(self):
        pass

    def trade(self, type, rate, amount, symbol='ltc_cny'):
        NotImplementedError("please implement trade api")

   # info = {
   #     "funds": {
   #         "freezed": {
   #         },
   #         "free": {
   #         }
   #     }
   # }
    def user_info(self):
        NotImplementedError("please implement user_info api")
    def format_info(self, info):
        info['funds']['free']['ltc'] = float(info['funds']['free']['ltc']) - 0.5
        info['funds']['free']['btc'] = float(info['funds']['free']['btc']) - 0.01
        info['funds']['free']['cny'] = float(info['funds']['free']['cny']) - 50
        return info
