#!/usr/bin/env python3

from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import Table, Column, Integer, String, MetaData, ForeignKey


import datetime
import rfc3339      # for date object -> date string
import iso8601      # for date string -> date object
import discord
import asyncio
import time
import sqlalchemy
from discord.ext import commands
import logging

"""Setting up debug logging"""
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)




try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

engine = sqlalchemy.create_engine('mysql://bot:f+?@upri-oP=c6etrast@localhost/bot_data')
metadata = MetaData()
users = Table('users', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(50)),
    Column('fullname', String(50)),
)
addresses = Table('addresses', metadata,
  Column('id', Integer, primary_key=True),
  Column('user_id', None, ForeignKey('users.id')),
  Column('email_address', String(50), nullable=False)
)
metadata.create_all(engine)

# If modifying these scopes, delete your previously saved credentials
# at ~/.credentials/calendar-python-quickstart.json
SCOPES = {'https://www.googleapis.com/auth/calendar', 'https://www.googleapis.com/auth/spreadsheets'}
CLIENT_SECRET_FILE = 'client_secret.json'
APPLICATION_NAME = 'Discord Xreni Bot'

jobstores = {
    'default': SQLAlchemyJobStore(url='mysql://bot:f+?@upri-oP=c6etrast@localhost/jobs')
}


scheduler = AsyncIOScheduler(jobstores = jobstores)

description = '''An example bot to showcase the discord.ext.commands extension
module.
There are a number of utility commands being showcased here.'''
bot = commands.Bot(command_prefix='!', description=description)


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
                                   'discord-xreni-bot.json')

    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        flow.user_agent = APPLICATION_NAME
        credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials
 
credentials = get_credentials()
http = credentials.authorize(httplib2.Http())
calenderService = discovery.build('calendar', 'v3', http=http)   

def main():
    #credentials = get_credentials()
    #http = credentials.authorize(httplib2.Http())
    #calenderService = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print('Getting the upcoming 10 events')
    eventsResult = calenderService.events().list(
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



async def event_reminder(channelID, event):
    content = "@everyone \n The event '" + event['summary'] + "' is starting in 30 min. \n Please remember to come."    
    await bot.send_message(bot.get_channel(channelID), content = content)
    print(time.time())
    
    
async def scheduled_event_coro(channelID, event):
    """main event reminder, quite unreadable"""
    embed = discord.Embed(title="`NEW EVENT STARTING!`", colour=discord.Colour(0x4a078b), url=event['htmlLink'], description="The event " +event['summary'] + " is starting.")
    embed.set_image(url="https://cdn.discordapp.com/attachments/413026441429778432/418760731362590721/ffxiv_06012018_005010.png")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/296957586362597386/419904436857733121/Yafuza.png")
    embed.set_footer(text="bot sponsored by the wit", icon_url="https://cdn.discordapp.com/emojis/422692563682852865.png")
    embed.timestamp = datetime.datetime.utcnow()
    embed.add_field(name="😎", value=event['description'])
    embed.add_field(name="😎", value="try exceeding some of them!")
    embed.add_field(name="😎", value="an informative error should show up, and this view will remain as-is until all issues are fixed")
    await bot.send_message(bot.get_channel(channelID), content = '@everyone',embed=embed)
    print(time.time())

async def reQueue(channelID):
    """credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    calenderService = discovery.build('calendar', 'v3', http=http)"""

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print(now)
    tomorrow = datetime.datetime.today().replace(hour= 0,minute=0,second=1,microsecond=0) + datetime.timedelta(days = 1)
    today = datetime.datetime.today().replace(hour= 0,minute=0,second=1,microsecond=0)
    await bot.send_message(bot.get_channel(channelID), 'Queueing the events for today')
    eventsResult = calenderService.events().list(
        calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', timeMin=rfc3339.rfc3339(today) , singleEvents=True, timeMax=rfc3339.rfc3339(tomorrow),
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])
    
    if not events:
        print('No upcoming events found.')            
    for event in events:
        start = iso8601.parse_date(event['start'].get('dateTime', event['start'].get('date')))
        #start = start.replace(tzinfo=datetime.timezone.utc)
        eventid = event['iCalUID']
        print(start)
        print(start.tzname())
        print(eventid)
        scheduler.add_job(scheduled_event_coro, trigger='date', run_date=start, id=eventid, replace_existing=True, args=(channelID, event))
        scheduler.add_job(event_reminder, trigger='date', run_date=start - datetime.timedelta(minutes=30), id=eventid + "_reminder", replace_existing=True, args=(channelID, event))
    scheduler.print_jobs()

@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    scheduler.start()
    scheduler.print_jobs()

@bot.command(pass_context=True)
async def test(ctx):
    counter = 0
    tmp = await bot.say('Calculating messages...')
    async for log in bot.logs_from(ctx.message.channel, limit=100):
        if log.author == ctx.message.author:
            counter += 1
    await bot.edit_message(tmp, 'You have {} messages.'.format(counter))

@bot.command()
async def sleep():
    await asyncio.sleep(5)
    await bot.say('Done sleeping')
@bot.command()
async def booze():
    await bot.say(':beer:')
@bot.command()
async def sudoku():
    await bot.say('Sudoku has been commited.')
    
@bot.command()
async def react():
    msg = await bot.say('React with thumbs up or thumbs down.')    
    await bot.add_reaction(msg, "👍🏻")
    await bot.add_reaction(msg, "👎🏻")
    await asyncio.sleep(0.1)
    def check(reaction, user):
        e = str(reaction.emoji)
        return e.startswith(('👍🏻', '👎🏻'))
    res = await bot.wait_for_reaction(message=msg, check=check)
    await bot.say('{0.user} reacted with {0.reaction.emoji}!'.format(res))
    
    
    
@bot.group(pass_context=True)
async def events(ctx):
    if ctx.invoked_subcommand is None:
        await bot.say('Invalid events command passed...')
@events.command()
async def upcoming():
    """Shows the next 10 events
    """
    """ credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    calenderService = discovery.build('calendar', 'v3', http=http)"""
    
    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    await bot.say('Getting the upcoming 10 events')
    eventsResult = calenderService.events().list(
        calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        await bot.say('No upcoming events found.')            
    for event in events:
        print(event)
        start = event['start'].get('dateTime', event['start'].get('date'))
        await bot.say('```' +  start + '\t' + event['summary'] + '```')
@events.command(pass_context=True)   
async def queue(ctx):
    """queues the events for the day and starts the auto queue"""
    channelID = discord.utils.get(ctx.message.server.channels, name='announcements').id
    print(channelID)
    scheduler.add_job(reQueue, trigger='cron', hour= '1', id='dailyReque' + channelID, replace_existing=True, args={channelID})
    await reQueue(channelID)
@events.command(pass_context=True)  
async def new(ctx):
    """
        Creates a new event and uploads it to the calendar.        
    """
    message = await bot.say("Please enter a name for the event.")
    msg = await bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel)
    print(msg.content)
    eventName = msg.content    
    await bot.edit_message(message, "Please enter a date and start time for the event. \r (Formate: dd.mm.yy hh:mm)")
    msg = await bot.wait_for_message(author=ctx.message.author, channel=ctx.message.channel)
    eventStart = datetime.datetime.strptime(msg.content, '%d.%m.%y %H:%M')
    eventStart.replace(tzinfo=datetime.timezone.utc)
    print(eventStart.tzname())
    eventEnd = eventStart + datetime.timedelta(hours = 1)
    event = calenderService.events().insert(calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', body = {'summary': eventName, 'status': 'confirmed', 'start': {'dateTime': rfc3339.format(eventStart) }, 'end': {'dateTime': rfc3339.format(eventEnd)}}).execute()
    print(event)
    channelID = discord.utils.get(ctx.message.server.channels, name='announcements').id
    print(channelID)
    await reQueue(channelID)
    
    
    
"""@bot.event
async def on_message(message):
    print(message.author.id)
    if (message.author.name == "Zatsu"):
        await bot.add_reaction(message, "🤦🏻")
    await bot.process_commands(message)"""
    
@bot.event
async def on_reaction_add(reaction, user):
    if(user!=bot.user):
        print(reaction.emoji)        
        

#@bot.event()
#async def on_error():
#   print(sys.exc_info())

@bot.event
async def on_resumed():
    print('reconnected')

f = open('botsecret.txt')
botsecret = f.read()
f.close()
print("wololo")
while 1:
    try:
        bot.run(botsecret)
    except OSError as err:
        print("OS error: {0}".format(err))
    except discord.errors.ConnectionClosed:
        print("Connection closed, trying again in a bit")
        sleep(120)
