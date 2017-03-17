# pylint: disable=C0103, C0111, I0011

import re
from urlparse import urlparse, parse_qs

from flask import (
    Flask, request, jsonify,
    render_template, redirect, flash
)
import requests

app = Flask(__name__)
app.secret_key = '9832jd8jf74jf895kg9ke9frk39fkl'

wechat_login_domain = 'https://open.weixin.qq.com'


# app configuration
# appid = 'wx9b26295cdfab4175'
# redirect_uri = 'http://www.qichacha.com/user_wxloginok'
# state = '#wechat_redirect'

# appid = 'wxccea2c54ef6ceb42'
# redirect_uri = 'http://www.xuetangx.com/complete/weixin/'
# state = ''


APP_CONFIG = {
    # for wechat app
    'appid': 'wx9b26295cdfab4175',
    'redirect_uri': 'http://www.qichacha.com/user_wxloginok',
    'state': '#wechat_redirect',
    # for wechat-auth
    'qr_img': None,
    'qr_id': None,
    'login_on_browser': False,
}

APP_CONFIG = {}
AUTH_INFO = {}


def validate_sessid():
    if not APP_CONFIG:
        return False
    return True


def get_qr_url():
    return (
        '{wechat_login_domain}/connect/qrconnect'
        '?appid={appid}'
        '&redirect_uri={redirect_uri}'
        '&state={state}'
        '&response_type=code'
        '&scope=snsapi_login'
    ).format(
        wechat_login_domain=wechat_login_domain,
        appid=APP_CONFIG['appid'],
        redirect_uri=APP_CONFIG['redirect_uri'],
        state=APP_CONFIG['state'],
    )


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        if not APP_CONFIG:
            return render_template('index.html')
        elif not AUTH_INFO:
            qr_page = requests.get(get_qr_url()).text
            qr_img = wechat_login_domain + re.findall('img .* src="(.*)"', qr_page)[0]

            APP_CONFIG['qr_id'] = qr_img.split('/')[-1]
            APP_CONFIG['qr_img'] = qr_img
            return render_template('qr.html', qr_img=APP_CONFIG['qr_img'])
        else:
            return 'Login succeed, you can use the api now.'

    elif request.method == 'POST':
        global APP_CONFIG

        qr_url = request.form.get('qr-url', '')
        login_on_browser = request.form.get('login-on-browser', '') == 'on'
        try:
            query_dict = parse_qs(urlparse(qr_url).query)
            APP_CONFIG['appid'] = query_dict['appid'][0]
            APP_CONFIG['redirect_uri'] = query_dict['redirect_uri'][0]
            APP_CONFIG['state'] = query_dict['state'][0].replace('#wechat_redirect', '')
            APP_CONFIG['login_on_browser'] = login_on_browser
        except:  # pylint: disable=W0702
            APP_CONFIG = {}
            flash('Please input a valid url.')
        return redirect('/')


@app.route('/logout/')
def logout():
    global AUTH_INFO
    AUTH_INFO = {}
    return redirect('/')


@app.route('/clear/')
def clear_config():
    global APP_CONFIG, AUTH_INFO
    APP_CONFIG = {}
    AUTH_INFO = {}
    return redirect('/')


@app.route('/query/')
@app.route('/query/<last>/')
def query(last=None):
    query_url = 'https://long.open.weixin.qq.com/connect/l/qrconnect?uuid={uuid}{last}'.format(
        uuid=APP_CONFIG['qr_id'],
        last=last and '&last=%s' % last or ''
    )
    wechat_resp = requests.get(query_url)
    resp_text = wechat_resp.text

    if 'wx_errcode=405' in resp_text:
        global AUTH_INFO

        redirect_uri = APP_CONFIG['redirect_uri']
        state = APP_CONFIG['state']
        login_on_browser = APP_CONFIG['login_on_browser']

        wx_code = re.findall("wx_code='(.*)';", resp_text)[0]
        if wx_code:
            login_url = redirect_uri + '{split}code={wx_code}{state}'.format(
                split='&' if '?' in redirect_uri else '?',
                wx_code=wx_code,
                state=('&state=%s' % state) if state else '',
            )

            # request the login url in backend.
            if not login_on_browser:
                login_resp = requests.get(login_url, allow_redirects=False)
                AUTH_INFO = dict(login_resp.cookies)
                login_url = '/'

            return (
                "{resp_text}window.login_url='{login_url}'"
            ).format(
                resp_text=resp_text,
                login_url=login_url,
            )

    return wechat_resp.text


if __name__ == '__main__':
    app.run(debug=True)
