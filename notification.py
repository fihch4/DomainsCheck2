from mysql_bot import MySQLi
from config import *
from status_code import get_list_from_mysql
import telebot

from datetime import datetime
bot = telebot.TeleBot(token_tg_bot)

def main():
    db = MySQLi(host, user, password, database_home)
    domains = db.fetch("SELECT domain, id_domain FROM domains")
    if len(domains['rows']) >= 1:
        for i in domains['rows']:
            id_domain = i[1]
            domain_url = i[0]
            users_id_for_notification = db.fetch("SELECT users.telegram_id FROM domains, users WHERE "
                                                 "domains.id_domain = "
                                                 "users.domain_id AND domains.domain =%s", domain_url)
            for user_telegram in get_list_from_mysql(users_id_for_notification):
                interval_notification = db.fetch("SELECT interval_notifications FROM users_notification_settings "
                                                 "WHERE id_user =%s", user_telegram)

                previous_date_notification_satus_code = db.fetch("SELECT datetime_notification FROM "
                                                                 "notifications_status_code WHERE id_user=%s AND "
                                                                 "id_domain=%s order by (datetime_notification) desc "
                                                                 "id_domain=%s order by (datetime_notification) desc "
                                                                 "LIMIT 1", user_telegram, id_domain)

                now_status_code_domain_check = db.fetch("SELECT ua, result_check, response_code, datetime FROM "
                                                        "statistic_domains_check WHERE id_domain = %s order by ("
                                                        "datetime) desc limit 4", id_domain)
                status_notification = ''
                if now_status_code_domain_check['rows']:
                    errors_count = 0
                    for element_dict in now_status_code_domain_check['rows']:
                        if element_dict[1] == 'Error_C':
                            if element_dict[2] != '200':
                                errors_count += 1
                                status_notification += 'UA: ' + element_dict[0] + ' | Response Code: ' + element_dict[2] + ' | Date check: ' + str(element_dict[3]) + '\n'
                    if len(status_notification) >= 1:
                        status_notification += 'Domain: ' + domain_url + '\n'
                        status_notification += '❌Ошибка: домен недоступен после 5 повторных проверок.' + '\n'
                        format_time = '%Y-%m-%d %H:%M:%S'
                        datetime_notification_now = datetime.now().strftime(format_time)
                        datetime_notification_now = datetime.strptime(datetime_notification_now, format_time)
                        if int(len(previous_date_notification_satus_code['rows'])) >= 1:
                            date_old = datetime.strptime(str(previous_date_notification_satus_code['rows'][0][0]), format_time)
                            time_delta_seconds = (datetime_notification_now - date_old).total_seconds()
                            if int(len(interval_notification['rows'])) >= 1:
                                interval_notification = interval_notification['rows'][0][0]
                            else:
                                interval_notification = 3600
                            if time_delta_seconds >= interval_notification:
                                if errors_count >= 3:
                                    bot.send_message(user_telegram, status_notification)
                                    db.commit(
                                        "INSERT INTO notifications_status_code (id_domain, datetime_notification, "
                                        "id_user, message_notification) VALUES (%s, %s, %s, %s)",
                                        id_domain, datetime_notification_now, user_telegram, status_notification)
                        else:
                            if errors_count >= 3:
                                bot.send_message(user_telegram, status_notification)
                                db.commit(
                                    "INSERT INTO notifications_status_code (id_domain, datetime_notification, id_user, "
                                    "message_notification) VALUES (%s, %s, %s, %s)", id_domain,
                                    datetime_notification_now, user_telegram, status_notification)

if __name__ == '__main__':
    main()
