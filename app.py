# pylint: disable=C0103, C0111, I0011

from collections import OrderedDict
from functools import wraps
import logging
import re
from urlparse import urlparse, parse_qs, urljoin

from flask import (
    Flask, request, jsonify, render_template, redirect, flash,
    make_response, g, url_for,
)
import requests

from user_config import ConfigSet


WECHAT_AUTH_DOMAIN = 'open.weixin.qq.com'
WECHAT_QRIMG_REGEX = r'img .* src="(.*)"'
WECHAT_SITENAME_REGEX = r'id="wx_default_tip"[\s\S]*?<p>[\s\S]*?<p>(.*)</p>'


HEADERS = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4',
    'Host': 'www.xuetangx.com',
    'Pragma': 'no-cache',
    'Referer': 'http://www.xuetangx.com/',
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
        ' AppleWebKit/537.36 (KHTML, like Gecko)'
        ' Chrome/56.0.2924.87 Safari/537.36'
    ),
}


AUTH_METHODS = OrderedDict([
    ('backend_login', 'Create login authencate api'),
    ('login_on_browser', 'Login on browser'),
    ('return_login_uri', 'Return login link'),
])


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

    if not user_config.request_host:
        user_config.set(request_host=request.headers['host'])

    if request.method == 'GET':
        if user_config.is_authenticated:
            '''
            It means that the login url was visited and related authentication
            tokens are stored by wechat-auth backend. So here providing a link
            for user to get these authentication tokens throught it.

            Beyond the link, some examples are listed to show how to query the
            tokens above which are written in several different language.
            '''
            path = url_for('auth', user_key=user_config.key)
            return render_template(
                'authenticated.html',
                host=user_config.get_target_site_host(),
                link=urljoin('http://' + user_config.request_host, path),
            )
        elif user_config.target_site_login_uri:
            '''
            Return the login url of the target website to frontend.

            User can click the link to login into the target website, but it
            maybe not work if the website requires a complicated login strategy.

            `target_site_login_uri` will only be set while:
                user_config.auth_method == 'return_login_uri'
                ** see query() method **
            '''
            return render_template(
                'login_uri.html',
                link=user_config.target_site_login_uri,
                site_name=user_config.target_site_name,
            )
        elif user_config.is_configurated:
            '''
            Visit wechat QR scan page to get the QR image and site name.
            After saving the necessary information, send the QR image to
            user for QR scaning.

            Should maintenance the Regular Expressions in case of wechat
            changes its QR scan page.
            '''
            qr_page = requests.get(_get_wechat_qr_scan_url(user_config)).text
            qr_img = urljoin(
                user_config.wechat_login_domain,
                re.findall(WECHAT_QRIMG_REGEX, qr_page)[0],
            )
            qr_id = qr_img.split('/')[-1]
            site_name = re.findall(WECHAT_SITENAME_REGEX, qr_page)[0]
            user_config.set(site_name=site_name)
            return render_template(
                'qr.html', qr_img=qr_img, qr_id=qr_id, site_name=site_name,
            )
        else:
            response = make_response(render_template(
                'index.html', auth_methods=AUTH_METHODS,
            ))
            response.set_cookie(USER_KEY_NAME, user_config.key)
            return response

    elif request.method == 'POST':
        qr_url = request.form.get('qr-url', '')
        auth_method = request.form.get('auth-method', 'backend_login')
        try:
            parsed = urlparse(qr_url)

            '''If the given url is not a valid wechat QR scan page url,
            visit the given url and try to get the real QR scan url.'''
            if parsed.netloc != WECHAT_AUTH_DOMAIN:
                '''Use session to store all the cookies which maybe useful
                for login process.'''
                session = requests.Session()
                response = session.get(qr_url)
                parsed = urlparse(response.url)
                if parsed.netloc != WECHAT_AUTH_DOMAIN:
                    user_config.clear()
                    flash('The url given is not supported to do wechat login.')
                    flash(qr_url)
                    parsed = None
                else:
                    # Save the session for further login process.
                    user_config.set(target_site_session=session)

            if parsed:
                # Get user config information from QR scan url.
                query_dict = parse_qs(parsed.query, keep_blank_values=True)
                user_config.set(
                    appid=list(query_dict['appid'])[0],
                    redirect_uri=list(query_dict['redirect_uri'])[0],
                    state=list(query_dict['state'])[0].replace('#wechat_redirect', ''),
                    auth_method=auth_method,
                )
            user_config.print_info()

        except Exception as ex:
            logging.error(ex, exc_info=1)
            user_config.clear()
            flash('Please input a valid url.')
            flash(qr_url)
        return redirect('/')


def _get_wechat_qr_scan_url(user_config):
    return (
        'https://'
        '{wechat_auth_domain}/connect/qrconnect'
        '?appid={appid}'
        '&redirect_uri={redirect_uri}'
        '&state={state}'
        '&response_type=code'
        '&scope=snsapi_login'
    ).format(
        wechat_auth_domain=WECHAT_AUTH_DOMAIN,
        appid=user_config.appid,
        redirect_uri=user_config.redirect_uri,
        state=user_config.state,
    )


@app.route('/query/<qr_id>/')
@app.route('/query/<qr_id>/<last>/')
@require_user_config
def query(qr_id, last=None):
    user_config = g.user_config
    query_url = 'https://long.open.weixin.qq.com/connect/l/qrconnect?uuid={uuid}{last}'.format(
        uuid=qr_id,
        last=last and '&last=%s' % last or ''
    )
    wechat_resp = requests.get(query_url)
    resp_text = wechat_resp.text

    if 'wx_errcode=405' in resp_text:
        redirect_uri = user_config.redirect_uri
        state = user_config.state

        wx_code = re.findall("wx_code='(.*)';", resp_text)[0]
        if wx_code:
            login_url = redirect_uri + '{split}code={wx_code}{state}'.format(
                split='&' if '?' in redirect_uri else '?',
                wx_code=wx_code,
                state=('&state=%s' % state) if state else '',
            )

            if user_config.auth_method == 'backend_login':
                session = user_config.target_site_session or requests.Session()
                get = lambda url: session.get(url, headers=HEADERS)
                get(user_config.get_target_site_homepage())
                get(login_url)

                user_config.set_auth(dict(session.cookies))
                login_url = '/'

            elif user_config.auth_method == 'return_login_uri':
                user_config.target_site_login_uri = login_url
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
    response = make_response(jsonify(user_config.target_site_auth_info))
    for key, value in user_config.target_site_auth_info.items():
        response.set_cookie(key, value, domain=urlparse(user_config.redirect_uri).netloc)
    return response


@app.route('/logout/')
@require_user_config
def logout():
    g.user_config.clear_auth()
    return redirect('/')


@app.route('/clear/')
@require_user_config
def clear_config():
    g.user_config.clear()
    return redirect('/')


if __name__ == '__main__':
    app.run(debug=True)
