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
        for key in settings:
            setattr(self, '_%s' % key, settings[key])

    def depth(self, symbol='ltc_cny'):
        NotImplementedError("please implement depth api")

    @property
    def can_withdrow(self):
        return False

    def web_login(self):
        pass

   # info = {
   #     "funds": {
   #         "freezed": {
   #         },
   #         "free": {
   #         }
   #     }
   # }
    def user_info(self):
        pass

