
from app import app, bot, db
from app.models import Message, Friend, Claimant, Link, Admin
from datetime import datetime
from datetime import timedelta
import time
from apscheduler.schedulers.background import BackgroundScheduler
import telegram


def general_send(message, *args, need_save=False, **kwargs):
    if message.text:
        bot_message = bot.sendMessage(
            chat_id=kwargs.get('chat_id'),
            reply_to_message_id=kwargs.get('reply_to_message_id'),
            text=message.text.encode('utf-8').decode())
        if need_save:
            save_link(message, bot_message)
    elif message.video:
        bot_message = bot.sendVideo(
            chat_id=kwargs.get('chat_id'),
            reply_to_message_id=kwargs.get('reply_to_message_id'),
            video=message.video.file_id,
            caption=message.caption)
        if need_save:
            save_link(message, bot_message)
    elif message.voice:
        bot_message = bot.sendVoice(
            chat_id=kwargs.get('chat_id'),
            reply_to_message_id=kwargs.get('reply_to_message_id'),
            voice=message.voice.file_id,
            caption=message.caption)
        if need_save:
            save_link(message, bot_message)
    elif message.animation:
        bot_message = bot.sendAnimation(
            chat_id=kwargs.get('chat_id'),
            reply_to_message_id=kwargs.get('reply_to_message_id'),
            animation=message.animation.file_id,
            caption=message.caption)
        if need_save:
            save_link(message, bot_message)
    elif message.document:
        bot_message = bot.sendDocument(
            chat_id=kwargs.get('chat_id'),
            reply_to_message_id=kwargs.get('reply_to_message_id'),
            document=message.document.file_id,
            caption=message.caption)
        if need_save:
            save_link(message, bot_message)
    elif message.photo:
        bot_message = bot.sendPhoto(
            chat_id=kwargs.get('chat_id'),
            reply_to_message_id=kwargs.get('reply_to_message_id'),
            photo=message.photo[-1].file_id,
            caption=message.caption)
        if need_save:
            save_link(message, bot_message)


def save_link(message, bot_message):
    link = Link(from_chat_id=message.chat.id,
                source_message_id=message.message_id,
                current_message_id=bot_message.message_id,
                claimant=str(message.from_user.username).lower())

    db.session.add(link)
    db.session.commit()


def keyboard_send(admin_cid):
    button3 = telegram.KeyboardButton(text='/показать_друга')
    button2 = telegram.KeyboardButton(text='/показать_взыскателей')
    button1 = telegram.KeyboardButton(text='/help')
    button8 = telegram.KeyboardButton(text='/удалить_всех')
    button4 = telegram.KeyboardButton(text='/статистика')
    button6 = telegram.KeyboardButton(text='/обновить_друга')
    button7 = telegram.KeyboardButton(text='/добавить_взыскателя')
    button5 = telegram.KeyboardButton(text='/удалить_взыскателя')
    button9 = telegram.KeyboardButton(text='/отправить_всем')
    mes = telegram.ReplyKeyboardMarkup(keyboard=[[button1], [button9], [button2],
                                                 [button3], [button4],
                                                 [button5], [button6],
                                                 [button7], [button8]],
                                       resize_keyboard=True,
                                       one_time_keyboard=True)
    bot.sendMessage(chat_id=admin_cid, text='Выберете команду:',
                    reply_markup=mes)
    return 'ok'


class AdminExec:
    def __init__(self, state=0):
        self.state = state
        self.command = ''

    def exec(self, val, admin_cid):
        if self.state == 0:
            if val[0] == '/':
                text = val[1:]
                self.command = text.split()[0]
                if self.command in ['показать_друга', 'показать_взыскателей', 'help',
                                    'удалить_всех', 'статистика']:
                    make_cmd(cmd=self.command)
                    keyboard_send(admin_cid)
                else:
                    self.state = 1
                    if (self.command == 'обновить_друга') and (Friend.query.first()):
                        bot.sendMessage(chat_id=admin_cid,
                                        text='Напоминаю, что старый юзернейм друга перезапишется новым. Введите, пожалуйста, новый юзернейм пользователя.')
                    elif self.command == 'отправить_всем':
                        bot.sendMessage(chat_id=admin_cid,
                                        text='Введите сообщение для взыскателей.')
                    else:
                        bot.sendMessage(chat_id=admin_cid,
                                        text='Введите юзернейм пользователя.')
        else:
            self.state = 0
            make_cmd(cmd=self.command, name=val)
            keyboard_send(admin_cid)


admin_exec = AdminExec()


def make_cmd(cmd=None, name=None):
    a = Admin.query.first()
    admin_cid = a.chat_id
    app.logger.info(f'Command: {cmd}')
    need_update = False

    if (cmd == 'обновить_друга') and name:
        app.logger.info(f'Adding friend...')
        f = Friend.query.first()
        if f:
            Friend.query.delete()
            db.session.commit()
        r = Friend(name=str(name).lower())
        db.session.add(r)
        need_update = True

    elif (cmd == 'добавить_взыскателя') and name:
        app.logger.info(f'Adding claimant...')
        r = Claimant(name=str(name).lower())
        db.session.add(r)
        need_update = True

    # elif cmd == 'add_several_claimants':
    #     print('adding several claimants')
    #     claims =
    #     r = Claimant(name=name)
    #     db.session.add(r)
    #     need_update = True

    elif (cmd == 'отправить_всем') and name:
        cs_raw = Claimant.query.all()
        cs = [x.name for x in cs_raw]
        links_raw = Link.query.distinct(Link.from_chat_id)
        chats = [x.from_chat_id for x in links_raw if x.claimant in cs]
        for clai in chats:
            bot.sendMessage(chat_id=clai, text=name)
            time.sleep(1)
        bot.sendMessage(chat_id=admin_cid, text='Сообщение отправлено всем взыскателям.')

    elif cmd == 'показать_друга':
        friend = Friend.query.first()
        if friend:
            text = friend.name
        else:
            text = 'No friend'
        bot.sendMessage(chat_id=admin_cid, text=text)

    elif cmd == 'показать_взыскателей':
        cs_raw = Claimant.query.all()
        cs = [x.name for x in cs_raw]
        if cs:
            bot.sendMessage(chat_id=admin_cid, text=(', '.join(cs)))
        else:
            bot.sendMessage(chat_id=admin_cid, text='No claimants')

    elif cmd == 'help':
        bot.sendMessage(chat_id=admin_cid, text='''Для настройки бота надо:

Перед запуском приложения в файле config.py указать username админа бота, в формате без "@", либо же указать в переменной окружения 'ADMIN', пример "test_user0"
Админ должен найти бота "ClaimantBot" и написать ему "/start", дождаться ответа бота со справкой.
Админ с помощью команд "/обновить_друга" и "/добавить_взыскателя" может обновлять username друга и добавлять username взыскателей соответственно, например: нажать кнопку "/обновить_друга", дожидаемся ответа бота, отправляем username друга "test_user1"; нажать кнопку  "/добавить_взыскателя", дожидаемся ответа бота, отправляем username взыскателя "test_user2".
После добавления друга командой "/обновить_друга" друг должен найти бота и отправить ему любое сообщение, бот ответит "Все готово!"
После добавления взыскателей они должны найти бота, отправить ему сообщение, эти сообщения попадают к другу, друг может отвечать на них с помощью стандартного функционала телеграма "ответить".
Для админа также существуют команды:

/показать_друга - показывает username друга
/показать_взыскателей - показывает username всех взыскателей
/удалить_всех - удаляет username и друга, и всех взыскателей
/удалить_взыскателя - удаляет username взыскателя, используется: нажатие кнопки команды, дожидаемся ответа бота, отправляем username взыскателя
/статистика - показывает статистику использования бота''')

    elif cmd == 'test_cmd':
        return 'all is good'

    elif cmd == 'удалить_всех':
        app.logger.info(f'Deleting all...')
        Friend.query.delete()
        Claimant.query.delete()
        need_update = True

    elif (cmd == 'удалить_взыскателя') and name:
        app.logger.info(f'Deleting claimant...')
        app.logger.info(f'{name}')
        # b = Claimant.query.filter_by(name=str(name).lower()).first()
        # if b:
        #     app.logger.info(f'{b.name}')
        #     b.delete()
        #     db.session.commit()
        Claimant.query.filter_by(name=str(name).lower()).delete()
        need_update = True

    elif cmd == 'статистика':
        b = datetime.now()
        count_today = Message.query.filter(
            Message.timestamp >= datetime(b.year, b.month, b.day))
        count_daily = Message.query.filter(
            Message.timestamp >= (b - timedelta(days=1)))
        claimant_today = count_today.filter(
            Message.from_claimant == True).count()
        claimant_daily = count_daily.filter(
            Message.from_claimant == True).count()
        count_today = count_today.count()
        count_daily = count_daily.count()
        last_7day = Message.query.filter(Message.timestamp >= (
            datetime(b.year, b.month, b.day)) - timedelta(days=7))
        claimant_last_7day = last_7day.filter(
            Message.from_claimant == True).count()
        last_30day = Message.query.filter(Message.timestamp >= (
            datetime(b.year, b.month, b.day)) - timedelta(days=30))
        claimant_last_30day = last_30day.filter(
            Message.from_claimant == True).count()
        last_7day = last_7day.count()
        last_30day = last_30day.count()
        count_all = Message.query
        claimant_count_all = count_all.filter(
            Message.from_claimant == True).count()
        count_all = count_all.count()

        resp = f'''Сообщений за этот день: {count_today}
Сообщений за последние сутки: {count_daily}
Сообщений за этот день от взыскателей: {claimant_today}
Сообщений за последние сутки от взыскателей: {claimant_daily}
Сообщений за неделю: {last_7day}
Сообщений за месяц: {last_30day}
Сообщений за неделю от взыскателей: {claimant_last_7day}
Сообщений за месяц от взыскателей: {claimant_last_30day}
Всего сообщений: {count_all}
Всего сообщений от взыскателей: {claimant_count_all}\n'''

        claimants = Claimant.query.all()
        claimants = [str(cl.name).lower() for cl in claimants]
        for cl in claimants:
            base_query = Message.query.filter(Message.from_user == cl)
            resp += f'  {cl}: {base_query.filter(Message.timestamp >= datetime(b.year, b.month, b.day)).count()} за день, \
{base_query.filter(Message.timestamp >= (b - timedelta(days=1))).count()} за сутки, \
{base_query.filter(Message.timestamp >= (datetime(b.year, b.month, b.day)) - timedelta(days=7)).count()} за неделю, \
{base_query.count()} сообщений всего.\n'

        bot.sendMessage(chat_id=admin_cid, text=resp)
    else:
        bot.sendMessage(chat_id=admin_cid, text='Что-то не так...')

    if need_update:
        db.session.commit()
        bot.sendMessage(chat_id=admin_cid, text='Сделано!')
        app.logger.info(f'Successful db commit!')


def respond(update):

    # update = telegram.Update.de_json(request.get_json(force=True), bot)
    app.logger.debug(f'update_id: {update.update_id}')
    info = bot.get_webhook_info()
    app.logger.debug(f'pending_update_count: {info.pending_update_count}')

    message = update.message
    app.logger.info(
        f'''from: {message.from_user.username}, message: {message.text}, mgi: {message.media_group_id}''')

    # админская часть
    try:
        if (str(message.from_user.username).lower() == str(app.config['ADMIN']).lower()) and\
                (message.text) and\
                ((message.text.encode('utf-8').decode()[0] == '/') or\
                 admin_exec.state == 1):
            text = message.text.encode('utf-8').decode()[1:]
            cmd = text.split()[0]

            if cmd == 'start':
                a = Admin.query.first()
                if a:
                    Admin.query.delete()
                    db.session.commit()
                a = Admin(name=str(app.config['ADMIN']).lower(), chat_id=message.chat.id)
                db.session.add(a)
                db.session.commit()

                bot.sendMessage(chat_id=message.chat.id, text='''Используй /help для описания возможных команд.''')
                keyboard_send(message.chat.id)
                # bot.sendMessage(chat_id=message.chat.id, text='Start!')
                return 'ok'

            # if len(text.split()) == 2:
            #     name = text.split()[1]
            # else:
            #     name = None

            # make_cmd(cmd=cmd, name=name)
            admin_exec.exec(message.text.encode('utf-8').decode(),
                            message.chat.id)
            return 'ok'

        # elif (message.from_user.username == app.config['ADMIN']):
        #     return 'ok'

    except Exception as e:
        app.logger.error(f'Error: {e}')
        return 'ok'

    # вытаскиваем имена взыскателей
    claimants_raw = Claimant.query.all()
    claimants = [str(x.name).lower() for x in claimants_raw]

    # вытаскивем имя друга
    friend = Friend.query.first()
    if not friend:
        return 'ok'

    try:
        # выясняем кому сообщение
        if str(message.from_user.username).lower() in claimants:
            to_user = str(friend.name).lower()
            from_claimant = True
        else:
            link = Link.query.filter_by(
                current_message_id=message.reply_to_message.message_id).first()
            to_user = str(link.claimant).lower()
            from_claimant = False
    # если друг решил отправить сообщение в никуда
    except Exception as e:
        friend = Friend.query.first()
        if friend and (str(message.from_user.username).lower() == str(friend.name).lower()) and (friend.chat_id):
            bot.sendMessage(chat_id=message.chat.id, text='Сообщение не доставлено. Нужно выбрать входящее сообщение, на которое отвечаете. Только так ответ будет доставлен нужному адресату.')
        app.logger.warning(f'to-whom error: {e}')
        to_user = None
        from_claimant = False

    # вытаскиваем file_id если есть
    if message.photo:
        file_id = [message.photo[-1].file_id]
    elif message.document:
        file_id = [message.document.file_id]
    elif message.voice:
        file_id = [message.voice.file_id]
    elif message.video:
        file_id = [message.video.file_id]
    elif message.animation:
        file_id = [message.animation.file_id]
    else:
        file_id = []

    # пытаемся выдрать текст если это обычный текст
    if message.text:
        t_b = message.text.encode('utf-8').decode()
    # если не получилось то берем caption
    elif message.caption:
        t_b = message.caption
    else:
        t_b = None

    # сохранение в БД
    # если не медиагруппа или первое сообщение из медиагруппы
    if (not message.media_group_id) or\
            (message.media_group_id and
             (not Message.query.filter_by(
                 media_group_id=message.media_group_id).first())):

        # сохраняем сообщение в БД
        m = Message(tlg_chat_id=message.chat.id,
                    tlg_msg_id=message.message_id,
                    text=t_b,
                    media_group_id=message.media_group_id,
                    from_user=str(message.from_user.username).lower(),
                    to_user=str(to_user).lower(),
                    file_ids=file_id,
                    from_claimant=from_claimant)

        db.session.add(m)
        db.session.commit()

        # if message.media_group_id:
        #     return 'ok'

    try:
        # если не первое сообщение из медиагруппы
        if message.media_group_id:
            old_message = Message.query.filter_by(
                media_group_id=message.media_group_id).first()
            if old_message:
                app.logger.debug(
                    f'old_message.file_ids: {old_message.file_ids}')
                old_files = old_message.file_ids
                if message.photo:
                    old_files.append(message.photo[-1].file_id)
                elif message.video:
                    old_files.append(message.photo[-1].file_id)
                old_message.file_ids = old_files

                db.session.commit()

                # # если последнее сообщение
                # if bot.get_webhook_info().pending_update_count == 1:

                #     if to_user == friend.name:
                #         chat_id = friend.chat_id
                #     else:
                #         chat_id = Link.query.filter_by(
                #             claimant=to_user).first().from_chat_id

                #     media = []
                #     for i, file in enumerate(old_message.file_ids):
                #         print(f'file: {file}')
                #         if i != 0:
                #             media.append(telegram.InputMediaPhoto(media=file))
                #         else:
                #             media.append(telegram.InputMediaPhoto(
                #                 media=file, caption=old_message.text))

                #     bot.sendMediaGroup(chat_id=chat_id, media=media)

    except Exception as e:
        app.logger.error(f'Error: {e}')
        return 'ok'

    # если сообщение от друга и с пересылкой
    if (str(message.from_user.username).lower() == str(friend.name).lower()) and\
            (message.reply_to_message is not None):

        cl_chat_id_raw = Link.query\
            .filter_by(current_message_id=message.reply_to_message.message_id)\
            .first()
        if cl_chat_id_raw:  # and not message.media_group_id:
            # пытаемся отправить, если не получается
            # то ответное сообщение удалено
            try:
                general_send(
                    message,
                    chat_id=cl_chat_id_raw.from_chat_id,
                    reply_to_message_id=cl_chat_id_raw.source_message_id)
            except Exception as e:
                app.logger.warning(f'Reply message is deleted! {e}')
                general_send(message, chat_id=cl_chat_id_raw.from_chat_id)
        else:
            a = Admin.query.first()
            admin_cid = a.chat_id
            bot.sendMessage(chat_id=admin_cid, text='error...')

    # если сообщение от друга без пересылки и не сохранен айдишник чата
    elif (str(message.from_user.username).lower() == str(friend.name).lower()) and (not friend.chat_id):
        friend.chat_id = message.chat.id
        db.session.commit()
        bot.sendMessage(chat_id=message.chat.id, text='Все готово!')

    # если сообщение от взыскателя
    elif (str(message.from_user.username).lower() in claimants):  # and\
        # (not message.media_group_id):
        general_send(message, need_save=True, chat_id=friend.chat_id)
    else:
        app.logger.warning(f'Warning: another case!')
        app.logger.debug(f'message.message_id: {message.message_id}')

    return 'ok'


@app.route('/healthcheck', methods=['GET', 'POST'])
def healthcheck():
    return 'ok'


offset = 0


def test_scheduler():
    global offset
    print("Polling...")
    print(time.time())
    if offset == 0:
        updates = bot.getUpdates(timeout=2)
    else:
        updates = bot.getUpdates(offset=(offset + 1), timeout=2)
    for update in updates:
        offset = update.update_id
        try:
            a = respond(update)
            app.logger.debug(f'respond: {a}')
            print(a)
        except Exception as e:
            app.logger.error(f'ERROR: {e}')


scheduler = BackgroundScheduler()
scheduler.add_job(test_scheduler, 'interval', seconds=5)
scheduler.start()
app.logger.info(f'Scheduler started!')
