# coding: utf-8
"""
author:qinzhiqiang
date:2017-11-20
函数文件功能：获取代理ip，验证代理ip是否可用。

"""
import requests
from bs4 import BeautifulSoup
import socket
import threading
from entities.models import session, Ip_Pool
import uuid
from datetime import datetime


def get_id():
    return str(uuid.uuid4())


header_xici = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'www.xicidaili.com',
    'If-None-Match': 'W/"ec32b847463a566bf6b5e081bd48aec2"',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36'
}

header_sse = {"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
              "Accept-Encoding": "gzip, deflate, br",
              "Accept-Language": "zh-CN,zh;q=0.9",
              "Cache-Control": "max-age=0",
              "Connection": "keep-alive",
              "Referer": "http://www.sse.com.cn/",
              "Host": "www.sse.com.cn",
              "Upgrade-Insecure-Requests": "1",
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36",
              }


def proxys(headers, url):
    html = requests.get(url, headers=headers)
    html.encoding = 'utf-8'
    down_html = html.text
    soup = BeautifulSoup(down_html, 'html.parser')
    ips = soup.findAll('tr')
    proxys_list = []
    for x in xrange(1, len(ips)):
        ip = ips[x]
        tds = ip.findAll("td")
        ip_temp = tds[5].contents[0].lower() + "://" + tds[1].contents[0] + ":" + tds[2].contents[0]
        proxys_list.append(str(ip_temp))
    return proxys_list


class myThread(object):
    def __init__(self, proxys_list, headers):
        self.lock = threading.Lock()  # 建立一个锁
        self.threads = []
        self.proxys_list = proxys_list
        self.headers = headers

    def test(self, i):
        """
        验证代理IP有效性的方法
        """
        socket.setdefaulttimeout(10)  # 设置全局超时时间
        try:
            if "https://" in self.proxys_list[i]:
                proxies = {"https": self.proxys_list[i]}
            elif "http://" in self.proxys_list[i]:
                proxies = {"http": self.proxys_list[i]}
            k = requests.get("http://www.sse.com.cn/", headers=self.headers, proxies=proxies,
                             timeout=5)
            self.lock.acquire()  # 获得锁
            print(self.proxys_list[i], 'is OK')
            ip = self.proxys_list[i]
            ipitem = dict(id=get_id(), ip=ip, updatetime=datetime.now(), datastatus=1)
            session.add(Ip_Pool(**ipitem))
            session.commit()
            self.lock.release()  # 释放锁
        except requests.exceptions.RequestException as e:
            self.lock.acquire()
            print(self.proxys_list[i], e)
            self.lock.release()

    def thread_list(self):
        """
        多线程验证
        """
        for i in range(len(self.proxys_list)):
            thread = threading.Thread(target=self.test, args=[i])
            self.threads.append(thread)
            thread.start()

    def run(self):
        """
       阻塞主进程，等待所有子线程结束
       """
        for thread in self.threads:
            thread.join()


import time

if __name__ == '__main__':
    for i in xrange(1, 20):
        url = 'http://www.xicidaili.com/nn/{}'.format(i)
        proxys_list = proxys(header_xici, url)
        t = myThread(proxys_list, header_sse)
        t.thread_list()
        t.run()

