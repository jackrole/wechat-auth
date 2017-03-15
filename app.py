import re

from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

url = 'https://open.weixin.qq.com/connect/qrconnect?appid=wx9b26295cdfab4175&redirect_uri=http://www.qichacha.com/user_wxloginok&response_type=code&scope=snsapi_login&state=#wechat_redirect'

@app.route('/')
def index():
    qr_page = requests.get(url).text
    qr_img = 'https://open.weixin.qq.com' + re.findall('img .* src="(.*)"', qr_page)[0]
    return render_template('index.html', qr_img=qr_img)


@app.route('/query/')
def query():
    return requests.get('https://long.open.weixin.qq.com/connect/l/qrconnect?uuid=051mQbP4eybRtHqc&_=1489594479520')


if __name__ == '__main__':
    app.run(debug=True)
