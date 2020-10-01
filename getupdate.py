#!/usr/bin/env python

import sys
import os
import requests
from bs4 import BeautifulSoup
import re
import datetime
import time
import toml
import argparse
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def get_config(args):
    conf = {}
    config_file = ""

    config_file = args.config
    if not isinstance(config_file, str):
        config_file = str('./getupdate.toml')

    with open(config_file, 'r', encoding='utf-8') as f:
        conf.update(toml.load(f))
    return conf


def make_url(conf):
    base = 'https://www.google.co.jp/search?'
    lang = 'hl=' + conf['SEARCH']['lang']
    num = 'num=' + str(conf['SEARCH']['numbers'])
    keywords = conf['SEARCH']['keywords']
    e_keywords = conf['SEARCH']['exclude_keywords']
    # Google API values
    query = 'as_q='
    e_query = 'as_eq='
    as_qdr = 'as_qdr=d' # day
    as_occt = 'as_occt=body'

    if keywords:
        for i in range(len(keywords)):
            if keywords[i] == '':
                pass
            elif i == 0:
                query += keywords[i]
            else:
                query += '+' + keywords[i]
    if e_keywords:
        for q in range(len(e_keywords)):
            if e_keywords[q] == '':
                pass
            elif q == 0:
                e_query += e_keywords[q]
            else:
                e_query += '+' + e_keywords[q]
    url = base + lang + '&' + num + '&' + as_qdr + '&' + as_occt + '&' + query + '&' + e_query
    # url = 'https://www.google.co.jp/search?hl=ja&tbs=qdr%3Ad&num=' + str(num_search) + '&q=' + '+'.join(keywords)
    return url


def make_files(conf):
    nowday = datetime.datetime.now()
    work_path = conf['PATH']['work_path']
    isHierarchy = conf['PATH']['hierarchy']
    dir_name = conf['PATH']['dir_name']
    file_name = nowday.strftime('%Y-%m-%d-%H') + ".html"
    if isHierarchy:
        file_path = work_path + "/" + nowday.strftime('%Y') + "/" + nowday.strftime('%m') + "/" + dir_name + "/"
    else:
        file_path = work_path + dir_name + "/"
    os.makedirs(file_path, exist_ok=True)
    return (file_path + file_name)


def print_header(f, work_path):
    string = """
<html lang="ja">
  <head>
    <meta charset="UTF-8">
"""
    #string += '<link rel="stylesheet" type="text/css" href="../../../getupdate.css">\n'.format(work_path)
    string += '<link rel="stylesheet" type="text/css" href="../../../getupdate.css">\n'
    string += """
  </head>
  <body>
  <div class="index">
    <p>
      <a href="./"> current Dir. </a>
       ...
      <a href="../"> parent Dir. </a>
       ... 
      <a href="../../../"> Top Dir. </a>
    </p>
  </div>
"""
    #print(string)
    f.write(string)


def print_footer(f):
    string = """
  <div class="index">
    <p>
      <a href="./"> current Dir. </a>
       ...
      <a href="../"> parent Dir. </a>
       ... 
      <a href="../../../"> Top Dir. </a>
    </p>
  </div>
  </body>
</html>
"""
    f.write(string)


def print_html(f, soup, work_path):
    print_header(f, work_path)
    for i in soup:
        try:
            title = str(i.find('h3').text)
            url = str(i.a.get('href'))
            desc = str(i.find('span', attrs={'class': 'aCOpRe'}).text)
#            desc = str(i.find('span', attrs={'class': 'st'}).text)
            f.write('<div class="article"><p><h3>{}</h3><a href="{}">{}</a></p>\n'.format(title, url, url))
            f.write('<p>{}</p></div>\n<hr>\n'.format(desc))
        except:
            pass
    print_footer(f)


def send_mail(conf, file_path):
    if (conf['MAIL']['send_mail']):
        with open(file_path, mode='r') as f:
            body = f.read()

        me = conf['MAIL']['from']
        you = conf['MAIL']['to']

        msg = MIMEMultipart('alternative')
        msg['Subject'] = conf['MAIL']['subject'] + str(datetime.datetime.now())
        msg['From'] = me
        msg['To'] = you
        part = MIMEText(body, 'html')
        msg.attach(part)
        s = smtplib.SMTP('localhost')
        s.sendmail(me, you, msg.as_string())
        s.quit()


def request_query(conf):
#    UA = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/603.3.8 (KHTML, like Gecko) Version/10.1.2 Safari/603.3.8'}
#    UA = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36'}
    UA = {'User-Agent' : conf['SEARCH']['ua']}
    file_path = make_files(conf)
    with open(file_path, mode='w') as f:
        url = make_url(conf)
        if url:
            retry = 5
            c = 0
            while (retry > c):
                res = requests.get(url, headers=UA)
                if res.status_code != 200:
                    c += 1
                    time.sleep(10)
                    continue
                else:
                    break
            soup = BeautifulSoup(res.text, 'html.parser')
            soup = soup.find_all('div', attrs={'class': 'g'})
            print_html(f, soup, str(conf['PATH']['work_path']))
    send_mail(conf, file_path)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", help="spefify config file.")
    args = parser.parse_args()
    return(args)


def main():
    args = get_args()
    conf = get_config(args)
    request_query(conf)

if __name__ == "__main__":
    main()
