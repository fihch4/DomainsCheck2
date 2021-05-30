import requests
from urllib3.exceptions import InsecureRequestWarning
from config import *
import random
import time
from urllib.parse import urlparse
from mysql_bot import MySQLi
from multiprocessing import Pool
import telebot
import datetime
import warnings

warnings.filterwarnings('ignore', message='Unverified HTTPS request')
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
bot = telebot.TeleBot(token_tg_bot)


def get_proxies(list_proxy):
    proxy = random.choice(list_proxy) + ':' + proxy_port
    proxy_dict = {
        'http': proxy,
        'https': proxy
    }
    return proxy_dict


def get_ua(headers_list):
    header = random.choice(headers_list)
    ua = {
        'User-Agent': header
    }
    return ua


def request_reference(sites):
    try:
        for site in sites:
            proxy = get_proxies(proxy_list)
            ua = get_ua(standard_headers_list)
            r = requests.get(site, proxies=proxy, verify=False, timeout=timeout_config, headers=ua)
            if r.status_code == 200:
                return proxy
    except requests.exceptions.ProxyError:
        return "Connection Error"
    except requests.exceptions.Timeout:
        return "Timeout Error"
    except requests.exceptions.ConnectionError:
        return "Connection Error"


def selection():
    flag = True
    num = 0
    while flag:
        check_request = request_reference(reference_sites)
        if check_request != 'Connection Error':
            return check_request
        num += 1
        if num >= attempt:
            print("Ошибка отбора прокси сервера для работы")
            break


def status_code(domain_url, headers_type, text='off'):
    try:
        if text == 'off':
            r = requests.get(domain_url,
                             proxies=selection(),
                             verify=False,
                             headers=get_ua(headers_type),
                             allow_redirects=False,
                             timeout=timeout_config
                             )
            return r.status_code
        else:
            r = requests.get(domain_url,
                             proxies=selection(),
                             verify=False,
                             headers=get_ua(headers_type),
                             allow_redirects=False,
                             timeout=timeout_config
                             )
            return r
    except requests.exceptions.Timeout:
        return "Timeout Error"
    except requests.exceptions.ProxyError:
        return "504"
    except requests.exceptions.ConnectionError:
        return "504"



def status_code_sitemap(domain_url, headers_type, text='off'):
    try:
        if text == 'off':
            r = requests.get(domain_url,
                             proxies=selection(),
                             verify=False,
                             headers=get_ua(headers_type),
                             timeout=timeout_config
                             )
            return r.status_code
        else:
            r = requests.get(domain_url,
                             proxies=selection(),
                             verify=False,
                             headers=get_ua(headers_type),
                             timeout=timeout_config
                             )
            return r
    except requests.exceptions.Timeout:
        return "Timeout Error"
    except requests.exceptions.ProxyError:
        return "504"


def text_source(url, headers_type):
    r = requests.get(url,
                     proxies=selection(),
                     verify=False,
                     headers=get_ua(headers_type),
                     allow_redirects=False
                     )

    return r.text


def check_domain(domain_url, headers_type, text='off'):
    flag = True
    col = 0
    if text == 'off':
        while flag:
            request_code = status_code(domain_url, headers_type)  # Задаем тип header (для обычных и ботов ПС)
            if request_code == 200:
                return request_code
            if col > col_max:
                error_request = {'code': request_code,
                                 'domain': domain_url,
                                 }
                return error_request
            col += 1
            time.sleep(pause_domain_check)
    if text == 'on':
        while flag:
            request_code = status_code(domain_url, headers_type, text='on')  # Задаем тип header (для обычных и ботов ПС)
            if request_code != 'Timeout Error' and request_code != '504':
                if request_code.status_code == 200:
                    error_request = {'code': request_code.status_code,
                                     'domain': domain_url,
                                     'text': request_code.text
                                     }
                    return error_request
                elif request_code.status_code == 301:
                    if col > col_max:
                        error_request = {'code': "301 Redirects",
                                         'domain': domain_url,
                                         'text': "301 Redirects"
                                         }
                        return error_request
                    col += 1
                    time.sleep(pause_domain_check)
                elif request_code.status_code == 404:
                    if col > col_max:
                        error_request = {'code': "404",
                                         'domain': domain_url,
                                         'text': "404 Not Found"
                                         }
                        return error_request
                    col += 1
                    time.sleep(pause_domain_check)
                elif request_code.status_code != 200:
                    if col > col_max:
                        error_request = {'code': "Is not 200 OK code",
                                         'domain': domain_url,
                                         'text': request_code.status_code
                                         }
                        return error_request
                    col += 1
                    time.sleep(pause_domain_check)
            else:
                if col > col_max:
                    error_request = {'code': "Timeout or 504",
                                     'domain': domain_url,
                                     'text': "Timeout or 504"
                                     }
                    return error_request
                col += 1
                time.sleep(pause_domain_check)



def check_domain_sitemap(domain_url, headers_type, text='off'):
    # try:
    flag = True
    col = 0
    if text == 'off':
        while flag:
            request_code = status_code_sitemap(domain_url, headers_type)  # Задаем тип header (для обычных и ботов ПС)
            if request_code == 200:
                return request_code
            if col > col_max:
                error_request = {'code': request_code,
                                 'domain': domain_url,
                                 }
                return error_request
            col += 1
            time.sleep(pause_domain_check)
    if text == 'on':
        while flag:
            request_code = status_code_sitemap(domain_url, headers_type, text='on')  # Задаем тип header (для обычных и ботов ПС)
            if request_code != 'Timeout Error' and request_code != '504':
                if request_code.status_code == 200:
                    error_request = {'code': request_code.status_code,
                                     'domain': domain_url,
                                     'text': request_code.text
                                     }
                    return error_request
                elif request_code.status_code == 301:
                    if col > col_max:
                        error_request = {'code': "301 Redirects",
                                         'domain': domain_url,
                                         'text': "301 Redirects"
                                         }
                        return error_request
                    col += 1
                    time.sleep(pause_domain_check)
            else:
                if col > col_max:
                    error_request = {'code': "Timeout or 504",
                                     'domain': domain_url,
                                     'text': "Timeout or 504"
                                     }
                    return error_request
                col += 1
                time.sleep(pause_domain_check)




def get_list_from_mysql(mysql_result):
    list_result = []
    if len(mysql_result['rows']) >= 1:
        for i in mysql_result['rows']:
            list_result.append(i[0])
    return list_result


def parse_domain_url(url):
    domain = urlparse(url).netloc
    return domain


def status_code_domains(domain_url):
    date_and_time = datetime.datetime.now()
    db = MySQLi(host, user, password, database_home)
    id_domain = db.fetch("SELECT id_domain FROm domains WHERE domain=%s", domain_url)
    id_domain = id_domain['rows'][0][0]
    status_code_standard = check_domain(domain_url, standard_headers_list)
    status_code_yandex_bot_pc = check_domain(domain_url, yandex_header_pc)
    status_code_yandex_bot_mobile = check_domain(domain_url, yandex_header_mobile)
    status_code_google_bot_mobile = check_domain(domain_url, google_bot_mobile)
    print(domain_url)
    if status_code_standard == 200:
        db.commit("INSERT INTO statistic_domains_check (datetime, id_domain, ua, response_code, result_check) VALUES "
                  "(%s, %s, %s, %s,%s)", date_and_time, id_domain, 'Standard', '200', 'Success_C')
    else:
        db.commit("INSERT INTO statistic_domains_check (datetime, id_domain, ua, response_code, result_check) VALUES "
                  "(%s, %s, %s, %s,%s)", date_and_time, id_domain, 'Standard', status_code_standard['code'], 'Error_C')
    if status_code_yandex_bot_pc == 200:
        db.commit("INSERT INTO statistic_domains_check (datetime, id_domain, ua, response_code, result_check) VALUES "
                  "(%s, %s, %s, %s,%s)", date_and_time, id_domain, 'Yandex_PC', '200', 'Success_C')
    else:
        db.commit("INSERT INTO statistic_domains_check (datetime, id_domain, ua, response_code, result_check) VALUES "
                  "(%s, %s, %s, %s,%s)", date_and_time, id_domain, 'Yandex_PC', status_code_yandex_bot_pc['code'],
                  'Error_C')
    if status_code_yandex_bot_mobile == 200:
        db.commit("INSERT INTO statistic_domains_check (datetime, id_domain, ua, response_code, result_check) VALUES "
                  "(%s, %s, %s, %s,%s)", date_and_time, id_domain, 'Yandex_MOB', '200', 'Success_C')
    else:
        db.commit("INSERT INTO statistic_domains_check (datetime, id_domain, ua, response_code, result_check) VALUES "
                  "(%s, %s, %s, %s,%s)", date_and_time, id_domain, 'Yandex_MOB', status_code_yandex_bot_mobile['code'],
                  'Error_C')
    if status_code_google_bot_mobile == 200:
        db.commit("INSERT INTO statistic_domains_check (datetime, id_domain, ua, response_code, result_check) VALUES "
                  "(%s, %s, %s, %s,%s)", date_and_time, id_domain, 'Google', '200', 'Success_C')
    else:
        db.commit("INSERT INTO statistic_domains_check (datetime, id_domain, ua, response_code, result_check) VALUES "
                  "(%s, %s, %s, %s,%s)", date_and_time, id_domain, 'Google', status_code_google_bot_mobile['code'],
                  'Error_C')
    print(status_code_standard)
    print(status_code_google_bot_mobile)
    print(status_code_yandex_bot_pc)
    print(status_code_yandex_bot_mobile)

def main():
    db = MySQLi(host, user, password, database_home)
    domains = db.fetch("SELECT domain FROM domains")
    domains_list = []
    if len(domains['rows']) >= 1:
        for i in domains['rows']:
            domains_list.append(i[0])
        threads = len(domains_list) // 2
        if threads >= 15:
            threads = 10
        elif threads <= 0:
            threads = 1
        with Pool(threads) as p:
            p.map(status_code_domains, domains_list)


if __name__ == '__main__':
    main()
