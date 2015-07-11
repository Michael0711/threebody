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

USD_TO_RMB = 6.21


FLOW_CONTROL_LTC = {
    'btce_okcoin' : [1.01, 2],
    'btce_btcchina' : [1.01, 2],
    'btce_huobi' : [1.01, 2],
    'okcoin_btce' : [1.01, 3],
    'btcchina_btce' : [1.01, 3],
    'huobi_btce' : [1.01, 3],
    'btce_btcchina' : [1.01, 2],
    'default' : [1.018, 2]
}

FLOW_CONTROL_BTC = {
    'btce_okcoin' : [1.01, 0.02],
    'btce_btcchina' : [1.04, 0.02],
    'btce_huobi' : [1.01, 0.02],
    'okcoin_btce' : [1.01, 0.02],
    'btcchina_btce' : [1.008, 0.02],
    'huobi_btce' : [1.008, 0.03],
    'default' : [1.018, 0.03]
}
