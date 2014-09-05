#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-
import time
import logging

class Log(object):
    FORMAT = "\033[1;3%sm%s\033[0m"
    ID = ''
    @staticmethod
    def init(log_file):
        if log_file:
            logging.basicConfig(filename=log_file, format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)
        else:
            logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)                                                           
        logging.getLogger('requests').setLevel(logging.ERROR)

    @staticmethod
    def reset_id(text):
        return "%s!%s" % (text,int(time.time()))

    @staticmethod
    def info(text):
        logging.info("id(%s) :%s" % (Log.ID, text)
    
    @staticmethod
    def error(text):
        logging.error("id(%s) :%s" % (Log.ID, text)

    @staticmethod
    def debug(text):
        logging.debug("id(%s) :%s" % (Log.ID, text)

    @staticmethod
    def green(text):
        return Log.FORMAT % ('2', text)

    @staticmethod
    def red(text):
        return Log.FORMAT % ('1', text)

    @staticmethod
    def yellow(text):
        return Log.FORMAT % ('3', text)
        
    @staticmethod
    def blue(text):
        return Log.FORMAT % ('4', text)

if __name__ == '__main__':
    print Log.green("rj")
    print Log.red("rj")
    print Log.blue("rj")


