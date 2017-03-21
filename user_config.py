# pylint: disable=C0111

from urlparse import urlparse
from uuid import uuid4


class UserConfig(object):
    wechat_login_domain = 'https://open.weixin.qq.com'

    def __init__(self):
        self.key = str(uuid4()).replace('-', '')
        self.request_host = None

        # for wechat app
        self.appid = None
        self.redirect_uri = None
        self.state = None
        # for wechat-auth(current app)
        self.auth_method = None
        # informations of the site to login
        self.target_site_session = None
        self.target_site_name = None
        self.target_site_host = None
        self.target_site_homepage = None
        self.target_site_login_uri = None
        self.target_site_auth_info = None

    # @property
    # def qr_url(self):
    #     return (
    #         '{wechat_login_domain}/connect/qrconnect'
    #         '?appid={appid}'
    #         '&redirect_uri={redirect_uri}'
    #         '&state={state}'
    #         '&response_type=code'
    #         '&scope=snsapi_login'
    #     ).format(
    #         wechat_login_domain=self.wechat_login_domain,
    #         appid=self.appid,
    #         redirect_uri=self.redirect_uri,
    #         state=self.state,
    #     )

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

    def clear(self):
        # for wechat app
        self.appid = None
        self.redirect_uri = None
        self.state = None
        # for wechat-auth(current app)
        self.auth_method = None
        # informations of the site to login
        self.target_site_name = None
        self.target_site_host = None
        self.target_site_homepage = None
        self.target_site_login_uri = None
        self.target_site_auth_info = None

    def set_auth(self, auth_info):
        self.target_site_auth_info = auth_info

    def clear_auth(self):
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
            'auth_method={auth_method}\n'
            '------------------'
        ).format(
            appid=self.appid,
            redirect_uri=self.redirect_uri,
            state=self.state,
            auth_method=self.auth_method,
        )


class ConfigSet(object):
    def __init__(self):
        self.__config_set = {}

    def get(self, user_key):
        config_set = self.__config_set
        if user_key in config_set:
            return config_set[user_key]
        else:
            config = UserConfig()
            config_set[config.key] = config
            return config
