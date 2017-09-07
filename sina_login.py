import time
import base64
import rsa
import math
import random
import binascii
import requests
import json
import re
import urlparse
import urllib

class YDMHttp(object):
    apiurl = 'http://api.yundama.com/api.php'
    username = ''
    password = ''
    appid = ''
    appkey = ''

    def __init__(self,username,password,app_id,app_key):
        self.username=username
        self.password = password
        self.appid = str(app_id)
        self.appkey = app_key

    def request(self, fields, files=[]):
        try:
            response = self.post_url(self.apiurl, fields, files)
            response = json.loads(response)
        except Exception as e:
            response = None
        return response

    def balance(self):
        data = {'method': 'balance', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey}
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['balance']
        else:
            return -9001

    def login(self):
        data = {'method': 'login', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey}
        print data
        response = self.request(data)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['uid']
        else:
            return -9001

    def upload(self, filename, codetype, timeout):
        data = {'method': 'upload', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey, 'codetype': str(codetype), 'timeout': str(timeout)}
        file = {'file': filename}
        response = self.request(data, file)
        if (response):
            if (response['ret'] and response['ret'] < 0):
                return response['ret']
            else:
                return response['cid']
        else:
            return -9001

    def result(self, cid):
        data = {'method': 'result', 'username': self.username, 'password': self.password, 'appid': self.appid, 'appkey': self.appkey, 'cid': str(cid)}
        response = self.request(data)
        return response and response['text'] or ''

    def decode(self, filename, codetype, timeout):
        cid = self.upload(filename, codetype, timeout)
        if (cid > 0):
            for i in range(0, timeout):
                result = self.result(cid)
                if (result != ''):
                    return cid, result
                else:
                    time.sleep(1)
            return -3003, ''
        else:
            return cid, ''
        
    def post_url(self, url, fields, files=[]):
        for key in files:
            files[key] = open(files[key], 'rb')
        res = requests.post(url, files=files, data=fields)
        return res.text

def captcha_verify():
    username = ''
    password = ''
    appid = 3977
    appkey = '39245fed6cdcd19605c4c06a539606f5'
    codetype= 1004
    filename = 'captcha.jpg'
    timeout = 60
    yundama = YDMHttp(username,password,appid,appkey)
    uid = yundama.login()
    #print 'uid:%s' % uid
    #balance = yundama.balance()
    #print 'balance:%s' % balance
    cid,result = yundama.decode(filename,codetype,timeout)
    #print 'cid:%s,result:%s' %(cid,result)
    return result
    

class weiboLogin(object):
    def __init__(self):
        self.session = requests.session()
        self.header = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0'
                }
        self.username = raw_input(u'用户名:')
        self.password = raw_input(u'密码:')
        self.filename = 'captcha.jpg'
        


    def login(self):
        su = self.su(self.username)
        serverData = self.server_data(su)
        nonce = serverData["nonce"]
        servertime = serverData['servertime']
        rsakv = serverData['rsakv']
        pubkey = serverData['pubkey']
        password_secret = self.get_pass(self.password,servertime,nonce,pubkey)
        
        postdata={
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'useticket': '1',
        'pagerefer': "http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl",
        'vsnf': '1',
        'su': su,
        'service': 'miniblog',
        'servertime': servertime,
        'nonce': nonce,
        'pwencode': 'rsa2',
        'rsakv': rsakv,
        'sp': password_secret,
        'sr': '1366*768',
        'encoding': 'UTF-8',
        'prelt': '115',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'returntype': 'META'
        }

        need_pin = serverData['showpin']
        if need_pin == 1:
            pcid  = saver_data['pcid']
            postdata['pcid'] = pcid
            img_url = self.get_pincode_url(pcid)
            self.get_img(img_url)
            door = captcha_verify()
            post['door'] = door

        login_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
        login_page = self.session.post(login_url,data=postdata,headers=self.header)
        login_page = login_page.content.decode("GBK")
        self.judge(login_page)

    def judge(self,login_page):
        pattern = r'location\.replace\([\'"](.*?)[\'"]\)'
        callback_url = re.findall(pattern,login_page)[0]
        login_index = self.session.get(callback_url,headers=self.header)
        domain_pattern = r'"userdomain":"(.*?)"'
        userdomain=re.findall(domain_pattern,login_index.text)[0]
        weibo_url = "https://weibo.com/"+userdomain
        weibo_page = self.session.get(weibo_url,headers=self.header)
        #weibo_pattern = r'<title>(.*?)</title>'
        weibo_pattern ="<em class=(.*?)>(.*?)<(.*?)>"
        user_name = re.findall(weibo_pattern,weibo_page.content)[9][1]
        if user_name != None:
            print u'登录成功:'+ user_name.decode('utf-8')
        else:
            print u'登录失败'
        
    def get_pincode_url(self,pcid):
        size = 0
        url = "http://login.sina.com.cn/cgi/pin.php"
        pincode_url = "{}?r={}&s={}&p={}",format(url,math.floor(random.random()*100000000),size,pcid)
        return pincode_url

    def get_img(self,url):
        resp = requests.get(url,headers=self.header,stream=True)
        with open(self.filename,'wb') as f:
            for chunk in resp.iter_content(1000):
                f.write(chunk)
        
    def su(self,username):
        username = urllib.quote_plus(username)
        username = base64.b64encode(username)
        return username

    def server_data(self,su):
        prelogin_url = "http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&su="
        prelogin_url = prelogin_url + su + "&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)&_="
        prelogin_url = prelogin_url + str(int(time.time()*1000))
        prelogin = self.session.get(prelogin_url,headers=self.header)

        server_data = eval(prelogin.content.decode("utf-8").replace("sinaSSOController.preloginCallBack",''))
        return server_data

    def get_pass(self,password,servertime,nonce,pubkey):
        publicKey = int(pubkey,16)
        key = rsa.PublicKey(publicKey,65537)
        message = str(servertime) + '\t' + str(nonce) + '\n' + str(password)
        message = message.encode('utf-8')
        password = rsa.encrypt(message,key)
        password = binascii.b2a_hex(password)
        return password

        
if __name__ == '__main__':
    weibo = weiboLogin()
    weibo.login()
    

