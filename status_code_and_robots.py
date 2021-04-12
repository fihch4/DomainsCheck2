import requests
from urllib3.exceptions import InsecureRequestWarning

from config import *
import random

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


# r = requests.get('https://protect-sc.ru', verify=False)
# print(r.text)

class Proxy:
    def get_proxies(self, list_proxy):
        proxy = random.choice(list_proxy) + ':' + proxy_port
        # print(proxy)
        proxy_dict = {
            'http': proxy,
            'https': proxy
        }
        return proxy_dict

    def get_ua(self, headers_list):
        header = random.choice(headers_list)
        ua = {
            'User-Agent': header
        }
        return ua

    def request_reference(self, sites):
        try:
            for site in sites:
                proxy = self.get_proxies(proxy_list)
                ua = self.get_ua(standard_headers_list)
                r = requests.get(site, proxies=proxy, verify=False, timeout=5, headers=ua)
                if r.status_code == 200:
                    return proxy
        except requests.exceptions.ProxyError:
            return f"Connection Error"

    def selection(self):
        flag = True
        num = 0
        while flag:
            check_request = self.request_reference(reference_sites)
            if check_request != 'Connection Error':
                return check_request
            num += 1
            if num >= attempt:
                print("Ошибка отбора прокси сервера для работы")
                break


proxies = Proxy()

r = requests.get('https://whoer.net/ru',
                 proxies=proxies.selection(),
                 verify=False,
                 headers=proxies.get_ua(standard_headers_list)
                 )
print(r.text)
# print(r.text)
