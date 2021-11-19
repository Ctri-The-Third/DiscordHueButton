import logging
import threading
from discord import channel, client
from gpiozero import PWMLED
from time import sleep
import discord
import gpiozero
import json
import asyncio
import math 
import statusLED
import re

from configHelper import *

class ButtonBot(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        self.config = configHelper()
        self.buttonLED = statusLED.statusLight(18)
        self.button = gpiozero.DigitalInputDevice(4)
        self.messages = {} #key is channel ID, value is message ID 
        self.matchingRegex = re.compile(r"""(It had been [0-9]* days*, [0-9]* hours*, and [0-9]* minutes* since the button was pressed.)""")
        self.registerMessageRegex = re.compile(r"""!btn register""")
        self.unregisterMessageRegex = re.compile(r"""!btn unregister""")
    
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        
        for intent in self.intents:
            print(intent)

    async def on_message(self,message: discord.message):
        await self._checkForMentions(message)
        await self._checkForButtonMessages(message)
        await self._checkForRegisterMessage(message)
        await self._checkForUnregisterMessage(message)        

    async def _checkForMentions(self, message:discord.message) -> None:
        memberName = ""
        if message.author.id != self.user.id:
            found = False
            if message.reference is not None:
                try: 
                    message.mentions.pop(0)
                except Exception as e:
                    pass
            for user in message.mentions: 
                if self.config.isUserWatched(user.id)  or user.id == self.user.id:
                    found = True
                    memberName = user.name
        
            for role in message.role_mentions:
                for member in role.members:
                    if self.config.isUserWatched(member.id):
                        found = True
                        memberName = member.name

            if found: 
                try:
                    await message.reply("Looking for {}? The beacon has been lit. :+1:".format(memberName))
                except Exception as e:
                    await message.channel.send("Looking for {}? The beacon has been lit. :+1:".format(memberName))

                self.buttonLED.setPulseSpeed(0.04)
            return 
    async def _checkForButtonMessages(self, message:discord.message) -> None:
        if message.author.id == self.user.id:
            #check if it's one of our messages, if so register its' ID for updates.
            result = self.matchingRegex.search(message.clean_content)
            if result is not None: 
                bot.messages[message.channel.id] = message.id
            return

    async def _checkForRegisterMessage(self,message:discord.message):
        if  self.config.isUserWatched(message.author.id):
            if self.registerMessageRegex.match(message.clean_content):
                self.config.registerChannel(message.channel.id)
                try: 
                    await message.reply("Got it, will update this channel with presses! :slight_smile:")                
                except Exception as e:
                    logging.warning("Couldn't reply to a message - possibly missing the read_message_history permission? _checkForRegisterMessage")
                    await message.channel.send("Got it, will update this channel with presses! :slight_smile:")
    async def _checkForUnregisterMessage(self,message:discord.message):
        if  self.config.isUserWatched(message.author.id):
            if self.unregisterMessageRegex.match(message.clean_content):
                self.config.unregisterChannel(message.channel.id)
                try:
                    await message.reply("Okay, won't update this channel with presses! :+1:")

                except Exception as e:
                    logging.warning("Couldn't reply to a message - possibly missing the read_message_history permission? _checkForRegisterMessage")
                    await message.channel.send("Okay, won't update this channel with presses! :+1:")

    async def onButtonPressed(self):

        #spam check - if it's been <180 seconds 
        
        timeSince = (datetime.datetime.now() - self.config.lastPressed )
        timeSinceDays = timeSince.days
        timeSinceHours = math.floor(timeSince.seconds / 60 /60)
        timeSinceMinutes = math.floor(timeSince.seconds / 60)

        for channelTargetID in self.config.channels:
            target = self.get_channel(channelTargetID)
            if isinstance(target,discord.TextChannel):
                despairMessage = self.config.getDespairMessage()
                messageText = "**C'tri pressed The Button** at {8}\nIt has now been pressed {0} times\nIt had been {1} day{2}, {3} hour{4}, and {5} minute{6} since the button was pressed.\n\n> {7}".format(
                    self.config.presses+1,
                    timeSinceDays,
                    "s" if timeSinceDays != 1 else "",
                    timeSinceHours,
                    "s" if timeSinceHours != 1 else "",
                    timeSinceMinutes,
                    "s" if timeSinceMinutes != 1 else "",
                    despairMessage,
                    datetime.datetime.now().strftime(r"%d-%b %H:%M")
                )
                targetMessageID = 0 if channelTargetID not in self.messages else self.messages[channelTargetID]
                if timeSinceHours <= 1 or targetMessageID == target.last_message_id:
                #if targetMessageID == target.last_message_id:
                    await self._tryUpdateMessage(messageText,channelTargetID)
                else:
                    await self._sendMessageToChannel(messageText,target)
                    

        self.config.incrementPresses()
        self.config.updateLastPressed(datetime.datetime.now())
        self.config.saveProgress()
    
        return 

    async def _tryUpdateMessage(self,messageText,channelDeets):
        channel = bot.get_channel(channelDeets)
        if channel == None:
            channel = await bot.fetch_channel(channelDeets)
            await self._sendMessageToChannel(messageText,channel)
            return 
        if not channel.id in self.messages:
            await self._sendMessageToChannel(messageText,channel)
            return

        try: 
            resultMessage  = await channel.fetch_message(self.messages[channel.id])
            if resultMessage.created_at >= self.config.lastPressed - datetime.timedelta(hours=1):
                await resultMessage.edit(content=messageText)
            else: 
                await self._sendMessageToChannel(messageText,channel)
            return 
        except Exception as e:

            logging.warning("couldn't retrieve an old message to update: %s" % e)
            await self._sendMessageToChannel(messageText,channel)
            return 

    
    async def _sendMessageToChannel(self,messageText:str,channel:discord.channel):
        await channel.send(messageText)
        
    def defaultIntents() -> str:
            intents = discord.Intents.default()
            intents.members = True 



def GPIOActions(bot: ButtonBot):
    
    led = bot.buttonLED
    button = bot.button


    oldState = button.is_active
    firstFoundTimeRemaining = 300

    while firstFoundTimeRemaining > 0:
        sleep(1)
        if bot.is_ready():
            firstFoundTimeRemaining = 0
    
    
    print ("Active")
    while bot.is_ready():    
        if button.is_active:
            
            led.flash(rate=0.2)  
        if button.is_active and button.is_active != oldState:
            asyncio.run_coroutine_threadsafe(bot.onButtonPressed(),bot.loop)

        oldState = button.is_active
        sleep(.025) 




if __name__ == "__main__":
    intents = discord.Intents(
        messages=True, #need to read messages 
        emojis=True, 
        guild_messages=True, #need to read messages?
        members=True,  #need to get roles
        #presences=True,
        guilds=True #need to get roles
        )
    bot = ButtonBot(intents = intents)
    token = ""
    try: 
        keys = json.load(open("auth.json"))
        token = keys["token"]      
        
    except:
        logging.error("Bot execution failed, defaulting to bot-less mode")
    buttonThread = threading.Thread(target=GPIOActions, args=[bot])
    buttonThread.start()
    bot.run(token)
    buttonThread.join()
    
    

