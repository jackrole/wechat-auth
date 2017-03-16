# pylint: disable=C0103, C0111

import re
from urlparse import urlparse

from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

wechat_login_domain = 'https://open.weixin.qq.com'

# app configuration
appid = 'wx9b26295cdfab4175'
redirect_uri = 'http://www.qichacha.com/user_wxloginok'

url = (
    '{wechat_login_domain}/connect/qrconnect'
    '?appid={appid}'
    '&redirect_uri={redirect_uri}'
    '&response_type=code'
    '&scope=snsapi_login'
    '&state=#wechat_redirect'
).format(
    wechat_login_domain=wechat_login_domain,
    appid=appid,
    redirect_uri=redirect_uri,
)


@app.route('/')
def index():
    qr_page = requests.get(url).text
    qr_img = wechat_login_domain + re.findall('img .* src="(.*)"', qr_page)[0]
    qr_id = qr_img.split('/')[-1]
    return render_template('index.html', qr_img=qr_img, qr_id=qr_id, redirect_uri=redirect_uri)


@app.route('/query/<qr_id>/')
@app.route('/query/<qr_id>/<last>/')
def query(qr_id, last=None):
    query_url = 'https://long.open.weixin.qq.com/connect/l/qrconnect?uuid={uuid}{last}'.format(
        uuid=qr_id,
        last=last and '&last=%s' % last or ''
    )
    wechat_resp = requests.get(query_url)
    resp_text = wechat_resp.text
    if 'wx_errcode=405' in resp_text:
        wx_code = re.findall("wx_code='(.*)';", resp_text)[0]
        if wx_code:
            print 'get wx_code %s' % wx_code
            login_url = redirect_uri + '{split}code={wx_code}'.format(
                split='?' in redirect_uri and '&' or '?',
                wx_code=wx_code
            )

            login_resp = requests.get(login_url, allow_redirects=False)

            # return jsonify(login_resp.cookies), 405
            php_sessid = dict(login_resp.cookies)['PHPSESSID']
            domain = urlparse(login_url).netloc.lstrip('www.')
            set_cookies_js = (
                "$.cookie('PHPSESSID', '{php_sessid}', {{domain: '{domain}', path: '/'}});"
            ).format(
                php_sessid=php_sessid,
                domain=domain,
            )
            print set_cookies_js
            return (
                resp_text + "window.login_url='%s';window.wx_code='%s';%s"
            ) % (login_url, wx_code, set_cookies_js)

    return wechat_resp.text


if __name__ == '__main__':
    app.run(debug=True)
