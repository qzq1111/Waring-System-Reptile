# coding:utf-8
import hashlib
import json
import requests
import time
import random
import logging
import threading

from datetime import datetime,timedelta
from apscheduler.schedulers.blocking import BlockingScheduler
from entities.models import session, Sh_A_Share, Sh_Share, Ip_Pool


class MyTimingReptile(object):
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
                  "User-Agent": None
                  }
        referer = 'http://www.sse.com.cn/assortment/stock/list/info/announcement/index.shtml?productId={}'.format(
            productId)
        header.update({"Referer": referer})
        uaList = [
            'Mozilla/4.0+(compatible;+MSIE+6.0;+Windows+NT+5.1;+SV1;+.NET+CLR+1.1.4322;+TencentTraveler)',
            'Mozilla/4.0+(compatible;+MSIE+6.0;+Windows+NT+5.1;+SV1;+.NET+CLR+2.0.50727;+.NET+CLR+3.0.4506.2152;+.NET+CLR+3.5.30729)',
            'Mozilla/5.0+(Windows+NT+5.1)+AppleWebKit/537.1+(KHTML,+like+Gecko)+Chrome/21.0.1180.89+Safari/537.1',
            'Mozilla/4.0+(compatible;+MSIE+6.0;+Windows+NT+5.1;+SV1)',
            'Mozilla/5.0+(Windows+NT+6.1;+rv:11.0)+Gecko/20100101+Firefox/11.0',
            'Mozilla/4.0+(compatible;+MSIE+8.0;+Windows+NT+5.1;+Trident/4.0;+SV1)',
            'Mozilla/4.0+(compatible;+MSIE+8.0;+Windows+NT+5.1;+Trident/4.0;+GTB7.1;+.NET+CLR+2.0.50727)',
            'Mozilla/4.0+(compatible;+MSIE+8.0;+Windows+NT+5.1;+Trident/4.0;+KB974489)',
            'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
            'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/30.0.1599.101 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.89 Safari/537.36',
        ]
        ua = random.choice(uaList)
        header.update({"User-Agent": ua})
        return header

    @staticmethod
    def get_url(productId, beginDate, endDate, pageNo, beginPage):
        jsonpCallback = 'jsonpCallback' + str(random.randint(1000, 99999))
        url = "http://query.sse.com.cn/security/stock/queryCompanyStatementNew.do?jsonCallBack={}" \
              "&isPagination=true&productId={}&keyWord=&isNew=1&reportType2=&reportType=ALL&beginDate={}" \
              "&endDate={}&pageHelp.pageSize=25&pageHelp.pageCount=50&pageHelp.pageNo={}&pageHelp.beginPage={}" \
              "&pageHelp.cacheSize=1&pageHelp.endPage=5&_={}".format(jsonpCallback, productId, beginDate, endDate,
                                                                     pageNo, beginPage,
                                                                     int(time.mktime(datetime.now().timetuple())))
        return url

    def get_page(self, url):
        while 1:
            proxies = self.check_out()
            if "https://" in proxies:
                proxie = {"https": proxies}
            elif "http://" in proxies:
                proxie = {"http": proxies}
            else:
                proxie = None
            try:
                response = requests.get(url, headers=self.referer_header, proxies=proxie, timeout=5)
            except requests.RequestException as e:
                print e
                continue
            else:
                result = response.text.encode('utf-8')
                strresult = str(result)
                try:
                    strJsonData = strresult[strresult.find('(') + 1:strresult.rfind(')')]
                    dict_data = dict(json.loads(strJsonData))
                except Exception as e:
                    print e
                    continue
                else:
                    print datetime.now(), len(dict_data["pageHelp"]["data"])
                    pagecount = dict_data["pageHelp"]["pageCount"]
                    return pagecount



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
            proxie = self.proxies[random.randint(0, len(self.proxies) - 1)]
            if self.check_out_base(proxie):
                result = proxie
                break
            else:
                session.query(Ip_Pool).filter(Ip_Pool.ip == proxie).update({Ip_Pool.datastatus: 2})
                session.commit()
                time.sleep(5)
                continue
        return result

    def download_page(self):
        urls = []
        beginDate = str(datetime.date(datetime.now()) - timedelta(days=1))
        endDate = str(datetime.date(datetime.now()))

        stock_url = self.get_url(productId=self.stock["stockcode"], beginDate=beginDate, endDate=endDate, pageNo=1,
                                 beginPage=1)
        pagecount = self.get_page(stock_url)
        for i in xrange(1, pagecount + 1):
            stock_url = self.get_url(productId=self.stock["stockcode"], beginDate=beginDate, endDate=endDate,
                                     pageNo=i,
                                     beginPage=i)
            urls.append(stock_url)
        time.sleep(5)
        return urls


def get_stock():
    stocks = session.query(Sh_Share).filter(Sh_Share.datastatus == 2).all()
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
        proxie = proxies[random.randint(0, len(proxies) - 1)]
        if check_out_base(proxie, check_header):
            result = proxie
            break
        else:
            session.query(Ip_Pool).filter(Ip_Pool.ip == proxie).update({Ip_Pool.datastatus: 2})
            session.commit()
            time.sleep(5)
            continue
    return result


def download_data(url, referer_header, stock, proxies, check_header):
    while 1:
        proxies_down = check_out(proxies, check_header)
        if "https://" in proxies_down:
            proxie = {"https": proxies_down}
        elif "http://" in proxies_down:
            proxie = {"http": proxies_down}
        else:
            proxie = None
        try:
            response = requests.get(url, headers=referer_header, proxies=proxie, timeout=5)
            response.raise_for_status()
            status_code = response.status_code
        except requests.exceptions.RequestException as e:
            print e
            status_code = 400
            response = None
        if status_code < 300 and response is not None:
            result = response.text.encode('utf-8')
            strresult = str(result)
            try:
                strJsonData = strresult[strresult.find('(') + 1:strresult.rfind(')')]
                dict_data = dict(json.loads(strJsonData))
            except Exception as e:
                print e
                time.sleep(5)
                continue
            else:
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
                break
        else:
            time.sleep(5)
            continue


class myThread(threading.Thread):
    def __init__(self, urls, proxies, check_header, referer_header, stock):
        threading.Thread.__init__(self)
        self.urls = urls
        self.proxies = proxies
        self.check_header = check_header
        self.referer_header = referer_header
        self.stock = stock

    def run(self):
        threadLock.acquire()
        download_data(self.urls, self.referer_header, self.stock, self.proxies, self.check_header)
        threadLock.release()


def try_timing():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s:%(levelname)s:%(name)s:%(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        filename='timelog.log',
                        filemode='a')
    print '{}:start'.format(datetime.now())
    stocks = get_stock()
    for i in stocks:
        threads = []
        stock = i
        print stock
        k = MyTimingReptile(stock)
        start = time.time()
        for dd in k.page_urls:
            thread = myThread(urls=dd, proxies=k.proxies, check_header=k.check_header, referer_header=k.referer_header,
                              stock=k.stock)
            thread.start()
            threads.append(thread)
        for t in threads:
            t.join()
        print 'down_success'
        end = time.time()
        msg = '股票代码：{},股票名称：{},耗时：{}s,日期：{}'.format(stock["stockcode"], stock["stockname"].encode('utf-8'), end - start,
                                                    datetime.now())
        logging.info(msg)
        time.sleep(5)
    print '{}:end'.format(datetime.now())


if __name__ == '__main__':
    threadLock = threading.Lock()
    scheduler = BlockingScheduler()
    scheduler.add_job(
        func=try_timing,
        trigger='cron',
        hour=24,
        id='try_timing',
        name='try_timing',
        replace_existing=True
    )
    scheduler.start()