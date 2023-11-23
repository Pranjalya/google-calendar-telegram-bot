#!/usr/bin/python3
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from pprint import pprint
import logging
from datetime import datetime, timedelta, time
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# For Python version < 3.8
# from backports.datetime_fromisoformat import MonkeyPatch

AUTH_LIST = [-436350771, 568333079]

jobs = {}

# NOT FOR Python3.8
# MonkeyPatch.patch_fromisoformat()

SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

creds = None
# The file token.pickle stores the user's access and refresh tokens, and is created automatically when the authorization flow completes for the first time.
if os.path.exists("token.pickle"):
    with open("token.pickle", "rb") as token:
        creds = pickle.load(token)

# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=8095)
        print("Creds : ", creds)
    # Save the credentials for the next run
    with open("token.pickle", "wb") as token:
        pickle.dump(creds, token)

service = build("calendar", "v3", credentials=creds)


def hello(update, context):
    """
    Command to get a congratulatory message greeting you.
    """
    print(datetime.now(), datetime.utcnow())
    update.message.reply_text("Hello {}".format(update.message.from_user.first_name))


def start(update, context):
    """
    Initial command for testing.
    """
    message = "Hey, I'm GoogleCalendarBot. These are my list of functions : \n/hello - Greeting\n/start or /help - Get the command list\n/getmyid - Get the chat or group id\n/getevents - Get the list of events in next 30 days once (max 15)\n/notify - Start sending daily notifications at that time\n\nI hope I'm useful :-)"
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)


def getmyid(update, context):
    """
    Command to get the effective id of the group/chat.
    """
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="The group or chat id is {}".format(update.effective_chat.id),
    )


def unknown(update, context):
    """
    Fallback command to return if the command is unidentified.
    """
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I didn't understand that command.",
    )


def getevents(update, context):
    """
    Prints the start and name of the next 15 events on the user's calendar.
    """
    if update.effective_chat.id in AUTH_LIST:
        # Call the Calendar API
        now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        days30 = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=days30,
                maxResults=15,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        answer = "Hey {}, here are your upcoming events in the next 30 days : ".format(
            update.message.from_user.first_name
        )
        context.bot.send_message(chat_id=update.effective_chat.id, text=answer)

        if not events:
            answer = "Sorry, you don't have any upcoming events in the next 30 days."
        i = 1
        answer = ""
        for event in events:
            answer += "EVENT #{}".format(i)
            if event["start"].get("dateTime") is not None:
                answer += "\nDate : " + datetime.fromisoformat(
                    event["start"]["dateTime"]
                ).strftime("%d-%m-%Y, %A")
                answer += "\nTime : " + datetime.fromisoformat(
                    event["start"]["dateTime"]
                ).strftime("%I:%M %p GMT %Z")
            elif event["start"].get("date") is not None:
                answer += "\nDate : " + datetime.fromisoformat(
                    event["start"]["date"]
                ).strftime("%d-%m-%Y, %A")
                answer += "\nTime : Not mentioned"
            answer += "\nEvent Name : {}".format(event["summary"])
            if "location" in event.keys():
                answer += "\nLocation : {}".format(event["location"])
            i += 1
            answer += "\n\n\n"
        context.bot.send_message(chat_id=update.effective_chat.id, text=answer)
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="Sorry, you are not authorized."
        )


def startevents(context):
    """
    Prints the start and name of the next 15 events on the user's calendar.
    """
    try:
        if jobs.get(context.job.context, None) is not None:
            if context.job.context in AUTH_LIST:
                # Call the Calendar API
                now = datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
                days30 = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"
                events_result = (
                    service.events()
                    .list(
                        calendarId="primary",
                        timeMin=now,
                        timeMax=days30,
                        maxResults=15,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
                events = events_result.get("items", [])

                context.bot.send_message(
                    chat_id=context.job.context,
                    text="Here are your upcoming events in the next 30 days : ",
                )

                i = 1
                answer = ""

                if not events:
                    answer = (
                        "Sorry, you don't have any upcoming events in the next 30 days."
                    )

                for event in events:
                    answer += "EVENT #{}".format(i)

                    if event["start"].get("dateTime") is not None:
                        answer += "\nDate : " + datetime.fromisoformat(
                            event["start"]["dateTime"]
                        ).strftime("%d-%m-%Y, %A")
                        answer += "\nTime : " + datetime.fromisoformat(
                            event["start"]["dateTime"]
                        ).strftime("%I:%M %p GMT %Z")
                    elif event["start"].get("date") is not None:
                        answer += "\nDate : " + datetime.fromisoformat(
                            event["start"]["date"]
                        ).strftime("%d-%m-%Y, %A")
                        answer += "\nTime : Not mentioned"

                    answer += "\nEvent Name : {}".format(event["summary"])

                    if "location" in event.keys():
                        answer += "\nLocation : {}".format(event["location"])

                    i += 1
                    answer += "\n\n\n"

                context.bot.send_message(chat_id=context.job.context, text=answer)
            else:
                context.bot.send_message(
                    chat_id=context.job.context, text="Sorry, you are not authorized."
                )
    except Exception as e:
        print(e)
        startevents(context)


def start_job(update, context):
    """
    Starts the daily job of sending notifications.
    """
    if jobs.get(update.effective_chat.id, None) == None:
        t = (
            datetime.now() - timedelta(hours=5, minutes=30) + timedelta(seconds=30)
        ).time()
        localtime = (datetime.now() + timedelta(seconds=30)).time()

        # Replace time=t with time=fixed_time if you want to send it at a fixed time instead. Remember this time is in UTC.
        ## fixed_time = time(0,0)
        print(t, localtime)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="I'm going to start sending notifications at {} daily.".format(
                localtime.strftime("%I:%M %p")
            ),
        )
        job_daily = context.job_queue.run_daily(
            startevents,
            time=t,
            days=(0, 1, 2, 3, 4, 5, 6),
            context=update.effective_chat.id,
            name="Daily notification at {}".format(t),
        )
        jobs[update.effective_chat.id] = job_daily

    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="You have already scheduled a notifcation sprint at {}".format(
                jobs.get(update.effective_chat.id).next_t.strftime("%I:%M %p UTC")
            ),
        )


def stop_job(update, context):
    if jobs.get(update.effective_chat.id):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sure, I'll stop sending notifications.",
        )
        jobs[update.effective_chat.id] = None
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id, text="You have no schduled notifications."
        )


def main():
    """
    1. Automate Google Calendar Events to post on Telegram using Telegram Bot daily
    2. Able to be use on PythonAnywhere.com
    3. Able to show up to 15 events within 30 days in the calendar.
    4. Telegram to show: DD-MM-YYYY, Time of Event, Event Name, Venue of Event
    5. Provide full script and guide on obtaining the correct credential for Google calendar api
    """
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    updater = Updater("<telegram-bot-key>", use_context=True)

    updater.dispatcher.add_handler(CommandHandler("hello", hello))
    updater.dispatcher.add_handler(CommandHandler("start", start))
    updater.dispatcher.add_handler(CommandHandler("help", start))
    updater.dispatcher.add_handler(CommandHandler("getmyid", getmyid))
    updater.dispatcher.add_handler(
        CommandHandler("notify", start_job, pass_job_queue=True)
    )
    updater.dispatcher.add_handler(
        CommandHandler("stop", stop_job, pass_job_queue=True)
    )
    updater.dispatcher.add_handler(CommandHandler("getevents", getevents))
    updater.dispatcher.add_handler(MessageHandler(Filters.command, unknown))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
