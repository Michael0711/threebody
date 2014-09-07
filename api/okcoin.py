#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-
from base import *
from config.constant import * 
from config import accounts
from lib.check_imap import ImapClient
from lib.google_auth import get_totp

import logging
import requests
import random
import time
import json

from collections import OrderedDict                                                                                                                       
from pyquery import PyQuery as pq

class OkcoinTrade(BaseTrade):

    def __init__(self, settings):
        BaseTrade.__init__(self, settings)
        self.s = requests.Session()
        self.s.headers.update(DEFAULT_HEADERS)
        self._login()

    def _login(self):
        url = "%s/login/index.do?random=%s" % (self._host, random.randint(1,100))
        try:
            data = {
                'loginName' : self._user_name,
                'password' : self._password
            }
            self.s.get(self._host, **HTTP_ARGS)
            r = self.s.post(url, data="loginName=%s&password=%s" %(self._user_name, self._password), **HTTP_ARGS)
            res = r.json()

            if res['resultCode'] == 0:
                return True
            else:
                raise WebLoginException("okcoin login failed. resultCode[%s]" % res['resultCode'])
            
        except Exception, e:
            raise WebLoginException('okcoin login exception e[%s]' % e) 

    def _gen_sign(self, order_param) :
        ret_str = ''
        for (k, v) in order_param.items() :
            ret_str += "%s=%s&" % (k, v)
        return ret_str[:-1] + self.secret_key

    def trade(self, type, rate, amount, symbol) :
        params = {
            'tradeAmount' : amount,
            'tradeCnyPrice' : rate,
            'symbol' : 0,
            'tradePwd' : self._trade_pwd, 
            'limited' : 0 
        }
        url = (self._host + '/trade/%sBtcSubmit.do?random=' + str(random.randint(1,100))) % type
        if symbol == 'btc_cny':
            params['symbol'] = 0
            coin = 'btc'
        elif symbol == 'ltc_cny':
            params['symbol'] = 1
            coin = 'ltc'

        self.s.headers.update({
            "Referer":"https://www.okcoin.cn/trade/%s.do" % coin,
        })

        result = self.s.post(url, data=params, **HTTP_ARGS)
        result = result.json()

        if result['resultCode'] == 0: 
            return { 'result' : True}
        else:
            TradeFailedException("okcoin trade fail e[%s]" % result['resultCode'])
    
    def depth(self, symbol='btc_cny') :
        rand_num = str(random.randint(100000000,999999999))
        url = self._host + '/api/depth.do?symbol=%s&r=%s' % (symbol, rand_num)
        try :
            r = self.s.get(url, **HTTP_ARGS) 
            s = r.json()
            resp = {
                'sell' : max(s['bids'][0], s['asks'][-1]),
                'buy' : min(s['bids'][0], s['asks'][-1]),
                'real_sell' : s['asks'][-1][0],
                'real_buy' : s['bids'][0][0]
            }
            resp['sell'][1] = s['asks'][-1][1]
            resp['buy'][1] = s['bids'][0][1]
            return resp
        except Exception, e:
            raise DepthFailedException("depth failed! e[%s]" % e)

    def user_info(self):
        info = {
            "funds": {
                "freezed": {
                },
                "free": {
                }
            }
        }
        d = pq(self.s.get(self._host, **HTTP_ARGS).text)
        nodes = list(d('.money.gray2').items())

        info['funds']['free']['cny'] = float("".join(nodes[0].text().split(",")))
        info['funds']['free']['btc'] = float("".join(nodes[1].text().split(",")))
        info['funds']['free']['ltc'] = float("".join(nodes[2].text().split(",")))

        info['funds']['freezed']['cny'] = float("".join(nodes[3].text().split(",")))
        info['funds']['freezed']['btc'] = float("".join(nodes[4].text().split(",")))
        info['funds']['freezed']['ltc'] = float("".join(nodes[5].text().split(",")))

        return info

    def withdrow_btc(self, amount, target_address):
        return self._withdraw(amount, target_address, 0)

    def withdrow_ltc(self, amount, target_address):
        return self._withdraw(amount, target_address, 1)

    def _withdraw(self, amount, target_address, symbol):
            SYMBOL_BTC = 0
            OK_WITHDRAW_LTC_FEE = 0.001
            OK_WITHDRAW_BTC_FEE = 0.0001

            if amount < 0.01 or not target_address:
                raise WithdrawException('okcoin Withdraw amount too small require[%s] min[0.01]', amount)

            #span = res.find('#withdrawAddrSpan').text()
            #curr_withdraw_addr = span.split(u'\xa0\xa0')[1]
            #if curr_withdraw_addr != target_address:
            #    self._change_withdraw_addr(target_address)


            url = self._host + '/account/withdrawBtcSubmit.do?random=%s' % random.randint(0, 100)
            data = {
                'withdrawAddr' : target_address, 
                'withdrawAmount': '%.2f' % amount,
                'serviceChargeFee': symbol == SYMBOL_BTC and OK_WITHDRAW_BTC_FEE or OK_WITHDRAW_LTC_FEE,
                'tradePwd' : self.trade_pwd or self.password,
                'totpCode' : str(get_totp(self.private_key, 1)),
                'symbol': str(symbol),
                'phoneCode': '0',
            }
            res = self.s.post(url, data, **HTTP_ARGS)
            res_data = res.json()
            if res_data['resultCode'] == -4 or res_data['resultCode'] == -9:
                logging.warning('OK password fail %s', res_data)
                raise PasswordErrorException("Withdraw Password Error[amount: %s, target_address: %s, symbol: %s, res: %s]" % (amount, target_address, self.symbol, res.text))
            if res_data['resultCode'] == 3 or res_data['resultCode'] == 4:
                return self.auto_click_url()

            if res_data['resultCode'] == -20:
                logging.info("google psw used, sleep")
                time.sleep(30)
                raise Exception("Withdraw fail [data: %s, res: %s]" % (data, res.text))
            if res_data['resultCode'] == 0:
                return True
            else:
                time.sleep(1)
                raise WithdrawException("Withdraw fail [data: %s, res: %s]" % (data, res.text))

    def retry_click(self, url):
            for i in range(3):
                res = self.s.get(url, **HTTP_ARGS)
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
                    mid, url = imap.check_ok_new_emails(self._src_fid)
                except Exception, info:
                    logging.error("IMAP check email fail %s", info)
                    imap = ImapClient(self._imap_host, self._imap_username, self._imap_password)
                    imap.login()
                    continue

                if not mid or not url:
                    logging.info("OKCoin not new Email %s", i)
                    time.sleep(15)
                    continue
                res = self.retry_click(url)

                imap.move_message(mid, self._src_fid, self._dst_fid)
                fail = pq(res.content).find('.scr-reg-error')

                if fail:
                    logging.warning("OKCoin click withdraw url fail[url: %s]" % (url))
                else:
                    return True
            raise WithdrawException("OKCoin can not find withdraw email")

    def get_btc_deposit_address(self):
        return self._get_deposit_address(symbol=0)

    def get_ltc_deposit_address(self):
        return self._get_deposit_address(symbol=1)

    def _get_deposit_address(self, symbol=0):
        url = self._host + "/rechargeBtc.do?symbol=%s" % symbol
        res = self.s.get(url)
        res = pq(res.content)

        address = res.find('.fincoinaddress-1 span').text()
        nick_name = res.find('.nickNameTitle').text().split(' ')[0]
        if nick_name != 'littlekfc.rao':
            raise Exception("Attention! Wrong nick Name!![%s]" % nick_name)
        address = address.split(' ')[0]
        return address

if __name__ == "__main__":

    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.DEBUG)
    logging.getLogger('requests').setLevel(logging.ERROR)
    okcoin = OkcoinTrade(accounts.okcoin)
    print okcoin.depth("ltc_cny")
    print okcoin.get_btc_deposit_address()
    print okcoin.get_ltc_deposit_address()
    #okcoin.withdrow_btc(3.0, '1MK4PfVzFgLvwhmS972xYXb8kaqoQsy7D5')

    #print okcoin.withdrow_ltc(400.0, 'LeBnaDochhdtLP6gj78nVmUdrV1qGUHZ2m')
    #print okcoin.auto_click_url()
    #print okcoin.get_btc_deposit_address()
    #print okcoin.get_ltc_deposit_address()
    #print okcoin.trade(type='sell', rate=7000, amount=0.3, symbol="btc_cny")
    #okcoin.trade(type='buy', rate=7, amount=1, symbol="ltc_cny")
