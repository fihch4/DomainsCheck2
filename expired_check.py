#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
from config import *
# import datetime
import requests
from mysql_bot import MySQLi
from status_code import get_list_from_mysql
import telebot
from datetime import datetime
bot = telebot.TeleBot(token_tg_bot)


def days_expired(domain_name, dict_time):
    dict_result_expired = {}
    expired_date = dict_time.date()  # Дата освобождения
    datetime_now = datetime.now()
    difference = dict_time - datetime_now
    difference_days = difference.days  # сколько дней осталось до освобождени
    dict_result_expired['expired_date'] = expired_date
    dict_result_expired['difference_days'] = difference_days
    dict_result_expired['domain_name'] = domain_name
    return dict_result_expired


def request_api_xml(domain_name):
    try:
        url_api = 'https://www.whoisxmlapi.com/whoisserver/WhoisService?apiKey='
        final_url = url_api + apiKey + '&domainName=' + domain_name + '&outputFormat=JSON'
        dict_result = requests.get(final_url).json()
        date_expired = dict_result['WhoisRecord']['registryData']['expiresDate']
        time_for_bd = datetime.strptime(date_expired, "%Y-%m-%dT%H:%M:%SZ")
        dict_expired = days_expired(domain_name, time_for_bd)
        return dict_expired
    except KeyError:
        return "Error"


def get_difference_days_expired(date_expired):
    date_now = datetime.now()
    difference_date = date_expired - date_now.date()
    return difference_date.days


def main():
    db = MySQLi(host, user, password, database_home)
    domains = db.fetch("SELECT domain, id_domain FROM domains")
    if len(domains['rows']) >= 1:
        for i in domains['rows']:
            id_domain = i[1]
            domain_url = i[0]
            check_domain_in_db = db.fetch("SELECT date_time FROM expired_date_domains WHERE id_domain=%s", id_domain)

            if not check_domain_in_db['rows']:
                expired_domain = request_api_xml(domain_url)
                if expired_domain != "Error":
                    db.commit("INSERT INTO expired_date_domains (date_time, id_domain) VALUES (%s, %s)",
                              expired_domain['expired_date'], id_domain)
            else:
                date_in_bd = db.fetch("SELECT date_time FROM expired_date_domains WHERE id_domain =%s", id_domain)
                days_difference = get_difference_days_expired(date_in_bd['rows'][0][0])
                if days_difference <= days_expired_check:
                    expired_domain = request_api_xml(domain_url)
                    if expired_domain != "Error":

                        if date_in_bd != expired_domain['expired_date']:
                            db.commit("UPDATE expired_date_domains SET date_time = %s, "
                                      "WHERE id_domain =%s", expired_domain['expired_date'], id_domain)
                        """Уведомления"""
                        users_id_for_notification = db.fetch("SELECT users.telegram_id FROM domains, users WHERE "
                                                             "domains.id_domain = "
                                                             "users.domain_id AND domains.domain =%s", domain_url)
                        for user_telegram in get_list_from_mysql(users_id_for_notification):
                            db = MySQLi(host, user, password, database_home)
                            previous_date = db.fetch(
                                "SELECT datetime_notification FROM notifications_expired where id_domain=%s AND id_user=%s "
                                "ORDER BY datetime_notification DESC "
                                "LIMIT 1", id_domain, user_telegram)

                            format_time = '%Y-%m-%d %H:%M:%S'
                            datetime_notification_now = datetime.now().strftime(format_time)
                            datetime_notification_now = datetime.strptime(datetime_notification_now, format_time)

                            if int(len(previous_date['rows'])) >= 1:
                                date_old = datetime.strptime(str(previous_date['rows'][0][0]), format_time)
                                time_delta_seconds = (datetime_notification_now - date_old).total_seconds()
                                interval_notification_expired = 1440
                                if time_delta_seconds >= interval_notification_expired:
                                    message_telegram = f"❗ Обратите внимание!\n"\
                                                       f"Домен {domain_url} освобождается .\nОбщее "
                                    bot.send_message(user_telegram, message_telegram)
                                    db.commit(
                                        "INSERT INTO notifications_status_code (id_domain, datetime_notification, "
                                        "id_user, message_notification) VALUES (%s, %s, %s, %s)",
                                        id_domain, datetime_notification_now, user_telegram, message_telegram)



    # print(request_api_xml("https://helga.ru"))

    # for domain in domains_dict:
    #     print(domain)
    #     print(domains_dict[domain])

    # dictionary = (get_dictionary_domains_expired())
    # for domain in dictionary:
    #     domain_name = domain
    #     domain_date_expired = dictionary[domain]['date_expired']
    #     domain_id = dictionary[domain]['id']
    #     user_tg_id = dictionary[domain]['user_tg_id']
    #     days_expired = get_difference_days_expired(domain_date_expired)
    #     print(days_expired)
    #     update_difference_days(domain_id, days_expired)
    #     if days_expired <= days_expired_check:
    #         expired_actual_check = request_api_xml(domain_name)
    #         date_now = expired_actual_check['expired_date']
    #         if domain_date_expired.date() == date_now:
    #             print("Дата освобождения домена еще не обновлена. Запись в БД новой даты не требуется")
    #             bot.send_message(chat_id=user_tg_id, text=f"❗Внимание❗\n"
    #                                                             f"Домен: {domain_name} освобождается {date_now}\n"
    #                                                       f"Дней до освобождения домена: {days_expired}\n"
    #                                                       f"Срочно продлите домен.")
    #         else:
    #             print("Дата освобождения домена обновлена. Перезаписываем информацию в БД.")


if __name__ == '__main__':
    main()

#
