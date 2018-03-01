from __future__ import print_function
import httplib2
import os

from apiclient import discovery
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore


import datetime
import discord
import asyncio
import time
from discord.ext import commands

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

jobstores = {
    'default': SQLAlchemyJobStore(url='postgresql://postgres:loghorizon@localhost:5432/jobs')
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
    bot.loop.create_task(scheduled_event_coro(message, event))    
    print(time.time())



async def scheduled_event_coro(message, event):
    start = event['start'].get('dateTime', event['start'].get('date'))
    embed = discord.Embed(title="`NEW EVENT STARTING!`", colour=discord.Colour(0x4a078b), url="https://discordapp.com", description="The event " +event['summary'] + " is starting.")
    
    embed.set_image(url="https://cdn.discordapp.com/attachments/413026441429778432/418760731362590721/ffxiv_06012018_005010.png")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/413026441429778432/418760731362590721/ffxiv_06012018_005010.png")
    embed.set_footer(text="footer text", icon_url="https://cdn.discordapp.com/embed/avatars/0.png")
    embed.timestamp = datetime.datetime.utcnow()
    embed.add_field(name="🤔", value=event['summary'])
    embed.add_field(name="😱", value="try exceeding some of them!")
    embed.add_field(name="🙄", value="an informative error should show up, and this view will remain as-is until all issues are fixed")
    embed.add_field(name="<:thonkang:219069250692841473>", value="these last two", inline=True)
    embed.add_field(name="<:thonkang:219069250692841473>", value="are inline fields", inline=True)

    await bot.send_message(message.channel.server.get_channel("413026872138399745"), content = '@everyone',embed=embed)
    print(time.time())

async def reQueue(message):
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    print(now)
    tomorrow = datetime.datetime.today().replace(hour= 0,minute=0,second=1,microsecond=0) + datetime.timedelta(days = 1)
    today = datetime.datetime.today().replace(hour= 0,minute=0,second=1,microsecond=0)
    await bot.send_message(message.channel, 'Queueing the events for today')
    eventsResult = service.events().list(
        calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', timeMin=today.isoformat() + 'Z' , singleEvents=True, timeMax=tomorrow.isoformat() + 'Z',
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        print('No upcoming events found.')            
    for event in events:
        start = datetime.datetime.strptime(event['start'].get('dateTime', event['start'].get('date')) + 'UTC', "%Y-%m-%dT%H:%M:%SZ%Z")
        start = start.replace(tzinfo=datetime.timezone.utc)
        eventid = event['iCalUID']
        print(start)
        print(start.tzname())
        print(eventid)
        scheduler.add_job(scheduled_event, trigger='date', run_date=start, id=eventid, replace_existing=True, args=(message, event))
    scheduler.add_job(reQueue, trigger='date', run_date=tomorrow, id='dailyreque', replace_existing=True, args={message})
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
    def check(reaction, user):
        e = str(reaction.emoji)
        return e.startswith(('👍', '👎'))

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
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('calendar', 'v3', http=http)

    now = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
    await bot.say('Getting the upcoming 10 events')
    eventsResult = service.events().list(
        calendarId='ie1n8t75hiper1779ogvaetr9o@group.calendar.google.com', timeMin=now, maxResults=10, singleEvents=True,
        orderBy='startTime').execute()
    events = eventsResult.get('items', [])

    if not events:
        await bot.say('No upcoming events found.')            
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        await bot.say('```' +  start + '\t' + event['summary'] + '```')
@events.command(pass_context=True)   
async def queue(ctx):
    """queues the events for the day and starts the auto queue"""
    await reQueue(ctx.message)

f = open('botsecret.txt')
bot.run(f.read())
f.close()