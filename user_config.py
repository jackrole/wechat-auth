# pylint: disable=C0111

from urlparse import urlparse
from uuid import uuid4

class UserConfig(object):
    wechat_login_domain = 'https://open.weixin.qq.com'

    def __init__(self, user_key):
        self.key = user_key
        self.request_host = None

        # for wechat app
        self.appid = ''
        self.redirect_uri = ''
        self.state = ''
        # for wechat-auth
        self.login_on_browser = False
        # informations of the site to login
        self.target_site_host = None
        self.target_site_homepage = None
        self.target_site_auth_info = None

    @property
    def qr_url(self):
        return (
            '{wechat_login_domain}/connect/qrconnect'
            '?appid={appid}'
            '&redirect_uri={redirect_uri}'
            '&state={state}'
            '&response_type=code'
            '&scope=snsapi_login'
        ).format(
            wechat_login_domain=self.wechat_login_domain,
            appid=self.appid,
            redirect_uri=self.redirect_uri,
            state=self.state,
        )

    @property
    def is_configurated(self):
        return self.appid and self.redirect_uri

    @property
    def is_authenticated(self):
        return self.target_site_auth_info is not None

    def set(self, **kwargs):
        for key in kwargs:
            if hasattr(self, key):
                setattr(self, key, kwargs[key])

    def unset(self):
        # for wechat app
        self.appid = ''
        self.redirect_uri = ''
        self.state = ''
        # for wechat-auth
        self.login_on_browser = False
        # wechat authcation information
        self.target_site_auth_info = None
        self.target_site_homepage = None
        self.target_site_auth_info = None

    def set_auth(self, auth_info):
        self.target_site_auth_info = auth_info

    def unset_auth(self):
        self.target_site_auth_info = None

    def get_target_site_host(self):
        if self.target_site_host:
            return self.target_site_host
        return urlparse(self.redirect_uri).netloc

    def get_target_site_homepage(self):
        if self.target_site_homepage:
            return self.target_site_homepage
        return 'http://%s' % self.get_target_site_host()

    def print_info(self):
        print (
            '------------------\n'
            'appid={appid}\n'
            'redirect_uri={redirect_uri}\n'
            'state={state}\n'
            'login_on_browser={login_on_browser}\n'
            '------------------'
        ).format(
            appid=self.appid,
            redirect_uri=self.redirect_uri,
            state=self.state,
            login_on_browser=str(self.login_on_browser),
        )


class ConfigSet(object):
    def __init__(self):
        self.__config_set = {}

    def get(self, user_key):
        config_set = self.__config_set
        if not user_key:
            user_key = str(uuid4()).replace('-', '')
        if user_key in config_set:
            return config_set[user_key]
        else:
            config = UserConfig(user_key)
            config_set[user_key] = config
            return config
