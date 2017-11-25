#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2017 FawkesPan
#
#

import time
import ssl
import sys
import code
import redis
from threading import Thread

import apiconfig

import six
from six.moves.urllib.parse import urlparse

import websocket

import string

try:
    import readline
except ImportError:
    pass

SYMBOL = 'XBTUSD'

def subscribe(ws):
    def run(*args):
        ws.send('{"op": "subscribe", "args": ["trade:XBTUSD"]}')
        while True:
            ws.send('ping')
            time.sleep(60)

    Thread(target=run).start()

def WriteREDIS(ws,message,r):
    p = r.pipeline()
    if 'table' in message:
        data = message['data']
        multi = 0
        for tickers in data:
            if multi == 0:
                date = tickers['timestamp'].replace('-','').replace('T','').replace(':','').replace(".",'').replace('Z','0000')
                multi = 1
            else:
                date = date + 1
            if tickers['tickDirection'] == 'MinusTick':
                side = 'SELL'
                change = -1
            elif tickers['tickDirection'] == 'ZeroMinusTick':
                side = 'SELL'
                change = 0
            elif tickers['tickDirection'] == 'PlusTick':
                side = 'BUY'
                change = 1
            elif tickers['tickDirection'] == 'ZeroPlusTick':
                side = 'BUY'
                change = 0
            price = tickers['price']
            size = tickers['homeNotional']
            value = tickers['foreignNotional']
            p.hset('timestamp:'+date,'symbol',SYMBOL)
            p.hset('timestamp:'+date,'side',side)
            p.hset('timestamp:'+date,'price',price)
            p.hset('timestamp:'+date,'size',size)
            p.hset('timestamp:'+date,'value',value)
            p.hset('timestamp:'+date,'change',change)

        p.execute()
            
    if 'pong' in message:
        print(time.strftime('%Y-%m-%d',time.localtime(time.time())) + "To the moon.")

def WriteCSV(ws,message,f):
    if 'table' in message:
        data = message['data']
        multi = 0
        for tickers in data:
            if multi == 0:
                date = tickers['timestamp'].replace('-','').replace('T','').replace(':','').replace(".",'').replace('Z','0000')
                multi = 1
            else:
                date = date + 1
            if tickers['tickDirection'] == 'MinusTick':
                side = 'SELL'
                change = -1
            elif tickers['tickDirection'] == 'ZeroMinusTick':
                side = 'SELL'
                change = 0
            elif tickers['tickDirection'] == 'PlusTick':
                side = 'BUY'
                change = 1
            elif tickers['tickDirection'] == 'ZeroPlusTick':
                side = 'BUY'
                change = 0
            price = tickers['price']
            size = tickers['homeNotional']
            value = tickers['foreignNotional']
            f.write("{},{},{},{},{},{}".format(SYMBOL,side,price,size,value,change))
            f.write("\n")
        
        f.flush()

    if 'pong' in message:
        print(time.strftime('%Y-%m-%d',time.localtime(time.time())) + "To the moon.")

def on_error(ws,error):
    print(time.strftime('%Y-%m-%d',time.localtime(time.time())) + error)

    exit()

def closing(ws):
    print("Shuting Down...")
    ws.close()

def main():
    config = {}
    config = apiconfig.get_config()
    options = {}

    websocket.enableTrace(True)

    if config['HTTP_PROXY_ENABLE']:
        options['http_proxy_host'] = config['HTTP_PROXY_HOST']
        options['http_proxy_port'] = config['HTTP_PROXY_PORT']

    URL = config['BASE_URL']
    METHOD = apiconfig.get_config()['STORAGE_METHOD']

    if METHOD == 'redis':
        r = redis.Redis(host=config['REDIS_HOST'],port=config['REDIS_PORT'],db=config['REDIS_DB'])
        ws = websocket.WebSocketApp(URL,
                                    on_message=WriteREDIS,
                                    on_error=on_error,
                                    on_close=closing)
    elif METHOD == 'csv':
        f = open(config['CSV_FILENAME'],"a")
        ws = websocket.WebSocketApp(URL,
                                    on_message=WriteCSV,
                                    on_error=on_error,
                                    on_close=closing)
    else:
        print("Unsupported Storage Method. Exiting...")

        exit()
    
    ws.on_open = subscribe
    ws.run_forever()

if __name__ == '__main__':
    main()