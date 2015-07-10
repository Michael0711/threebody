#!/usr/bin/python                                                                                                                                         
# -*- coding: utf-8 -*-

import tornado.ioloop
import tornado.web
from tornado import gen 
from tornado.httpclient import AsyncHTTPClient
from settings import settings

import json

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        is_all = self.get_argument("all", None)
        fi = file("/root/threebody/web/status.txt")
        content = json.loads(fi.read())
        if is_all != None:
            content = content['all']
        self.render("index.html", content=json.dumps(content, indent=4))

if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
    ], **settings)  
    application.listen(8001)
    tornado.ioloop.IOLoop.instance().start()

