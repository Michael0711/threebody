#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-
 
from base import *
from config import accounts
from config.constant import *

import time
import re
import hmac
import hashlib
import base64
#import httplib
import json
import requests
 
class BtcchinaTrade(BaseTrade):
    def __init__(self, settings):
        BaseTrade.__init__(self, settings)
        #self.conn=httplib.HTTPSConnection("api.btcchina.com")
 
    def _get_tonce(self):
        return int(time.time()*1000000)
 
    def _get_params_hash(self,pdict):
        pstring=""
        # The order of params is critical for calculating a correct hash
        fields=['tonce','accesskey','requestmethod','id','method','params']
        for f in fields:
            if pdict[f]:
                if f == 'params':
                    # Convert list to string, then strip brackets and spaces
                    # probably a cleaner way to do this
                    param_string=re.sub("[\[\] ]","",str(pdict[f]))
                    param_string=re.sub("'",'',param_string)
                    pstring+=f+'='+param_string+'&'
                else:
                    pstring+=f+'='+str(pdict[f])+'&'
            else:
                pstring+=f+'=&'
        pstring=pstring.strip('&')
 
        # now with correctly ordered param string, calculate hash
        phash = hmac.new(self._secret_key, pstring, hashlib.sha1).hexdigest()
        return phash
 
    def _private_request(self,post_data):
        #fill in common post_data parameters
        tonce=self._get_tonce()
        post_data['tonce']=tonce
        post_data['accesskey']=self._access_key
        post_data['requestmethod']='post'
 
        # If ID is not passed as a key of post_data, just use tonce
        if not 'id' in post_data:
            post_data['id']=tonce
 
        pd_hash=self._get_params_hash(post_data)
 
        # must use b64 encode        
        auth_string='Basic '+base64.b64encode(self._access_key+':'+pd_hash)
        headers={'Authorization':auth_string,'Json-Rpc-Tonce':tonce}
 
        #post_data dictionary passed as JSON        
        response = requests.post("https://api.btcchina.com/api_trade_v1.php", headers=headers, data=json.dumps(post_data), **HTTP_ARGS)
        #self.conn.request("POST",'/api_trade_v1.php',json.dumps(post_data),headers)
        #response = self.conn.getresponse()
 
        # check response code, ID, and existence of 'result' or 'error'
        # before passing a dict of results
        if response.status_code == 200:
            # this might fail if non-json data is returned
            #resp_dict = json.loads(response.read())
            resp_dict = response.json()
 
            # The id's may need to be used by the calling application,
            # but for now, check and discard from the return dict
            if str(resp_dict['id']) == str(post_data['id']):
                if 'result' in resp_dict:
                    return resp_dict['result']
                elif 'error' in resp_dict:
                    return resp_dict['error']
        else:
            # not great error handling....
            print "status:",response.status
            print "reason:".response.reason
 
        return None
 
    def user_info(self):
        post_data = {}
        
        post_data['method']='getAccountInfo'
        post_data['params']=[]
        resp =  self._private_request(post_data)
        res = {
            "funds" : {
                "free": {
                    'ltc' : resp['balance']['ltc']['amount'],
                    'btc' : resp['balance']['btc']['amount'],
                    'cny' : resp['balance']['cny']['amount']
                }
            }
        }
        return self.format_info(res)

    def depth(self, symbol='ltc_cny'):
        post_data = {}
        post_data['method']='getMarketDepth2'
        post_data['params']=[3,"ALL"]
        resp = self._private_request(post_data)
        if symbol == 'ltc_cny':
            res = {
                'sell' : [resp['market_depth_ltccny']['ask'][0]['price'], resp['market_depth_ltccny']['ask'][0]['amount']],
                'buy' : [resp['market_depth_ltccny']['bid'][0]['price'],resp['market_depth_ltccny']['bid'][0]['amount']]
            }
            if res['sell'][0] < res['buy'][0]:
                raise DepthFailedException("btcchina get depth error[%s]" % res)
            return res
        elif symbol == 'btc_cny':
            res = {
                'sell' : [resp['market_depth_btccny']['ask'][0]['price'], resp['market_depth_btccny']['ask'][0]['amount']],
                'buy' : [resp['market_depth_btccny']['bid'][0]['price'],resp['market_depth_btccny']['bid'][0]['amount']]
            }
            if res['sell'][0] < res['buy'][0]:
                raise DepthFailedException("btcchina get depth error[%s]" % res)
            return res
        elif symbol == 'all':
            ltc = {
                'sell' : [resp['market_depth_ltccny']['ask'][0]['price'], resp['market_depth_ltccny']['ask'][0]['amount']],
                'buy' : [resp['market_depth_ltccny']['bid'][0]['price'],resp['market_depth_ltccny']['bid'][0]['amount']]
            }
            if ltc['sell'][0] < ltc['buy'][0]:
                raise DepthFailedException("btcchina get ltc depth error[%s]" % res)
            btc = {
                'sell' : [resp['market_depth_btccny']['ask'][0]['price'], resp['market_depth_btccny']['ask'][0]['amount']],
                'buy' : [resp['market_depth_btccny']['bid'][0]['price'],resp['market_depth_btccny']['bid'][0]['amount']]
            }
            if btc['sell'][0] < btc['buy'][0]:
                raise DepthFailedException("btcchina get btc depth error[%s]" % res)
            return ltc,btc


    def trade(self, type, rate, amount, symbol='ltc_cny') :
        try:
            if symbol == 'ltc_cny':
                market = 'LTCCNY'
            elif symbol == 'btc_cny':
                market = 'BTCCNY'
            elif symbol == 'ltc_btc':
                market = 'LTCBTC'
            if type == 'sell':
                return self.sell(rate, amount, market)
            if type == 'buy':
                return self.buy(rate, amount, market)
        except Exception as e:
            raise TradeFailedException('type[%s] rate[%s] amount[%s] market[%s] error[%s]' % \
                                       (type, rate, amount, market, e))

#[BTCCNY],[LTCCNY],[LTCBTC]  
    def buy(self,price,amount,market,post_data={}):
        post_data['method']='buyOrder2'
        post_data['params']=["{0:.4f}".format(round(price,4)),"{0:.4f}".format(round(amount,4)),market]
        return self._private_request(post_data)
 
    def sell(self,price,amount,market,post_data={}):
        post_data['method']='sellOrder2'
        post_data['params']=["{0:.4f}".format(round(price,4)),"{0:.4f}".format(round(amount,4)),market]
        return self._private_request(post_data)
 
    def cancel(self,order_id,post_data={}):
        post_data['method']='cancelOrder'
        post_data['params']=[order_id]
        return self._private_request(post_data)
 
    def request_withdrawal(self,currency,amount,post_data={}):
        post_data['method']='requestWithdrawal'
        post_data['params']=[currency,amount]
        return self._private_request(post_data)
 
    def get_deposits(self,currency='BTC',pending=True,post_data={}):
        post_data['method']='getDeposits'
        if pending:
            post_data['params']=[currency]
        else:
            post_data['params']=[currency,'false']
        return self._private_request(post_data)
 
    def get_orders(self,id=None,open_only=True,post_data={}):
        # this combines getOrder and getOrders
        if id is None:
            post_data['method']='getOrders'
            if open_only:
                post_data['params']=[]
            else:
                post_data['params']=['false']
        else:
            post_data['method']='getOrder'
            post_data['params']=[id]
        return self._private_request(post_data)
 
    def get_withdrawals(self,id='BTC',pending=True,post_data={}):
        # this combines getWithdrawal and getWithdrawls
        try:
            id = int(id)
            post_data['method']='getWithdrawal'
            post_data['params']=[id]
        except:
            post_data['method']='getWithdrawals'
            if pending:
                post_data['params']=[id]
            else:
                post_data['params']=[id,'false']
        return self._private_request(post_data)

if __name__ == "__main__":
    #btcchina = BTCChina(access=settings['btcchina']['access_key'], secret=settings['btcchina']['secret_key'])
    btcchina = BtcchinaTrade(accounts.btcchina)
    #print json.dumps(btcchina.get_account_info(), indent=4)
    #print json.dumps(btcchina.user_info())
    ltc,btc,ltc_btc = btcchina.depth("all")
    print ltc
    print btc
    print ltc_btc
    #print json.dumps(btcchina.trade(type="sell", rate=20, amount=68, symbol='ltc_cny'))
    #print json.dumps(btcchina.trade(type="buy", rate=1, amount=2, symbol='ltc_cny'))
    #def sell(self,price,amount,market,post_data={}):
    #print btcchina.sell(1, 1, 'LTCBTC')
            

    #print json.dumps(btcchina.get_orders(), indent=4)
    
    #print json.dumps(btcchina.buy(0.025,3,'LTCBTC'))
    #print json.dumps(btcchina.cancel(15549603))

