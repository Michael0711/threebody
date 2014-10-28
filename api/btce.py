#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-
import logging
import hashlib,hmac
import requests
import random
import time
import urllib
import re
import json
from collections import OrderedDict
from pyquery import PyQuery as pq

from base import *
from lib.text import *
from lib.google_auth import get_totp
from lib.check_imap import ImapClient
from config import accounts
from config.constant import *


requests.adapters.DEFAULT_RETRIES = 3

TITLE = 'Withdrawal successfully confirmed'
FEE = 0.998
error_title1 = 'Ошибка: Заявка уже подтверждена или отменена ранее'
daily_limit = 'Ошибка: You have exceeded the daily limit on withdrawal'

class BtceTrade(BaseTrade) :

    TIMEOUT = 5
    _nonce = 0
    
    def __init__(self, settings) :
        BaseTrade.__init__(self, settings)
        self.session = requests.Session()
        self.session.headers = DEFAULT_HEADERS
        #{u'success': 0, u'error': u'invalid nonce parameter; on key:2999999698, you sent:0, you should send:2999999699'}
        info = self.user_info(no_exception=True)
        REX_NONCE = r'you should send:(\d*)'
        self._nonce = int(re.search(REX_NONCE,info['error']).group(1)) - 1

    def _get_nonce(self) :
        self._nonce = self._nonce + 1
        return str(self._nonce)

        #return str(int(str(int(time.time() * 1000))))
    
    def _get_sign(self, post_param) :
        post_param['nonce'] = self._get_nonce()
        ret_str = urllib.urlencode(post_param)
        return hmac.new(self._sec, ret_str, hashlib.sha512).hexdigest()

    def depth(self, symbol='ltc_btc') :
        rand_num = str(random.randint(100000000,999999999))
        url = self._host + '/api/2/%s/depth?r=%s' % (symbol, rand_num)

        try :
            r = requests.get(url, timeout=self.TIMEOUT, headers={'Cache-Control' : 'no-cache'})
            s = r.json()
            resp = {
                'sell' : s['asks'][0],
                'buy' : s['bids'][0],
            }
            if symbol != 'ltc_btc':
                resp['sell'][0] = float(resp['sell'][0]) * USD_TO_RMB
                resp['buy'][0] = float(resp['buy'][0]) * USD_TO_RMB
                resp['sell'][1] = float(resp['sell'][1])
                resp['buy'][1] = float(resp['buy'][1])
            return resp
        except Exception, e:
            raise DepthFailedException("btce get depth error[%s]" % e)

    def user_info(self, no_exception=False) :
        url = self._host + '/tapi/'
        post_param = {
            'method' : 'getInfo',
            'nonce' : self._get_nonce()
        }
        sign = self._get_sign(post_param)
        headers = {
            "Content-type" : "application/x-www-form-urlencoded",
            'Sign' : sign,
            'Key' : self._key,
        }
        try :
            r = requests.post(url, data=post_param, headers=headers, timeout=self.TIMEOUT)
            resp = r.json()
            if resp.get("error", None) and no_exception == False:
                raise UserInfoFailedException("btce[%s]" % resp)
            elif resp.get("error", None) and no_exception == True:
                return resp
            res = {
                'funds' : {
                    'free' : {
                        'ltc' : float(resp['return']['funds']['ltc']),
                        'btc' : float(resp['return']['funds']['btc']),
                        'cny' : float(resp['return']['funds']['usd']) * USD_TO_RMB
                    }
                }
            }
            return self.format_info(res)
        except Exception, e:
            raise UserInfoFailedException("btce get userinfo error[%s]" % e)
    
    def trade(self, type, rate, amount, symbol='ltc_btc') :
        if symbol.find('usd') != -1:
            rate = float(rate) / USD_TO_RMB
        url = self._host + '/tapi/'
        post_param = {
            'method' : 'Trade',
            'nonce' : self._get_nonce(),
            'pair' : symbol,
            'type' : type,
            'rate' : "%.5f" % float(rate),
            'amount' : "%.5f" % float(amount),
        }

        if symbol.find('usd') != -1:
            post_param['rate'] = "%.3f" % float(rate)
            post_param['amount'] = "%.3f" % float(amount)

        sign = self._get_sign(post_param)
        headers = {
            "Content-type" : "application/x-www-form-urlencoded",
            'Sign' : sign,
            'Key' : self._key,
        }
        try :
            r = requests.post(url, data=post_param, headers=headers, timeout=self.TIMEOUT)
            logging.debug('url[%s] resp[%s]' % (url, r.text))
            resp = r.json()
            return resp
        except Exception, e:
            logging.warning("trade failed! e[%s]" % e)
            return False 

    def name(self):
            if self.web_username:
                return 'BTCE(%s)' % (self.web_username)
            return 'BTCE'

    def md5(self, a):
            b = hashlib.md5(a).hexdigest()
            return b[::-1]

    def get_pow(self, a, b):
            c = 0
            while True:
                hash_hex = self.md5(self.md5(b+str(c)))
                hash = int(hash_hex, 16)
                c += 1
                if c > 100000:
                    raise Exception('Login Fail')
                if hash < a:
                    return c
            return c 

    def web_login(self):
            url = self._host
            res = self.session.get(url, **HTTP_ARGS)
            if res.text.find('Please wait...') != -1:
                new_cookie = get_in(res.text, 'document.cookie="a=', ';path=')
                self.session.cookies['a'] = new_cookie
                res = self.session.get(url, **HTTP_ARGS)
            if res.content and res.content.find("var auth_login = ''") == -1:
                logging.info('%s had login', self.name())
                return True
     
            url = self._host + '/ajax/login'
            data = "email=%s&password=%s&otp=-&PoW_nonce=" % (urllib.quote_plus(self._web_username), urllib.quote_plus(self._web_password)) 
            res = self.session.post(url, data=data, **HTTP_ARGS)
            #{"success":1, "data":{"PoW":1,"work":{"target":3.1153781151209e+34,"data":"INZNJV92K196PR1Z9XGHVY20S3KQK0VIVZYSHO7C9TUKRUO9UYZETS1UNRREHC8I"}}}
            res_data = res.json()
            print res_data
            if res_data['success']:
                if res_data['data'].get('login_success', 0) != 1:
                    nonce = self.get_pow(res_data['data']['work']['target'], res_data['data']['work']['data'])
                    #data = urllib.urlencode(data)
                    data = "email=%s&password=%s&otp=%s&PoW_nonce=%s" % (urllib.quote_plus(self._web_username), urllib.quote_plus(self._web_password), urllib.quote_plus(str(get_totp(self._private_key))), nonce)
            
                    res = self.session.post(url, data=data,  **HTTP_ARGS)
                    res_data = res.json()
                    print '>>>>', res_data
                if res_data['data'].get('login_success', 0) == 1:
                    logging.info("%s login success", self.name())
                    return True

            raise Exception("BTCE login fail")

    def get_deposit_address(self, coin):
            url = self._host + "/ajax/billing"
            res = self.session.post(url, data={'act' : 'deposit_coin/%s' % coin}, **HTTP_ARGS)

            res = pq(res.content)
            address = res.find('#coin-address').text()
            if not address:
                raise Exception("Failed to get address")
            return address

    def get_csrf_token(self):
            url = self._host + '/profile'
            res = self.session.get(url)
            print res.content
            return pq(res.content).find('#csrf-token').val()

    def withdraw_ltc(self, amount, target_address):
            if amount < 1:
                raise Exception('Withdraw amount too small require[%s] min[1]', amount)
            self._withdraw(amount, target_address, 8)

    def withdraw_btc(self, amount, target_address):
            if amount < 0.01:
                raise Exception('Withdraw amount too small require[%s] min[0.01]', amount)
            self._withdraw(amount, target_address, 1)

    def _withdraw(self, amount, target_address, coin):
            url = self._host + '/ajax/billing'
            data = {'act': 'withdraw_coin/%s' % coin, 'csrfToken': self.get_csrf_token()}
            res = self.session.post(url, data=data, **HTTP_ARGS)
            if not res.content:
                raise Exception("Failed withdraw [amount: %s, target_address: %s, coin: %s, res: %s]" % (amount, target_address, coin, res.content))

            inputs = get_input(res.content, type="hidden", name='id')
            token = inputs['token']
            url = self._host + '/ajax/coins'
            data = {
                'act': "withdraw",
                'sum': str(amount),
                'address': target_address,
                'coin_id': str(coin),
                'token': token,
                'otp': str(get_totp(self._private_key, 1)),
                'csrfToken': self.get_csrf_token()
            }
            res = self.session.post(url, data=data, **HTTP_ARGS)
            result = pq(res.text).find('h1').text()
            if result == "A letter with further instructions sent to your email!":
                logging.info("Withdraw[amount: %s, target_address: %s, coin: %s]", amount, target_address, coin)
            else:
                raise Exception("Failed withdraw [amount: %s, target_address: %s, coin: %s, res: %s]" % (amount, target_address, coin, result))
            self.auto_click_url()

    def retry_click(self, url):
            for i in range(3):
                res = self.session.get(url, **HTTP_ARGS)
                if res.status_code != 200:
                    continue
                return res
            return res

    def auto_click_url(self):
            imap = ImapClient(self._imap_host, self._imap_username, self._imap_password)
            imap.login()
            logging.info('IMAP login success')
            for i in range(60):
                try:
                    mid, url = imap.check_new_emails(self._src_fid)
                except Exception, info:
                    logging.error("IMAP check email fail %s", info)
                    imap = ImapClient(self._imap_host, self._imap_username, self._imap_password)
                    imap.login()
                    continue

                if not mid or not url:
                    logging.info("BTCE not new Email")
                    time.sleep(30)
                    continue
                res = self.retry_click(url)
                if not res.text:
                    raise BtceNotLoginException()
                imap.move_message(mid, self._src_fid, self._dst_fid)
                title = pq(res.text).find('h1').text()

                if title.find(TITLE) != -1:
                    if title.find('BTC-E CODE:') != -1:
                        return get_in(title, 'BTC-E CODE: ')
                    return True

                if error_title1 in title:
                    imap.move_message(mid, self._src_fid, self._dst_fid)
                    continue
                if daily_limit in title:
                    raise DailyLimitException(daily_limit)
                logging.warning("BTCE click withdraw url fail[title: %s, url: %s]" % (title, url))
                #raise Exception()
            raise Exception("BTCE can not find withdraw email")
         

if __name__ == "__main__" :
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.ERROR)

    e = BtceTrade(accounts.btce)
    #print e.depth(symbol='ltc_btc')
    #print e.user_info()
    #print e.trade(type='buy', rate=2000, amount=0.01, symbol='btc_usd')
    #print e.web_login()
    #print e.get_deposit_address(8)
    #print e.withdraw_btc(5, '13r8HATkywXL8tHZrZK54Ysuzz8GdqtM2a')
    #print e.get_deposit_address(8)


    #print e.trade(type='sell', rate='1', amount='1', symbol='ltc_btc')

