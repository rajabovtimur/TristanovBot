import requests.packages.urllib3, json
requests.packages.urllib3.disable_warnings()

import logging, datetime
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram import CallbackQuery, Message

from storage import DataStore

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
level=logging.INFO)

CLB_LESSON_BYDAY = 'window_byday'
CLB_LESSON_BYDATE = 'window_bydate'
CLB_LESSON_LAB = 'window_lab'
CLB_LESSON_LAB_SELECT = 'labds'
CLB_WINDOW_HELP = 'window_help'
CLB_WINDOW_MENU = 'window_menu'
CLB_WINDOW_SELECT_GROUP = 'wdwsel_gr'
CLB_WINDOW_SELECT_DISCIPLINE = 'wdwsel_ds'

CONST_TXT_MENU = 'text:menu'
CONST_TXT_LESSON_BYDAY = 'text:lesson:byday'
CONST_TXT_LESSON_BYDATE = 'text:lesson:bydate'
CONST_TXT_LESSON_LAB = 'text:lesson:lab'
CONST_TXT_LAB_NOLABS = 'text:nolabs'
CONST_TXT_LESSON_NOLESSONS = 'text:no_lessons'
CONST_TXT_BACK = 'text:back'
CONST_TXT_HELP = 'text:help'
CONST_TXT_SELECT_GROUP = 'text:select_group'
CONST_TXT_SELECT_DISCIPLINE = 'text:select_discipline'

datastore = DataStore()

def serialize_path(route, args=[]):
    items = [route]
    items.extend( map(lambda x:str(x), args) )
    return ':'.join( items )

def deserialize_path(callback_query):
    path = callback_query.data
    items = path.split(":")
    return items[0], items[1:]

def window_start(bot, update):
    # print word("{say} world {say}", {'say': 'hello', 'unknown': '1'})
    # logging.info(update)
    user_id = update.message.chat.id
    update.message.reply_text(word('text:welcome'))
    if datastore.get_user_group(user_id) is None:
        window_select_group(bot, update)
    else:
        window_menu(bot, update)

def window_select_group(bot, update):
    keyboard = []
    for i in datastore.groups():
        keyboard.append([ InlineKeyboardButton( i, callback_data=serialize_path(CLB_WINDOW_SELECT_GROUP, [i])) ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    query = update.callback_query
    if query:
        route, items = deserialize_path(query)
        if len(items) == 0:
            # show select groups
            bot.edit_message_text( word(CONST_TXT_SELECT_GROUP), 
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        reply_markup=reply_markup )
        else:
            # user selected group
            datastore.set_user_group(query.message.chat_id, items[0])
            window_menu(bot, update)
    else:
        # just send
        update.message.reply_text(word(CONST_TXT_SELECT_GROUP), reply_markup=reply_markup)

def window_help(bot, update):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton( word(CONST_TXT_BACK), callback_data=CLB_WINDOW_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.edit_message_text(word(CONST_TXT_HELP), 
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            reply_markup=reply_markup)

def window_lesson_byday(bot, update):
    query = update.callback_query

    days = [
        "day_mon",
        "day_tue",
        "day_wed",
        "day_thu",
        "day_fri",
        "day_sat"
    ]
    keyboard = []
    for idx in range(0, len(days), 2):
        d = days[idx]
        res = []
        res.append(
            InlineKeyboardButton( word(d), callback_data=serialize_path(CLB_LESSON_BYDAY, [d]) )
        )
        if idx+1 < len(days):
            d = days[idx+1]
            res.append(
                InlineKeyboardButton( word(d), callback_data=serialize_path(CLB_LESSON_BYDAY, [d]) )
            )
        keyboard.append(res)
    keyboard.append([
        InlineKeyboardButton( word(CONST_TXT_BACK), callback_data=CLB_WINDOW_MENU)
    ])

    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        route, items = deserialize_path(query)
        if len(items) == 0:
            # show days
            bot.edit_message_text(word(CONST_TXT_LESSON_BYDAY),
                        chat_id=query.message.chat_id,
                        message_id=query.message.message_id,
                        reply_markup=reply_markup)
        else:
            # user selected day, show schedule and show this page again
            selected = items[0]
            group = datastore.get_user_group(query.message.chat.id)
            schedules = datastore.schedule_byday(group, days.index(selected))
            res = []
            for s in schedules:
                res.append( '- [%s]: %s - %s' % (s['discipline'], s['start'], s['end']) )

            if res:
                bot.sendMessage(query.message.chat_id, "\n".join(res) )
            else:
                bot.sendMessage(query.message.chat_id, word(CONST_TXT_LESSON_NOLESSONS) )
            update.callback_query = None
            update.message = query.message
            window_lesson_byday(bot, update)
    else:
        update.message.reply_text(word(CONST_TXT_LESSON_BYDAY), reply_markup=reply_markup)

def window_lesson_bydate(bot, update):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton( word(CONST_TXT_BACK), callback_data=CLB_WINDOW_MENU)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    datastore.set_user_state(query.message.chat.id, CLB_LESSON_BYDATE)
    bot.edit_message_text(word(CONST_TXT_LESSON_BYDATE), 
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            reply_markup=reply_markup)

def window_lesson_lab(bot, update):
    query = update.callback_query
    group = None
    if query:
        group = datastore.get_user_group(query.message.chat.id)
    else:
        group = datastore.get_user_group(update.message.chat.id)
    keyboard = []
    for d in datastore.schedule_lab_disciplines(group):
        trimmed = d[:5]
        keyboard.append([
            InlineKeyboardButton( d, callback_data=serialize_path(CLB_LESSON_LAB_SELECT, [trimmed])),
        ])

    keyboard.append([
        InlineKeyboardButton( word(CONST_TXT_BACK), callback_data=CLB_WINDOW_MENU)
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if query:
        bot.edit_message_text(word(CONST_TXT_LESSON_LAB), 
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            reply_markup=reply_markup)
    else:
        update.message.reply_text(word(CONST_TXT_LESSON_LAB), reply_markup=reply_markup)


def window_lesson_lab_select(bot, update):
    # comes when lab has been selected
    query = update.callback_query
    group = datastore.get_user_group(query.message.chat.id)

    route, items = deserialize_path(query)
    selected_discipline = items[0]
    discipline = None
    for d in datastore.schedule_lab_disciplines(group):
        trimmed = d[:5]
        if trimmed == selected_discipline:
            discipline = d
            break
    if discipline is None:
        update.callback_query = None
        update.message = query.message
        window_lesson_lab(bot, update)
        return

    labs = datastore.schedule_labs_bydiscipline(group, discipline)
    res = []
    for b in labs:
        res.append('- [%s]: %s - %s' % (b["title"], b["start"], b["end"]))
    if res:
        bot.sendMessage(query.message.chat_id, "\n".join(res) )
    else:
        bot.sendMessage(query.message.chat_id, word(CONST_TXT_LAB_NOLABS))
    # update.message.reply_text("\n".join(res))
    update.callback_query = None
    update.message = query.message
    window_lesson_lab(bot, update)


def window_menu(bot, update):
    query = getattr(update, 'callback_query', None)
    keyboard = [
        [
            InlineKeyboardButton( word(CLB_LESSON_BYDAY), callback_data=CLB_LESSON_BYDAY), 
            InlineKeyboardButton( word(CLB_LESSON_BYDATE), callback_data=CLB_LESSON_BYDATE)
        ],
        [InlineKeyboardButton( word(CLB_LESSON_LAB), callback_data=CLB_LESSON_LAB)],
        [InlineKeyboardButton( word(CLB_WINDOW_HELP), callback_data=CLB_WINDOW_HELP)],
        [InlineKeyboardButton( word(CLB_WINDOW_SELECT_GROUP), callback_data=CLB_WINDOW_SELECT_GROUP)]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    if query:
        bot.edit_message_text(word(CONST_TXT_MENU), 
                            chat_id=query.message.chat_id,
                            message_id=query.message.message_id,
                            reply_markup=reply_markup)
    else:
        update.message.reply_text(word(CONST_TXT_MENU), reply_markup=reply_markup)

def window_plaintext(bot, update):
    user_id = update.message.chat.id
    state = datastore.get_user_state(user_id)
    if state is None:
        window_start(bot, update)
        return
    if state == CLB_LESSON_BYDATE:
        # parse date here and show lesson by date
        dt = None
        try:
            dt = datetime.datetime.strptime(update.message.text, "%Y/%m/%d")
        except Exception as e:
            keyboard = [
                [InlineKeyboardButton( word(CONST_TXT_BACK), callback_data=CLB_WINDOW_MENU)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            update.message.reply_text(word(CONST_TXT_LESSON_BYDATE),
                                    reply_markup=reply_markup)
            return
        datastore.set_user_state(user_id, None)
        group = datastore.get_user_group(user_id)
        if group is None:
            window_start(bot, update)
            return 
        schedules = datastore.schedule_bydate(group, dt)
        res = []
        for s in schedules:
            res.append( '- [%s]: %s - %s' % (s['discipline'], s['start'], s['end']) )

        if res:
            update.message.reply_text("\n".join(res))
        else:
            update.message.reply_text(word(CONST_TXT_LESSON_NOLESSONS))
        window_menu(bot, update)


CALLBACK_HANDLER = {
    CLB_LESSON_BYDAY: window_lesson_byday,
    CLB_LESSON_BYDATE: window_lesson_bydate,
    CLB_LESSON_LAB: window_lesson_lab,
    CLB_LESSON_LAB_SELECT: window_lesson_lab_select,
    CLB_WINDOW_HELP: window_help,
    CLB_WINDOW_MENU: window_menu,
    CLB_WINDOW_SELECT_GROUP: window_select_group
}

def window_callback(bot, update):
    query = update.callback_query
    data = query.data

    route = data.split(':')[0]

    if route in CALLBACK_HANDLER.keys():
        CALLBACK_HANDLER[route](bot, update)
    else:
        print 'not found: ', data

GLOB_WORDS = {}
def word(st, mp={}):
    w = GLOB_WORDS.get(st, st)
    return w.format(mp)

def parse_lang():
    global GLOB_WORDS
    with open("lang.json") as fl:
        lines = fl.readlines()
        content = ''.join(lines)
        GLOB_WORDS = json.loads(content)

def parse_file():
    datastore.set_groupfile("db/groups.json")
    datastore.set_labfile("db/labs.json")
    datastore.set_schedulefile("db/schedule.json")
    datastore.set_userinfofile("db/userinfo.json")

updater = Updater('273367922:AAGW_1ByYH-ylPx_O-s186fq9reXTxCbSi4')

updater.dispatcher.add_handler(CommandHandler('start', window_start))
updater.dispatcher.add_handler(CommandHandler('help', window_help))
updater.dispatcher.add_handler(CallbackQueryHandler(window_callback))
updater.dispatcher.add_handler(MessageHandler(Filters.text, window_plaintext))

parse_lang()
parse_file()

updater.start_polling()
updater.idle()
