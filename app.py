# pylint: disable=C0103, C0111, I0011

from functools import wraps
import re
from urlparse import urlparse, parse_qs, urljoin

from flask import (
    Flask, request, jsonify, render_template, redirect, flash,
    make_response, g, url_for,
)
import requests

from user_config import ConfigSet


app = Flask(__name__)
app.secret_key = '9832jd8jf74jf895kg9ke9frk39fkl'

USER_KEY_NAME = 'WECHAT-AUTH-USER'
CONFIG_SET = ConfigSet()


def require_user_config(func):
    @wraps(func)
    def _require_user_config(*args, **kwargs):
        user_key = request.cookies.get(USER_KEY_NAME)
        g.user_config = CONFIG_SET.get(user_key)
        return func(*args, **kwargs)
    return _require_user_config


@app.route('/', methods=['GET', 'POST'])
@require_user_config
def index():
    user_config = g.user_config

    print request.headers['host']
    if not user_config.host:
        user_config.set(host=request.headers['host'])

    if request.method == 'GET':
        if user_config.is_authenticated:
            path = url_for('auth', user_key=user_config.key)
            host = urlparse(user_config.redirect_uri).netloc
            return render_template(
                'authenticated.html',
                host=host,
                link=urljoin('http://' + user_config.host, path),
            )
        elif user_config.is_configurated:
            qr_page = requests.get(user_config.qr_url).text
            qr_img = urljoin(
                user_config.wechat_login_domain,
                re.findall('img .* src="(.*)"', qr_page)[0],
            )
            qr_id = qr_img.split('/')[-1]
            return render_template('qr.html', qr_img=qr_img, qr_id=qr_id)
        else:
            response = make_response(render_template('index.html'))
            response.set_cookie(USER_KEY_NAME, user_config.key)
            return response

    elif request.method == 'POST':
        qr_url = request.form.get('qr-url', '')
        login_on_browser = request.form.get('login-on-browser', '') == 'on'
        try:
            query_dict = parse_qs(urlparse(qr_url).query, keep_blank_values=True)
            user_config.set(
                appid=list(query_dict['appid'])[0],
                redirect_uri=list(query_dict['redirect_uri'])[0],
                state=list(query_dict['state'])[0].replace('#wechat_redirect', ''),
                login_on_browser=login_on_browser
            )
        except Exception as ex:
            print ex.trace()
            user_config.unset()
            flash('Please input a valid url.')
        return redirect('/')


@app.route('/logout/')
@require_user_config
def logout():
    g.user_config.unset_auth()
    return redirect('/')


@app.route('/clear/')
@require_user_config
def clear_config():
    g.user_config.unset()
    return redirect('/')


@app.route('/query/<qr_id>/')
@app.route('/query/<qr_id>/<last>/')
@require_user_config
def query(qr_id, last=None):
    user_config = g.user_config
    # user_config.print_info()
    query_url = 'https://long.open.weixin.qq.com/connect/l/qrconnect?uuid={uuid}{last}'.format(
        uuid=qr_id,
        last=last and '&last=%s' % last or ''
    )
    # print 'querying: %s' % query_url
    wechat_resp = requests.get(query_url)
    resp_text = wechat_resp.text

    if 'wx_errcode=405' in resp_text:
        redirect_uri = user_config.redirect_uri
        state = user_config.state
        login_on_browser = user_config.login_on_browser

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
                user_config.set_auth(dict(login_resp.cookies))
                login_url = '/'

            return (
                "{resp_text}window.login_url='{login_url}'"
            ).format(
                resp_text=resp_text,
                login_url=login_url,
            )

    return wechat_resp.text


@app.route('/auth/<user_key>')
def auth(user_key):
    user_config = CONFIG_SET.get(user_key)
    response = make_response(jsonify(user_config.wechat_auth))
    for key, value in user_config.wechat_auth.items():
        response.set_cookie(key, value, domain=urlparse(user_config.redirect_uri).netloc)
    return response


@app.route('/cookie1/')
def get_cookie1():
    response = make_response('get cookie1')
    response.set_cookie('cookie1', 'cookie1 value')
    return response


@app.route('/cookie2/')
def get_cookie2():
    response = make_response('get cookie2')
    response.set_cookie('cookie2', 'cookie2 value', domain='www.qichacha.com')
    return response


if __name__ == '__main__':
    app.run(debug=True)
