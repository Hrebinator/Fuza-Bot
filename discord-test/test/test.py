from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apscheduler.schedulers.asyncio import AsyncIOScheduler


import datetime
import discord
import asyncio
import time
import threading

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = 'https://www.googleapis.com/auth/calendar.readonly'
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Google Calendar API Python Quickstart'
scheduler = AsyncIOScheduler()


def get_credentials():
    """Gets valid user credentials from storage.

    If nothing has been stored, or if the stored credentials are invalid,
    the OAuth2 flow is completed to obtain the new credentials.

    Returns:
        Credentials, the obtained credential.
    """
    home_dir = os.path.expanduser('~')
    credential_dir = os.path.join(home_dir, '.credentials')
    if not os.path.exists(credential_dir):
        os.makedirs(credential_dir)
    credential_path = os.path.join(credential_dir,
                                   'calendar-python-quickstart.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)
        print('Storing credentials to ' + credential_path)
    return credentials

client = discord.Client()

async def schedTask():
    await client.wait_until_ready()
    while not client.is_closed:
        await asyncio.sleep(60)
    

def main():
    """Shows basic usage of the Google Calendar API.

    Creates a Google Calendar API service object and outputs a list of the next
    10 events on the user's calendar.
    """
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    eventsResult = service.events().list(
        calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        print(start, event['summary'])

if __name__ == '__main__':
    main()



def scheduled_event(message, event):
    client.loop.create_task(scheduled_event_coro(message, event))    
    print(time.time())



async def scheduled_event_coro(message, event):
    start = event['start'].get('dateTime', event['start'].get('date'))
    await client.send_message(message.channel.server.get_channel("413026872138399745"), '@everyone \n ```Event starting' + '\n' +  start + '\t' + event['summary'] + '```')
    print(time.time())

async def reQueue(message):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print(now)
    tomorrow = datetime.datetime.today().replace(hour= 0,minute=0,second=1,microsecond=0) + datetime.timedelta(days = 1)
    today = datetime.datetime.today().replace(hour= 0,minute=0,second=1,microsecond=0)
    await client.send_message(message.channel, 'Queueing the events for today')
    eventsResult = service.events().list(
        calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', timeMin=today.isoformat() + 'Z' , singleEvents=True, timeMax=tomorrow.isoformat() + 'Z',
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')            
    for event in events:
        start = datetime.datetime.strptime(event['start'].get('dateTime', event['start'].get('date')) + 'UTC', "%Y-%m-%dT%H:%M:%SZ%Z")
        start = start.replace(tzinfo=datetime.timezone.utc)
        print(start)
        print(start.tzname())
        scheduler.add_job(scheduled_event, 'date', run_date=start, args=(message, event))
        scheduler.add_job(reQueue, 'date', run_date=tomorrow, args={message})

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')
    scheduler.start()

@client.event
async def on_message(message):
    if message.content.startswith('!test'):
        counter = 0
        tmp = await client.send_message(message.channel, 'Calculating messages...')
        async for log in client.logs_from(message.channel, limit=100):
            if log.author == message.author:
                counter += 1

        await client.edit_message(tmp, 'You have {} messages.'.format(counter))
    elif message.content.startswith('!sleep'):
        await asyncio.sleep(5)
        await client.send_message(message.channel, 'Done sleeping')
    elif message.content.startswith('!upcoming'):
        """Shows basic usage of the Google Calendar API.

            Creates a Google Calendar API service object and outputs a list of the next
        10 events on the user's calendar.
    """
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        await client.send_message(message.channel, 'Getting the upcoming 10 events')
        eventsResult = service.events().list(
            calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', timeMin=now, maxResults=10, singleEvents=True,
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            await client.send_message(message.channel, 'No upcoming events found.')            
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            await client.send_message(message.channel, '```' +  start + '\t' + event['summary'] + '```')
    elif message.content.startswith('!queue'):
        credentials = get_credentials()
        http = credentials.authorize(httplib2.Http())
        service = discovery.build('calendar', 'v3', http=http)

        now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        print(now)
        tomorrow = datetime.datetime.today().replace(hour= 0,minute=0,second=1,microsecond=0) + datetime.timedelta(days = 1)
        today = datetime.datetime.today().replace(hour= 0,minute=0,second=1,microsecond=0)
        await client.send_message(message.channel, 'Queueing the events for today')
        eventsResult = service.events().list(
            calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', timeMin=today.isoformat() + 'Z' , singleEvents=True, timeMax=tomorrow.isoformat() + 'Z',
            orderBy='startTime').execute()
        events = eventsResult.get('items', [])

        if not events:
            print('No upcoming events found.')            
        for event in events:
            start = datetime.datetime.strptime(event['start'].get('dateTime', event['start'].get('date')) + 'UTC', "%Y-%m-%dT%H:%M:%SZ%Z")
            start = start.replace(tzinfo=datetime.timezone.utc)
            print(start)
            print(start.tzname())
            scheduler.add_job(scheduled_event, 'date', run_date=start, args=(message, event))
        scheduler.add_job(reQueue, 'date', run_date=tomorrow, args={message})
    elif message.content.startswith('!booze'):
        await client.send_message(message.channel, ':beer:')
    elif message.content.startswith('!sudoku'):
        await client.send_message(message.channel, 'Sudoku has been commited.')
client.loop.create_task(schedTask())
client.run('Mjk2OTU3MzM1NDUxMDc0NTYx.DWSy6Q.9DjdnMG8ucsodQ5Oay4wmi_5A_4')