#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-


#coding=utf-8
import time, re, requests, md5, urllib, urllib2, json

from base import *
from config import accounts
from config.constant import *


class HuobiTrade(BaseTrade):
    def __init__(self, settings):
        BaseTrade.__init__(self, settings)

    def _sign(self, params):
        params = '&'.join(sorted(["%s=%s"%(k, v) for k, v in params.items()]))
        #print 's:',s
        return md5.new(params).hexdigest().lower()

    def _request(self, params):
        params['access_key'] = self._access_key
        params['secret_key'] = self._secret_key
        params['created'] = str(int(time.time()))
        sign = self._sign(params)
        params['sign'] = sign
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        r = requests.post(self._trade_host, data=params, headers=headers, **HTTP_ARGS)
        return r.json()

    def user_info(self):
        params = {'method': 'get_account_info'}
        try:
            resp = self._request(params)
            res = {
                'funds' : {
                    'free' : {
                        'ltc' : resp['available_ltc_display'],
                        'btc' : resp['available_btc_display'],
                        'cny' : resp['available_cny_display']
                    }
                }
            }
            return res
        except Exception as e:
            raise UserInfoFailedException('huobi user info failed error[%s]' % e)


    def trade(self, type, rate, amount, symbol='ltc_cny'):
        try:
            params = {'method': type,
                      'price': rate,
                      'amount': amount,
                      'coin_type' : symbol == 'ltc_cny' and '2' or '1'
                    }
            resp =  self._request(params)
            if resp['result'] == 'success':
                return True
            else:
                raise TradeFailedException('huobi trade error[%s]' % resp)
        except Exception as e:
            raise TradeFailedException('huobi trade failed error[%s]' % e)
    
    def cancel_order(self, order_id, currency='BTC'):
        params = {'method':'cancel_delegation',
                  'id':order_id}
        return self._request(params)

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
        except Exception as e:
            raise DepthFailedException("get depth data fail[%s]" % e)
            return False
    
    def get_order(self, order_id, currency='BTC'):
        params = {'method':'delegation_info',
                  'id':order_id}
        return self._request(params)

if __name__ == "__main__":
    huobi = HuobiTrade(accounts.huobi)
    #print json.dumps(huobi.user_info(), indent=4)
    #print json.dumps(huobi.depth(symbol='btc_cny'))
    print json.dumps(huobi.trade(type='buy', rate=2800, amount=0.01, symbol='btc_cny'))
