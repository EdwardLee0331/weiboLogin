import execjs
import requests
import json
import re

def get_runtime(path):
    '''
    path:加密js的路径
    '''
    phantom = execjs.get('PhantomJS')
    with open(path,'r') as f:
        source = f.read()
    return phantom.compile(source)

#获取经过预处理编码的用户名
def get_encodename(name,runtime):
    return runtime.call('get_name',name)

#获取加密后的密码
def get_pass(password,pre_obj,runtime):
    nonce = pre_obj['nonce']
    pubkey = pre_obj['pubkey']
    servertime = pre_obj['servertime']

    return runtime.call('get_pass',password,nonce,servertime,pubkey)

#获取预登录返回信息
def get_prelogin_info(prelogin_url,session):
    json_pattern = r'.*?\((.*)\)'
    reponse = session.get(prelogin_url).text
    m = re.match(json_pattern,reponse)
    return  json.loads(m.group(1))


#进行跳转并判别登录是否成功
def judge(session,login_page):
        pattern = r'location\.replace\([\'"](.*?)[\'"]\)'
        callback_url = re.findall(pattern,login_page)[0]
        login_index = session.get(callback_url)
        domain_pattern = r'"userdomain":"(.*?)"'
        userdomain=re.findall(domain_pattern,login_index.text)[0]
        weibo_url = "https://weibo.com/"+userdomain
        weibo_page = session.get(weibo_url)
        #weibo_pattern = r'<title>(.*?)</title>'
        weibo_pattern ="<em class=(.*?)>(.*?)<(.*?)>"
        user_name = re.findall(weibo_pattern,weibo_page.content)[9][1]
        if user_name != None:
            print u'登录成功:'+ user_name.decode('utf-8')
        else:
            print u'登录失败'

if __name__ == '__main__':
    name = raw_input(u'请输入登录用户名：\n')
    password = raw_input(u'请输入登录密码：\n')
    session = requests.session()
    runtime = get_runtime('login.js')

    su = get_encodename(name,runtime)
    post_url = 'http://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.18)'
    prelogin_url = 'http://login.sina.com.cn/sso/prelogin.php?entry=weibo&callback=sinaSSOController.preloginCallBack&' \
                   'su=' + su + '&rsakt=mod&checkpin=1&client=ssologin.js(v1.4.18)'

    pre_obj = get_prelogin_info(prelogin_url, session)
    sp = get_pass(password, pre_obj, runtime)

    # 提交的数据可以根据抓包获得
    data = {
        'entry': 'weibo',
        'gateway': '1',
        'from': '',
        'savestate': '7',
        'useticket': '1',
        'pagerefer': "http://login.sina.com.cn/sso/logout.php?entry=miniblog&r=http%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl",
        'vsnf': '1',
        'su': su,
        'service': 'miniblog',
        'servertime': pre_obj['servertime'],
        'nonce': pre_obj['nonce'],
        'pwencode': 'rsa2',
        'rsakv': pre_obj['rsakv'],
        'sp': sp,
        'sr': '1366*768',
        'encoding': 'UTF-8',
        'prelt': '115',
        'url': 'http://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack',
        'returntype': 'META',
    }

    login_page = session.post(post_url, data=data)

    login_page = login_page.content.decode('GBK')
    judge(session,login_page)
