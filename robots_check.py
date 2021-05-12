#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import requests
# import datetime
import hashlib
import urllib3
from mysql_bot import MySQLi
from config import *
from status_code import check_domain, get_list_from_mysql
from multiprocessing import Pool
import telebot
from datetime import datetime

bot = telebot.TeleBot(token_tg_bot)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings()


def get_robots_url(domain_url):
    domain_url = domain_url.rstrip("/")
    robots_url = domain_url + '/robots.txt'
    return robots_url


def sitemaps_from_robotstxt(robots_txt):
    sitemaps = []
    for line in robots_txt.splitlines():
        line_split = [s.strip() for s in line.split(':', maxsplit=1)]
        if line_split[0].lower() == 'sitemap':
            sitemaps.append(line_split[1])
    return sitemaps


def check_robots_hash(domain_url):
    robots_url = get_robots_url(domain_url)
    db = MySQLi(host, user, password, database_home)
    id_domain = db.fetch("SELECT id_domain FROM domains WHERE domain=%s", domain_url)
    id_domain = id_domain['rows'][0][0]
    previous_robots_hash = db.fetch("SELECT robots_hash FROM robots_txt where id_domain=%s ORDER BY datetime DESC "
                                    "LIMIT 1", id_domain)
    format_time = '%Y-%m-%d %H:%M:%S'
    date_and_time = datetime.now().strftime(format_time)
    date_and_time = datetime.strptime(date_and_time, format_time)
    if not previous_robots_hash['rows']:
        """Первичная проверка. Если в БД отсутствует информация о предыдущем robots.txt hash"""
        robots_text = check_domain(robots_url, standard_headers_list, text='on')
        if robots_text['code'] == 200:
            hash_robots = hashlib.sha1(robots_text['text'].encode('utf-8')).hexdigest()
            db.commit("INSERT INTO robots_txt (datetime, id_domain, ua, robots_txt, robots_hash) VALUES (%s, %s, %s, "
                      "%s, %s)", date_and_time, id_domain, "Standard", robots_text['text'], hash_robots)
    else:
        robots_text = check_domain(robots_url, standard_headers_list, text='on')
        if robots_text['code'] == 200:
            hash_robots = hashlib.sha1(robots_text['text'].encode('utf-8')).hexdigest()
            previous_hash = previous_robots_hash['rows'][0][0]

            users_id_for_notification = db.fetch("SELECT users.telegram_id FROM domains, users WHERE "
                                                 "domains.id_domain = "
                                                 "users.domain_id AND domains.domain =%s", domain_url)

            if hash_robots != previous_hash:
                for user_telegram in get_list_from_mysql(users_id_for_notification):
                    previous_date = db.fetch(
                        "SELECT datetime_notification FROM notifications_robots_txt where id_domain=%s AND id_user=%s "
                        "ORDER BY datetime_notification DESC "
                        "LIMIT 1", id_domain, user_telegram)
                    if not previous_date['rows']:
                        message_telegram = f"Robots.txt для домена {domain_url} был изменен. Рекомендуем проверить " \
                                           f"корректность изменений. "
                        bot.send_message(user_telegram, message_telegram)
                        db.commit(
                            "INSERT INTO notifications_robots_txt (id_domain, id_user, datetime_notification, "
                            "message_notification) VALUES (%s, %s, %s, %s)", id_domain, user_telegram, date_and_time,
                            message_telegram)
                    else:
                        count_hash_robots = db.fetch("SELECT count(robots_hash) FROM robots_txt WHERE id_domain=%s "
                                                     "AND datetime > %s", id_domain, previous_date['rows'][0][0])
                        if count_hash_robots['rows'][0][0] >= 1:
                            interval_notification = db.fetch(
                                "SELECT interval_notifications FROM users_notification_settings "
                                "WHERE id_user =%s", user_telegram)
                            format_time = '%Y-%m-%d %H:%M:%S'
                            datetime_notification_now = datetime.now().strftime(format_time)
                            datetime_notification_now = datetime.strptime(datetime_notification_now, format_time)
                            if int(len(previous_date['rows'])) >= 1:
                                date_old = datetime.strptime(str(previous_date['rows'][0][0]), format_time)
                                time_delta_seconds = (datetime_notification_now - date_old).total_seconds()
                                if int(len(interval_notification['rows'])) >= 1:
                                    interval_notification = interval_notification['rows'][0][0]
                                else:
                                    interval_notification = 3600
                                if time_delta_seconds >= interval_notification:
                                    message_telegram = f"Robots.txt для домена {domain_url} был изменен.\nОбщее " \
                                                       f"количество изменений за {interval_notification} сек.: " \
                                                       f"{count_hash_robots['rows'][0][0]} раз(а).\nРекомендуем " \
                                                       f"проверить файл robots.txt"
                                    bot.send_message(user_telegram, message_telegram)
                                    db.commit(
                                        "INSERT INTO notifications_status_code (id_domain, datetime_notification, "
                                        "id_user, message_notification) VALUES (%s, %s, %s, %s)",
                                        id_domain, datetime_notification_now, user_telegram, message_telegram)
                db.commit(
                    "INSERT INTO robots_txt (datetime, id_domain, ua, robots_txt, robots_hash) VALUES (%s, %s, %s, "
                    "%s, %s)", date_and_time, id_domain, "Standard", robots_text['text'], hash_robots)

            else:  # ветка else для ситуаций, когда robots.txt не был изменен за период проверки
                for user_telegram in get_list_from_mysql(users_id_for_notification):
                    previous_date = db.fetch(
                        "SELECT datetime_notification FROM notifications_robots_txt where id_domain=%s AND id_user=%s "
                        "ORDER BY datetime_notification DESC "
                        "LIMIT 1", id_domain, user_telegram)
                    if len(previous_date['rows']) >= 1:
                        count_hash_robots = db.fetch("SELECT count(robots_hash) FROM robots_txt WHERE id_domain=%s "
                                                     "AND datetime > %s", id_domain, previous_date['rows'][0][0])
                        if count_hash_robots['rows'][0][0] >= 1:
                            interval_notification = db.fetch(
                                "SELECT interval_notifications FROM users_notification_settings "
                                "WHERE id_user =%s", user_telegram)
                            format_time = '%Y-%m-%d %H:%M:%S'
                            datetime_notification_now = datetime.now().strftime(format_time)
                            datetime_notification_now = datetime.strptime(datetime_notification_now, format_time)
                            if int(len(previous_date['rows'])) >= 1:
                                date_old = datetime.strptime(str(previous_date['rows'][0][0]), format_time)
                                time_delta_seconds = (datetime_notification_now - date_old).total_seconds()
                                if int(len(interval_notification['rows'])) >= 1:
                                    interval_notification = interval_notification['rows'][0][0]
                                else:
                                    interval_notification = 3600
                                if time_delta_seconds >= interval_notification:
                                    message_telegram = f"Robots.txt для домена {domain_url} был изменен.\nОбщее " \
                                                       f"количество изменений за {interval_notification} сек.: " \
                                                       f"{count_hash_robots['rows'][0][0]} раз(а).\nРекомендуем " \
                                                       f"проверить файл robots.txt"
                                    bot.send_message(user_telegram, message_telegram)
                                    db.commit(
                                        "INSERT INTO notifications_status_code (id_domain, datetime_notification, "
                                        "id_user, message_notification) VALUES (%s, %s, %s, %s)",
                                        id_domain, datetime_notification_now, user_telegram, message_telegram)


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
        p.map(check_robots_hash, domains_list)


if __name__ == '__main__':
    main()
