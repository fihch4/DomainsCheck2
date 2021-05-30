#!/usr/bin/python3.8
# -*- coding: utf-8 -*-
import logging
from datetime import time
import subprocess
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from telebot import types
from status_code import *

list_domains = ""

bot = telebot.TeleBot(token_tg_bot)


@bot.message_handler(commands=['start'])
def get_text_messages(message):
    print(message.from_user.id)
    print(message.text)
    db = MySQLi(host, user, password, database_home)
    domain_list = db.fetch("SELECT domains.domain, users.id_user "
                           "FROM domains, users WHERE domains.id_domain = users.domain_id "
                           "AND users.telegram_id = %s ", message.from_user.id)
    start_menu = types.ReplyKeyboardMarkup(True, True)
    start_menu.row('✅️Добавить сайт', '❌ Удалить сайт')
    if len(domain_list['rows']) >= 1:
        start_menu.row('ℹ Информация о домене')
    # start_menu.row('📈️ Перезаписать HASH robots', '👀 Мой профиль')
    # start_menu.row('📈 Получить логи проверок')
    bot.send_message(message.chat.id, 'Стартовое меню', reply_markup=start_menu)


@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    if message.text == '✅️Добавить сайт':
        back_button = types.ReplyKeyboardMarkup(True, True)
        back_button.row('Назад')
        print(message.chat.id)
        print(message.text)
        bot.send_message(message.chat.id,
                         f"📨 Пришлите мне адрес домена, который требуется отслеживать. Примеры:\n"
                         f"https://site.ru\n"
                         f"http://site.ru\n"
                         f"https://www.site.ru",
                         reply_markup=back_button, parse_mode="HTML")
        bot.register_next_step_handler(message, add_site_bd)

    elif message.text == '❌ Удалить сайт':
        back_button = types.ReplyKeyboardMarkup(True, True)
        back_button.row('Назад')
        db = MySQLi(host, user, password, database_home)
        domain_list = db.fetch("SELECT domains.domain, users.id_user "
                               "FROM domains, users WHERE domains.id_domain = users.domain_id "
                               "AND users.telegram_id = %s ", user_id)
        print(domain_list)
        print(len(domain_list))
        if len(domain_list['rows']) >= 1:
            list_domain = []
            for i in domain_list['rows']:
                domain = i[0]
                id_for_list = i[1]
                list_domain.append(f"{domain}: ID - {id_for_list}")
            domains_str = ''
            for i in list_domain:
                domains_str += i + '\n'
            bot.send_message(message.chat.id, text=
            f"Для <b>удаления</b> сайта требуется указать его <b>ID</b> из указанного ниже списка.\n"
            f"👇Ваш список отслеживаемых доменов:👇\n"
            f"{domains_str}\n"
            f"<b>УКАЖИТЕ ID</b> выбранного домена для удаления", parse_mode="HTML",
                             reply_markup=back_button)
            bot.register_next_step_handler(message, delete_site_bd)
        else:
            bot.send_message(message.chat.id, f"Ваш список отслеживаемых доменов пуст 😟\n"
                                              f"Для продолжения напишите /start и добавьте новый домен.")

    elif message.text == 'ℹ Информация о домене':
        back_button = types.ReplyKeyboardMarkup(True, True)
        back_button.row('Назад')
        print(message.chat.id)
        print(message.text)
        db = MySQLi(host, user, password, database_home)
        domain_list = db.fetch("SELECT domains.domain, users.id_user "
                               "FROM domains, users WHERE domains.id_domain = users.domain_id "
                               "AND users.telegram_id = %s ", user_id)

        if len(domain_list['rows']) >= 1:
            list_domain = []
            for i in domain_list['rows']:
                domain = i[0]
                id_for_list = i[1]
                list_domain.append(f"{domain}: ID - {id_for_list}")
            domains_str = ''
            for i in list_domain:
                domains_str += i + '\n'
            bot.send_message(message.chat.id, f"Ваш список отслеживаемых доменов:\n{domains_str}"
                                              f"\nУкажите ID домена для получения подробной информации.",
                             reply_markup=back_button)
            bot.register_next_step_handler(message, information_domain)
        else:
            bot.send_message(message.chat.id, f"Ваш список отслеживаемых доменов пуст 😟\n"
                                              f"Для продолжения напишите /start и добавьте новый домен.")


    elif message.text == 'Назад':
        print(message.text)
        get_text_messages(message)


def information_domain(message):
    try:
        if message.text == 'Назад':
            get_text_messages(message)
        else:
            domain_id = message.text
            user_id = message.from_user.id
            db = MySQLi(host, user, password, database_home)
            check_domain_information = db.fetch("SELECT domain_id FROM users WHERE telegram_id = %s AND id_user = %s",
                                                user_id,
                                                domain_id)
            if len(check_domain_information['rows']) >= 1:
                print(f"Пользователь {user_id} отправил заявку на получение информации о домене {domain_id} из БД")

                db_domain_url = db.fetch("SELECT domains.domain FROM domains INNER JOIN users ON users.domain_id = "
                                         "domains.id_domain WHERE users.id_user = %s AND users.telegram_id = %s",
                                         domain_id, user_id)
                domain_url = db_domain_url['rows'][0][0]
                db_date_expired_domain = db.fetch("select expired_date_domains.date_time FROM domains INNER JOIN "
                                                  "expired_date_domains ON domains.id_domain = "
                                                  "expired_date_domains.id_domain INNER JOIN users ON "
                                                  "domains.id_domain = users.domain_id WHERE users.telegram_id = "
                                                  "%s AND users.id_user = %s", user_id, domain_id)
                date_expired = db_date_expired_domain['rows'][0][0]
                db_ua_standard = db.fetch("SELECT statistic_domains_check.response_code FROM statistic_domains_check "
                                          "INNER JOIN domains ON domains.id_domain = "
                                          "statistic_domains_check.id_domain INNER JOIN users ON domains.id_domain = "
                                          "users.domain_id WHERE users.telegram_id = %s AND users.id_user = "
                                          "%s AND UA = 'Standard' ORDER BY (datetime) desc LIMIT 1", user_id, domain_id)
                code_ua_standard = db_ua_standard['rows'][0][0]
                db_ua_yandex_mob = db.fetch("SELECT statistic_domains_check.response_code FROM statistic_domains_check "
                                            "INNER JOIN domains ON domains.id_domain = "
                                            "statistic_domains_check.id_domain INNER JOIN users ON domains.id_domain = "
                                            "users.domain_id WHERE users.telegram_id = %s AND users.id_user = "
                                            "%s AND UA = 'Yandex_MOB' ORDER BY (datetime) desc LIMIT 1", user_id,
                                            domain_id)
                code_ua_yandex_mob = db_ua_yandex_mob['rows'][0][0]
                db_ua_yandex_pc = db.fetch("SELECT statistic_domains_check.response_code FROM statistic_domains_check "
                                           "INNER JOIN domains ON domains.id_domain = "
                                           "statistic_domains_check.id_domain INNER JOIN users ON domains.id_domain = "
                                           "users.domain_id WHERE users.telegram_id = %s AND users.id_user = "
                                           "%s AND UA = 'Yandex_PC' ORDER BY (datetime) desc LIMIT 1", user_id,
                                           domain_id)
                code_ua_yandex_pc = db_ua_yandex_pc['rows'][0][0]
                db_ua_ggl = db.fetch("SELECT statistic_domains_check.response_code FROM statistic_domains_check "
                                     "INNER JOIN domains ON domains.id_domain = "
                                     "statistic_domains_check.id_domain INNER JOIN users ON domains.id_domain = "
                                     "users.domain_id WHERE users.telegram_id = %s AND users.id_user = "
                                     "%s AND UA = 'Google' ORDER BY (datetime) desc LIMIT 1", user_id,
                                     domain_id)
                code_ua_ggl = db_ua_ggl['rows'][0][0]
                db_ua_date = db.fetch("SELECT statistic_domains_check.datetime FROM statistic_domains_check "
                                      "INNER JOIN domains ON domains.id_domain = "
                                      "statistic_domains_check.id_domain INNER JOIN users ON domains.id_domain = "
                                      "users.domain_id WHERE users.telegram_id = %s AND users.id_user = "
                                      "%s AND UA = 'Google' ORDER BY (datetime) desc LIMIT 1", user_id,
                                      domain_id)
                code_date = db_ua_date['rows'][0][0]
                db_date_check_robots = db.fetch("SELECT robots_txt.datetime FROM robots_txt INNER JOIN domains ON "
                                                "domains.id_domain = robots_txt.id_domain INNER JOIN users ON "
                                                "domains.id_domain = users.domain_id WHERE users.telegram_id = %s AND "
                                                "users.id_user = "
                                                "%s ORDER BY (datetime) desc LIMIT 1", user_id, domain_id)
                date_check_robots = db_date_check_robots['rows'][0][0]
                # db_count_domains_users = db.fetch("SELECT count(domain_id) from USERS where id_user = %s", domain_id)
                db_count_domains_users = db.fetch("SELECT count(domain_id) FROM users where domain_id = (SELECT domain_id FROM users WHERE id_user = %s)", domain_id)
                count_domains_users = db_count_domains_users['rows'][0][0]
                string_message = f"🌐Домен: {domain_url}\n" \
                                 f"✨Status Code UA Standard: {code_ua_standard}\n" \
                                 f"✨Status Code UA Yandex Mobile: {code_ua_yandex_mob}\n" \
                                 f"✨Status Code UA Google Mobile: {code_ua_ggl}\n" \
                                 f"✨Status Code UA Yandex PC: {code_ua_yandex_pc}\n" \
                                 f"📅Дата освобождения: {date_expired}\n" \
                                 f"📅Дата проверки кода ответа сервера: {code_date}\n" \
                                 f"📅Дата проверки robots_txt: {date_check_robots}\n" \
                                 f"👥Кол-во пользователей следит за доменом, шт.: {count_domains_users}\n"
                bot.send_message(message.from_user.id, string_message)

            else:
                bot.send_message(message.from_user.id, f"Указан некорректный id. Напишите /start и повторите команду.")
    except IndexError:
        bot.send_message(message.from_user.id, f"⚠Отсутствует информация о домене.\nТребуется 24 часа для сбора "
                                               f"дополнительной информации.\n"
                                               f"✨Status Code UA Standard: unknown\n" \
                                               f"✨Status Code UA Yandex Mobile: unknown\n" \
                                               f"✨Status Code UA Google Mobile: unknown\n" \
                                               f"✨Status Code UA Yandex PC: unknown\n" \
                                               f"📅Дата освобождения: unknown\n" \
                                               f"📅Дата проверки кода ответа сервера: unknown\n" \
                                               f"📅Дата проверки robots_txt: unknown\n" \
                                               f"📅Дата последнего изменения robots_txt: unknown\n" \
                                               f"👥Кол-во пользователей следит за доменом, шт.: unknown\n")
    except ValueError:
        bot.send_message(message.from_user.id, f"Указан некорректный id. Напишите /start и повторите команду.")


def add_seconds_timedelta(message):
    if message.text == 'Назад':
        get_text_messages(message)
    else:
        try:
            user_id = message.from_user.id
            select_interval_notification(user_id)
            seconds = int(message.text)
            update_interval_notification(user_id, seconds)
            print(seconds)
            bot.send_message(message.chat.id, f"✅ Интервал уведомлений успешно изменен.\n"
                                              f"Для продолжения нажмите 'Назад' или /start")
        except ValueError:
            bot.send_message(message.chat.id, f"Вы указали некорректное число. "
                                              f"Для продолжения нажмите 'Назад' или /start")


def add_site_bd(message):
    try:
        if message.text == 'Назад':
            get_text_messages(message)
        else:
            user_id = message.from_user.id
            domain_name_telegram = message.text
            domain_name_telegram = str(domain_name_telegram).lower()
            print(f"USER ID: {user_id} пытается добавить домен {domain_name_telegram}")
            print(parse_domain_url(domain_name_telegram))
            if not parse_domain_url(domain_name_telegram):
                """
                Пользователь прислал домен без протокола.
                """
                bot.send_message(message.from_user.id,
                                 f"❌ Ошибка добавления домена.\n"
                                 f"Причина: отсутствует протокол http/https\n"
                                 f"Для продолжения напишите /start или нажмите на кнопку 'Назад'")
            else:
                print(type(parse_domain_url(domain_name_telegram)))
                db = MySQLi(host, user, password, database_home)
                check_id_domain = db.fetch("SELECT id_domain FROM domains WHERE domain LIKE CONCAT('%', %s, '%')",
                                           parse_domain_url(domain_name_telegram))
                print(check_id_domain)
                if not check_id_domain['rows']:  # если в БД нет домена
                    print("Домена нет в БД")
                    bot.send_message(message.from_user.id,
                                     f"🕒 Пожалуйста, ожидайте.\n👮 Проводим первичную проверку домена.")

                    status = check_domain(domain_name_telegram, standard_headers_list)

                    if status != 200:
                        """
                        Код ответа сервера для домена не равен 200 ОК. Отправляем юзеру уведомление.
                        """
                        bot.send_message(message.from_user.id,
                                         f"❌ Ошибка добавления домена: {domain_name_telegram}\n"
                                         f"Причина: код ответа сервера {status['code']}\n"
                                         f"💡 Добавляемый домен должен быть доступен для проверки "
                                         f"и иметь код ответа сервера 200 ОК.\n"
                                         f"Для продолжения напишите /start или нажмите на кнопку 'Назад'")
                    else:
                        """
                        Код ответа сервера = 200 ОК. Добавляем домен в БД и связываем с пользователем.
                        """
                        db.commit("INSERT INTO domains (domain) VALUES (%s)", domain_name_telegram)
                        check_id_domain = db.fetch(
                            "SELECT id_domain FROM domains WHERE domain LIKE CONCAT('%', %s, '%')",
                            parse_domain_url(domain_name_telegram))
                        print(check_id_domain)
                        id_domain = (check_id_domain['rows'][0][0])
                        print(id_domain)
                        db.commit("INSERT INTO users (name, domain_id, telegram_id) VALUES (%s, %s, %s)",
                                  message.from_user.username, id_domain, user_id)
                        bot.send_message(message.from_user.id,
                                         f"🌐 Домен: {domain_name_telegram}\n"
                                         f"✅ Успешно добавлен в базу данных\n"
                                         f"Для продолжения напишите /start или нажмите на кнопку 'Назад'")
                else:
                    print("Проверка привязки домена к пользователю")
                    """
                    Проверяем привязку домена к пользователям в БД.
                    """
                    telegram_users_id = db.fetch("SELECT telegram_id FROM users WHERE domain_id = %s",
                                                 check_id_domain['rows'][0][0])
                    if len(telegram_users_id['rows']) == 0:
                        id_domain = (check_id_domain['rows'][0][0])
                        db.commit("INSERT INTO users (name, domain_id, telegram_id) VALUES (%s, %s, %s)",
                                  message.from_user.username, id_domain, user_id)
                        bot.send_message(message.from_user.id,
                                         f"🌐 Домен: {domain_name_telegram}\n"
                                         f"✅ Успешно добавлен в базу данных\n"
                                         f"Для продолжения напишите /start или нажмите на кнопку 'Назад'")
                    else:
                        if user_id in telegram_users_id['rows'][0]:
                            bot.send_message(message.from_user.id,
                                             f"🌐 Домен: {domain_name_telegram} уже отслеживается.\n"
                                             f"Для продолжения напишите /start или нажмите на кнопку 'Назад'")
                        else:
                            id_domain = (check_id_domain['rows'][0][0])
                            db.commit("INSERT INTO users (name, domain_id, telegram_id) VALUES (%s, %s, %s)",
                                      message.from_user.username, id_domain, user_id)
                            bot.send_message(message.from_user.id,
                                             f"🌐 Домен: {domain_name_telegram}\n"
                                             f"✅ Успешно добавлен в базу данных\n"
                                             f"Для продолжения напишите /start или нажмите на кнопку 'Назад'")

    except ValueError:
        bot.send_message(message.from_user.id, f"Ошибка добавления домена. Напишите /start")
    except TypeError:
        bot.send_message(message.from_user.id, f"Ошибка добавления домена. Напишите /start")


def delete_site_bd(message):
    try:
        if message.text == 'Назад':
            get_text_messages(message)
        else:
            domain_id = message.text
            user_id = message.from_user.id
            db = MySQLi(host, user, password, database_home)
            check_delete = db.fetch("SELECT domain_id FROM users WHERE telegram_id = %s AND id_user = %s", user_id,
                                    domain_id)
            if len(check_delete['rows']) >= 1:
                db.commit("DELETE FROM users WHERE telegram_id = %s AND id_user = %s", user_id, domain_id)
                print(f"Пользователь {user_id} отправил заявку на удаление домена {domain_id} из БД")
                check_delete = db.fetch("SELECT domain_id FROM users WHERE telegram_id = %s AND domain_id = %s",
                                        user_id, domain_id)
                if int(len(check_delete['rows'])) == 0:
                    bot.send_message(message.from_user.id, f"Домен успешно удален. Продолжить /start")
                else:
                    bot.send_message(message.from_user.id,
                                     f"Указан некорректный id. Напишите /start и повторите команду")
            else:
                bot.send_message(message.from_user.id, f"Указан некорректный id. Напишите /start и повторите команду")
    except ValueError:
        bot.send_message(message.from_user.id, f"Указан некорректный id. Напишите /start и повторите команду")


def add_telephone(message):
    try:
        if message.text == 'Назад':
            get_text_messages(message)
        else:
            user_id = message.from_user.id
            print(f"Пользователь {user_id} пытается добавить номер телефона")
            status_number = correctly_telephone(message.text)
            print(status_number)
            if status_number == 'Error':
                bot.send_message(message.from_user.id, f"Указан некорректный номер телефона.\n"
                                                       f"Напишите /start и повторите команду")
            elif status_number == 'Success':
                telephone = message.text
                print(telephone)
                bot.send_message(message.from_user.id, f"Ваш оператор:\n"
                                                       f"/Tele2\n"
                                                       f"\n"
                                                       f"/MTS\n"
                                                       f"\n"
                                                       f"/Yota\n"
                                                       f"\n"
                                                       f"/Megafon\n"
                                                       f"\n"
                                                       f"/Beeline")
                insert_telephone(message.text, user_id)
                bot.register_next_step_handler(message, id_operator)

    except ValueError:
        bot.send_message(message.from_user.id, f"Указан некорректный номер. Напишите /start и повторите команду")


def id_operator(message):
    try:
        if message.text == 'Назад':
            get_text_messages(message)
        else:
            user_id = message.from_user.id
            if message.text == '/Tele2':
                update_mobile_operator(user_id, "Tele2")
                bot.send_message(message.from_user.id, f"Добавление номера завершено. Для продолжения напишите /start")
            elif message.text == '/MTS':
                update_mobile_operator(user_id, "MTS")
                bot.send_message(message.from_user.id, f"Рассылка на MTS невозможна. Для продолжения напишите /start и"
                                                       f" добавьте номер другого оператора.")
            elif message.text == '/Yota':
                update_mobile_operator(user_id, "Yota")
                bot.send_message(message.from_user.id, f"Добавление номера завершено. Для продолжения напишите /start")
            elif message.text == '/Megafon':
                update_mobile_operator(user_id, "Megafon")
                bot.send_message(message.from_user.id, f"Добавление номера завершено. Для продолжения напишите /start")
            elif message.text == '/Beeline':
                update_mobile_operator(user_id, "Beeline")
                bot.send_message(message.from_user.id, f"Добавление номера завершено. Для продолжения напишите /start")
            else:
                print("Ошибка указания оператора")
                bot.send_message(message.from_user.id, f"Указан некорректный моб. оператор. "
                                                       f"Напишите /start и повторите команду")

    except ValueError:
        bot.send_message(message.from_user.id, f"Указан некорректный id. Напишите /start и повторите команду")


def main():
    com = 'pgrep -f telegram.py'
    p = subprocess.Popen([com], stdout=subprocess.PIPE, shell=True)
    res = p.communicate()[0]
    if isinstance(res, bytes):
        res = res.decode("utf-8")
    res = [str(x) for x in res.split('\n') if len(x) > 0]
    print('Ожидаем 10 секунд')
    time.sleep(10)
    if len(res) >= 4:
        print('Процесс запущен. Запуск не требуется.')
    else:
        try:
            bot.polling(none_stop=True, interval=2)
        except Exception as err:
            logging.error(err)
            time.sleep(5)
            print("Internet error!")


if __name__ == '__main__':
    main()

#
