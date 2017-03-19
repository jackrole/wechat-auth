# pylint: disable=C0111

from uuid import uuid4

class UserConfig(object):
    wechat_login_domain = 'https://open.weixin.qq.com'

    def __init__(self, user_key):
        self.key = user_key
        self.host = None
        self.unset()

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
        return self.wechat_auth is not None

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
        self.wechat_auth = None

    def set_auth(self, auth_info):
        self.wechat_auth = auth_info

    def unset_auth(self):
        self.wechat_auth = None

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
