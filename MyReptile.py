# coding:utf-8
import hashlib
import json
import requests
import time
import random
import logging

from multiprocessing import Pool
from datetime import datetime
from entities.models import session, Sh_A_Share, Sh_Share, Ip_Pool


class MyReptile(object):
    def __init__(self, stock):
        header = {
            "Accept - Ranges": "bytes",
            "Connection": "Keep-Alive",
            "Content-Length": "42625",
            "Content-Type": "text/html",
            "Keep-Alive": "timeout = 10, max = 100",
            "Server": "IBM_HTTP_Server"
        }
        self.stock = stock
        self.referer_header = self.get_header(self.stock["stockcode"])
        self.proxies = self.get_proxies()
        self.check_header = header
        self.page_urls = self.download_page()

    @staticmethod
    def get_header(productId):
        header = {"Accept": "text/html,application/xhtml+xml,application/xml;"
                            "q=0.9,image/webp,image/apng,*/*;q=0.8",
                  "Accept-Encoding": "gzip, deflate, br",
                  "Accept-Language": "zh-CN,zh;q=0.9",
                  "Cache-Control": "max-age=0",
                  "Connection": "keep-alive",
                  "Referer": "http://www.sse.com.cn/",
                  "Host": "query.sse.com.cn",
                  "Upgrade-Insecure-Requests": "1",
                  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) "
                                "Chrome/62.0.3202.89 Safari/537.36",
                  }
        referer = 'http://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?productId={}'.format(
            productId)
        header.update({"Referer": referer})
        return header

    @staticmethod
    def get_url(productId, beginDate, endDate, pageNo, beginPage):
        url = "http://query.sse.com.cn/security/stock/queryCompanyStatementNew.do?jsonCallBack=jsonpCallback18344" \
              "&isPagination=true&productId={}&keyWord=&isNew=1&reportType2=&reportType=ALL&beginDate={}" \
              "&endDate={}&pageHelp.pageSize=25&pageHelp.pageCount=50&pageHelp.pageNo={}&pageHelp.beginPage={}" \
              "&pageHelp.cacheSize=1&pageHelp.endPage=5&_={}".format(productId, beginDate, endDate, pageNo, beginPage,
                                                                     int(time.mktime(datetime.now().timetuple())))
        return url

    def get_page(self, url, proxies):
        try:
            if "https://" in proxies:
                proxie = {"https": proxies}
            elif "http://" in proxies:
                proxie = {"http": proxies}
            else:
                proxie = None
            response = requests.get(url, headers=self.referer_header, proxies=proxie, timeout=5)
            result = response.text.encode('utf-8')
            strJsonData = str(result)[len('jsonpCallback18344') + 1:-1]
            dict_data = dict(json.loads(strJsonData))
            print datetime.now(),len(dict_data["pageHelp"]["data"])
            pagecount = dict_data["pageHelp"]["pageCount"]
            return pagecount
        except requests.RequestException as e:
            print e
            return False

    @staticmethod
    def get_proxies():
        proxies = session.query(Ip_Pool).filter(Ip_Pool.datastatus == 1).all()
        proxielist = []
        for proxie in proxies:
            proxielist.append(proxie.ip)
        return proxielist

    def check_out_base(self, proxys):
        try:
            if "https://" in proxys:
                proxies = {"https": proxys}
            elif "http://" in proxys:
                proxies = {"http": proxys}
            else:
                proxies = None
            k = requests.get("http://www.sse.com.cn/", headers=self.check_header, proxies=proxies, timeout=5)
            k.raise_for_status()
        except requests.exceptions.RequestException as e:
            print e
            return False
        else:
            return True

    def check_out(self):
        while 1:
            proxie = self.proxies[random.randint(0, len(self.proxies))]
            if self.check_out_base(proxie):
                result = proxie
                break
            else:
                session.query(Ip_Pool).filter(Ip_Pool.ip == proxie).update({Ip_Pool.datastatus: 2})
                session.commit()
                continue
        return result

    def download_page(self):
        urls = []
        for t in xrange(4):
            proxie = self.check_out()
            beginDate = str(2014 + t) + '-01-01'
            endDate = str(2015 + t) + '-01-01'

            stock_url = self.get_url(productId=self.stock["stockcode"], beginDate=beginDate, endDate=endDate, pageNo=1,
                                     beginPage=1)
            pagecount = self.get_page(stock_url, proxie)
            for i in xrange(1, pagecount + 1):
                stock_url = self.get_url(productId=self.stock["stockcode"], beginDate=beginDate, endDate=endDate,
                                         pageNo=i,
                                         beginPage=i)
                urls.append(stock_url)
            time.sleep(5)

        return urls


def get_stock():
    stocks = session.query(Sh_Share).all()
    data = []
    for stock in stocks:
        base = stock.__dict__
        base.pop('_sa_instance_state')
        base.pop('companycode')
        base.pop('companyname')
        data.append(base)
    return data


def check_out_base(proxys, check_header):
    try:
        if "https://" in proxys:
            proxies = {"https": proxys}
        elif "http://" in proxys:
            proxies = {"http": proxys}
        else:
            proxies = None
        k = requests.get("http://www.sse.com.cn/", headers=check_header, proxies=proxies, timeout=5)
        k.raise_for_status()
    except requests.exceptions.RequestException as e:
        print e
        return False
    else:
        return True


def check_out(proxies, check_header):
    while 1:
        proxie = proxies[random.randint(0, len(proxies))]
        if check_out_base(proxie, check_header):
            result = proxie
            break
        else:
            session.query(Ip_Pool).filter(Ip_Pool.ip == proxie).update({Ip_Pool.datastatus: 2})
            session.commit()
            continue
    return result


def download_data(url, referer_header, stock, proxies, check_header):
    proxies_down = check_out(proxies, check_header)
    time.sleep(5)
    if "https://" in proxies_down:
        proxie = {"https": proxies_down}
    elif "http://" in proxies_down:
        proxie = {"http": proxies_down}
    else:
        proxie = None
    response = requests.get(url, headers=referer_header, proxies=proxie, timeout=5)
    result = response.text.encode('utf-8')
    strJsonData = str(result)[len('jsonpCallback18344') + 1:-1]
    dict_data = dict(json.loads(strJsonData))
    for i in dict_data["pageHelp"]["data"]:
        pdfurl = 'http://static.sse.com.cn' + i["URL"]
        bulletinid = hashlib.md5(pdfurl).hexdigest()
        data_base = dict(bulletinid=bulletinid, stockcode=i["security_Code"], stockname=stock["stockname"],
                         title=i["title"],
                         category=i["bulletin_Type"], url=pdfurl, bulletinyear=i["bulletin_Year"],
                         bulletindate=i["SSEDate"], uploadtime=datetime.now(), datastatus=1)
        try:
            session.add(Sh_A_Share(**data_base))
            session.commit()
        except:
            session.rollback()


def download_pool(urls, proxies, check_header, referer_header, stock):
    pool = Pool(processes=4)
    for i in xrange(len(urls)):
        pool.apply_async(download_data, (urls[i], referer_header, stock, proxies, check_header))
    pool.close()
    pool.join()
    print 'down_success'


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename='timelog.log',
                        filemode='a')
    print '{}:start'.format(datetime.now())
    stocks = get_stock()
    for i in stocks:
        stock = i
        print stock
        k = MyReptile(stock)
        start = time.time()
        download_pool(urls=k.page_urls, proxies=k.proxies, check_header=k.check_header, referer_header=k.referer_header,
                      stock=k.stock)
        end = time.time()
        msg = '股票代码：{},股票名称：{},耗时：{}s,日期：{}'.format(stock["stockcode"], stock["stockname"].encode('utf-8'), end - start,
                                                    datetime.now())
        logging.info(msg)
        time.sleep(5)
    print '{}:end'.format(datetime.now())
