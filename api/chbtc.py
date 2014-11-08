#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

import time, re, requests, md5, urllib, urllib2, json, hashlib, struct, sha

from base import *
from config import accounts
from config.constant import *


class ChbtcTrade(BaseTrade):
    def __init__(self, settings):
        BaseTrade.__init__(self, settings)

    def __fill(self, value, lenght, fillByte):
        if len(value) >= lenght:
            return value
        else:
            fillSize = lenght - len(value)
        return value + chr(fillByte) * fillSize

    def __doXOr(self, s, value):
        slist = list(s)
        for index in xrange(len(slist)):
            slist[index] = chr(ord(slist[index]) ^ value)
        return "".join(slist)

    def __hmacSign(self, aValue, aKey):
        keyb   = struct.pack("%ds" % len(aKey), aKey)
        value  = struct.pack("%ds" % len(aValue), aValue)
        k_ipad = self.__doXOr(keyb, 0x36)
        k_opad = self.__doXOr(keyb, 0x5c)
        k_ipad = self.__fill(k_ipad, 64, 54)
        k_opad = self.__fill(k_opad, 64, 92)
        m = hashlib.md5()
        m.update(k_ipad)
        m.update(value)
        dg = m.digest()
        
        m = hashlib.md5()
        m.update(k_opad)
        subStr = dg[0:16]
        m.update(subStr)
        dg = m.hexdigest()
        return dg

    def __digest(self, aValue):
        value  = struct.pack("%ds" % len(aValue), aValue)
        h = sha.new()
        h.update(value)
        dg = h.hexdigest()
        return dg

    def __api_call(self, path, params = ''):
        try:
            SHA_secret = self.__digest(self._secret_key)
            sign = self.__hmacSign(params, SHA_secret)
            reqTime = (int)(time.time()*1000)
            params+= '&sign=%s&reqTime=%d'%(sign, reqTime)
            url = 'https://trade.chbtc.com/api/' + path + '?' + params
            request = urllib2.Request(url)
            response = urllib2.urlopen(request, timeout=2)
            doc = json.loads(response.read())
            return doc
        except Exception,ex:
            raise Exception(ex)

   # info = {
   #     "funds": {
   #         "freezed": {
   #         },
   #         "free": {
   #         }
   #     }
   # }
    def user_info(self):
        try:
            params = "method=getAccountInfo&accesskey="+self._access_key
            path = 'getAccountInfo'
            obj = self.__api_call(path, params)
            res = {
                'funds' : {
                    'freezed' : {
                        'ltc' : obj['result']['frozen']['LTC']['amount'],
                        'btc' : obj['result']['frozen']['BTC']['amount'],
                        'cny' : obj['result']['frozen']['CNY']['amount']
                    },
                    'free' : {
                        'ltc' : obj['result']['balance']['LTC']['amount'],
                        'btc' : obj['result']['balance']['BTC']['amount'],
                        'cny' : obj['result']['frozen']['CNY']['amount']
                    }
                }
            }
            return res
        except Exception,ex:
            raise UserInfoFailedException('chbtc[%s]' % ex)
    
    def trade(self, type, rate, amount, symbol='ltc_cny'):
        pass
    

    def depth(self, symbol) :
        if symbol == 'btc_cny':
            url = 'http://api.chbtc.com/data/depth'
        else:
            url = 'http://api.chbtc.com/data/ltc/depth'
        try:
            resp = requests.get(url).json()
            res = {
                'buy' : resp['bids'][0],
                'sell' : resp['asks'][-1]
            }
            if res['buy'][0] > res['sell'][0]:
                raise DepthFailedException("chbtc get depth data error[bids > asks]")
            return res
        except Exception, e:
            raise DepthFailedException("chbtc get depth data fail[%s]" % e)
    

if __name__ == "__main__":
    chbtc = ChbtcTrade(accounts.chbtc)
    print chbtc.user_info()
    print chbtc.depth(symbol='btc_cny')


