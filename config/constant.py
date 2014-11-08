#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

HTTP_ARGS = { 
    'timeout': 3,
    'verify': False
}
TRADE_HTTP_ARGS = {
    'timeout': 3,
    'verify': False
}
DEFAULT_HEADERS = {                                                                                                                                       
    "Accept":"*/*",
    "Accept-Encoding":"gzip,deflate,sdch",
    "Accept-Language":"en-US,en;q=0.8,zh-CN;q=0.6,zh-TW;q=0.4",
    "Cache-Control":"no-cache",
    "Connection":"keep-alive",
    "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
    "Host":"www.okcoin.cn",
    "Pragma":"no-cache",
    "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.57 Safari/537.36",
    "X-Requested-With":"XMLHttpRequest"
}

USD_TO_RMB = 6.15


FLOW_CONTROL_LTC = {
    'btce_okcoin' : [1.004, 20],
    'btce_btcchina' : [1.004, 20],
    'btce_huobi' : [1.004, 20],
    'okcoin_btce' : [1.001, 30],
    'btcchina_btce' : [1.001, 30],
    'huobi_btce' : [1.001, 30],
    'btce_btcchina' : [1.004, 20],
    'default' : [1.0018, 20]
}

FLOW_CONTROL_BTC = {
    'btce_okcoin' : [1.004, 0.3],
    'btce_btcchina' : [1.004, 0.3],
    'btce_huobi' : [1.004, 0.3],
    'okcoin_btce' : [1.001, 0.3],
    'btcchina_btce' : [1.001, 0.3],
    'huobi_btce' : [1.001, 0.3],
    'default' : [1.002, 0.3]
}
