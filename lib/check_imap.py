#!/usr/bin/python                                                               
# -*- coding: utf-8 -*-

import logging
import imaplib
import re
from text import get_in
import email
import base64
from pyquery import PyQuery as pq

RE_BODYSTRUCTURE = re.compile(r"\d+ \(UID (\d+) BODY")

class MailerError(Exception):
    pass

class ImapClient(object):
    def __init__(self, host, username, password):
        self.host = host
        self.username = username
        self.password = password
        self.conn = None 

    def login(self):
        for i in range(5):
            try:
                self.conn = imaplib.IMAP4_SSL(self.host)
                self.conn.login(self.username, self.password)
                return True
            except:
                continue
        raise Exception("IMAP login Fail")
    
    def search_folder(self, search_name):
        res, data = self.conn.list()
        if res == 'OK':
            for item in data:
                name = item.split(' ')[-1]
                if name.find(search_name) != -1:
                    return name
        return None

    def check_new_emails(self, fid):
        self.conn.select(fid)
        res, data = self.conn.list()
        data, uids = self.conn.uid('search', None, '(UID *:*)')

        if not uids or not uids[0]:
            return None, None
        uids = uids[0].split(' ')
        uids = uids[-1:]
        error, data = self.conn.uid("fetch", ",".join(uids), "(UID BODY.PEEK[])")
        if error != 'OK':
            return None

        for i in reversed(range(0, len(data))):
            item = data[i]
            mo = RE_BODYSTRUCTURE.match(item[0])
            if not mo:
                #logging.error("Returned data not match regex: %s", item)
                continue

            mid = mo.group(1)
            #print item[1]
            key = get_in(item[1], 'To confirm the transaction, go to:', 'To cancel a')
            if not key:
                continue
            url = key.strip()
            return mid, url
        return None, None

    def check_ok_new_emails(self, fid):
        self.conn.select(fid)
        res, data = self.conn.list()
        data, uids = self.conn.uid('search', None, '(UID *:*)')

        if not uids or not uids[0]:
            return None, None
        uids = uids[0].split(' ')
        uids = uids[-1:]
        error, data = self.conn.uid("fetch", ",".join(uids), "(UID BODY.PEEK[])")
        if error != 'OK':
            return None

        for i in reversed(range(0, len(data))):
            item = data[i]
            mo = RE_BODYSTRUCTURE.match(item[0])
            if not mo:
                #logging.error("Returned data not match regex: %s", item)
                continue

            mid = mo.group(1)
            #print item[1]
            #base64_text = get_in(item[1], 'Content-Transfer-Encoding: base64', '------=')
            #msg_text = base64.b64decode(base64_text.strip())
            msg = email.message_from_string(item[1])
            content = msg.get_payload()[0].get_payload(decode=1)
            content = pq(content).text()
            content = content.replace('\n', ' ')
            print repr(content)
            key = get_in(content, 'http', ' ')
            if not key:
                continue
            key = "http" + key.strip()
            return mid, key
        return None, None


    def move_message(self, mids, src_fid, dst_fid):
        if not mids: return
        if isinstance(mids, basestring):
            mids = [mids]
        error, data = self.conn.select(src_fid)
        if error != "OK":
            raise MailerError(data[0])

        error, data = self.conn.uid("copy", ",".join(mids), dst_fid)
        if error != "OK":
            raise MailerError(data[0])

        error, data = self.conn.select(src_fid)
        if error != "OK":
            raise MailerError(data[0])

        error, data = self.conn.uid("store", ",".join(mids), '+FLAGS', '(\Deleted)')
        if error != "OK":
            raise MailerError(data[0])

        error, data = self.conn.expunge()
        if error != "OK":
            raise MailerError(data[0])

def main():
    app = ImapClient('imap.qq.com', '171322809@qq.com', 'shoes.com.888')
    print app.login()
    print app.check_ok_new_emails('&UXZO1mWHTvZZOQ-/btce')

if __name__ == '__main__':
    main()

