#!/usr/bin/python

import getopt
import sys
import re

import requests
from flask import Flask
from flask import redirect

app = Flask(__name__)

login = ''
password = ''

session = ''

defaultHeaders = {
    "Content-Type": "application/x-www-form-urlencoded",
    "Referer": "https://vs.domru.ru/login.html",
    "X-Requested-With": "XMLHttpRequest",
}

cameraHeaders = {
    "Connection": 'keep-alive',
    "Referer": 'https://vs.domru.ru/login.html',
    "Host": 'vs.domru.ru',
    'X-Requested-With': 'XMLHttpRequest',
    'Accept-Language': 'en-US,en;q=0.9,ru;q=0.8',
    "Origin": 'https://vs.domru.ru',
    'User-Agent':
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.131 '
        'Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, br',
    "Cookie": '',
    "Accept": 'application/json'
}

def auth():
    try:
        response = requests.post(
          url="https://vs.domru.ru/login.html",
          headers=defaultHeaders,
          data={
            "User[Remember]": "0",
            "User[Password]": password,
            "User[Login]": login,
            },
        )

        getSession(response.headers)

    except requests.exceptions.RequestException:
        print('HTTP Request failed')


def getSession(headers):
    cookies = headers.get('Set-Cookie')

    if cookies:
        global session

        list = cookies.split(',')
        raw = list.pop()
        session = re.search('PHPSESSIDFPST=([^;]+); path=/', raw).group(1)


def getCameraUrl(camId):
    cameraHeaders["Cookie"] = 'PHPSESSIDFPST=%s' % session

    try:
        response = requests.post(
          url='https://vs.domru.ru/account/camera/%s/url.html' % camId,
          headers=cameraHeaders,
          params={
            "timeZoneOffset": "18000",
            "format": "hls"
          }
        )

        try:
            camData = response.json()
            url = camData['URL']
            url = url.replace('rtsp', 'hls') + '/playlist.m3u8'

            print(url)
            return url
        except ValueError:
            print('Decoding JSON has failed')
            return None
    except requests.exceptions.RequestException:
        print('HTTP Request failed')

@app.route('/api/v1/cams/<int:camId>')
def getCam(camId):
    global session

    if session == '':
        auth()
        print('AUTH: %s' % session)

    url = getCameraUrl(camId=camId)

    if url:
        return redirect(url)
    else:
        session = ''
        return 'Parse URL error!'

@app.route('/api/v1/cams/url/<int:camId>')
def getCamUrl(camId):
    global session

    if session == '':
        auth()
        print('AUTH: %s' % session)

    url = getCameraUrl(camId)

    if url:
        return url
    else:
        session = ''
        return 'Parse URL error!'

def main(argv):
    global login, password

    try:
        opts, args = getopt.getopt(argv, "l:p:", ["login=", "password="])
    except getopt.GetoptError:
        print('test.py -l <login> -p <password>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print('test.py -i <login> -p <password>')
            sys.exit()
        elif opt in ("-l", "--login"):
            login = arg
        elif opt in ("-p", "--password"):
            password = arg

if __name__ == '__main__':
    main(sys.argv[1:])

    if login and password:
        app.run(host='0.0.0.0', port=80)