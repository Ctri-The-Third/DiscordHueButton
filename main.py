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
LOGOUTPUT = "log"

class ButtonBot(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        logging.basicConfig(filename=LOGOUTPUT, filemode="a+")
        self.config = configHelper()
        self.buttonLED = statusLED.statusLight(18)
        self.button = gpiozero.DigitalInputDevice(4)
        
        self.matchingRegex = re.compile(r"""(It had been [0-9]* days*, [0-9]* hours*, and [0-9]* minutes* since the button was pressed.)""")
        self.registerMessageRegex = re.compile(r"""!btn register""")
        self.unregisterMessageRegex = re.compile(r"""!btn unregister""")
        self.statsRequestMessageRegex = re.compile(r"""!btn(?: statu?s)?""") #!btn stats or !btn
        self.helpMessageRegex = re.compile(r"""!btn help""")
    


    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!btn help"))

        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        if len(self.config.openMessages) >= 1:
            self.buttonLED.setPulseSpeed(0.04)

        
    async def on_message(self,message: discord.message):
        await self._checkForMentions(message)
        #await self._checkForButtonMessages(message)
        await self._checkForRegisterMessage(message)
        await self._checkForUnregisterMessage(message)
        await self._checkForStatsRequestMessage(message)  
        await self._checkForHelpMessage(message)  


    async def _checkForHelpMessage(self,message:discord.message) -> None:
        if self.helpMessageRegex.match(message.clean_content):
            await message.reply("""Well hey there! I'm a bot attached to a big button that belongs to {}. I'm a bit like a pager. If I see you mentioning them, I'll make that button flash until they press it! 
Each time they press it, I keep track. Curious? Check in with !btn stats. I used to announce button presses regularly, but it was noisey so I stopped. Have a smiley day!""")
        pass 

    async def _checkForStatsRequestMessage(self, message:discord.message):
        if self.statsRequestMessageRegex.match(message.clean_content):

            timeSince = (datetime.datetime.now() - self.config.lastPressed )
            timeSinceDays = timeSince.days
            timeSinceHours = math.floor(timeSince.seconds / 60 /60) % 60
            timeSinceMinutes = math.floor(timeSince.seconds / 60) % 60
            despairMessage = self.config.getDespairMessage()
            messageText = "**The Button:** was last pressed at {8}\nIt has now been pressed {0} times\nIt had been {1} day{2}, {3} hour{4}, and {5} minute{6} since the button was pressed.\n\n> {7}".format(
                self.config.presses+1,
                timeSinceDays,
                "s" if timeSinceDays != 1 else "",
                timeSinceHours,
                "s" if timeSinceHours != 1 else "",
                timeSinceMinutes,
                "s" if timeSinceMinutes != 1 else "",
                despairMessage,
                self.config.lastPressed.strftime(r"%d-%b %H:%M")
            )
            await message.reply(messageText)


        pass 

    async def _checkForMentions(self, message:discord.message) -> None:
        memberName = ""
        if message.author.id != self.user.id and message.channel.type == discord.ChannelType.text:
            found = False
            foundUser = self.get_user(self.config.users[0])
            if message.reference is not None:
                try: 
                    message.mentions.pop(0)
                except Exception as e:
                    pass
            
            for user in message.mentions: 
                if self.config.isUserWatched(user.id):
                    found = True
                    break
                elif user.id == self.user.id:
                    found = True
                    break 
            if not found: 
                for role in message.role_mentions:
                    for member in role.members:
                        if self.config.isUserWatched(member.id):
                            found = True
                            break

            if found: 
                self.buttonLED.setPulseSpeed(0.04)
                await self.notifyPersonOfInterest(message,foundUser)
    async def notifyPersonOfInterest(self,message, foundUser):
        try:

            tcName = self._tryGetChannelName(message)
            tgName = self._tryGetGuildName(message)
            self.config.registerOpenMessage(message.id,message.channel.id)
            await message.add_reaction("📣")
            #await message.reply("Looking for {}? The beacon has been lit. :+1:".format(memberName))
            
            await foundUser.send("Hey there {}, **{}** on [**{}**]-[**{}**] is looking for you! Here's a direct link =)\n{}".format(
            foundUser.name, message.author.name,
            tgName, tcName,
            message.jump_url
            ))
        except Exception as e:
            logging.error("Something went wrong processing a mention! \t %s", e)


    async def _checkForButtonMessages(self, message:discord.message) -> None:
        logging.warning("Using depreciated method _checkForButtonMessages - shouldn't be necessary anymore.")
        if message.author.id == self.user.id:
            #check if it's one of our messages, if so register its' ID for updates.
            result = self.matchingRegex.search(message.clean_content)
            if result is not None: 
                bot.config.messages[message.channel.id] = message.id
            return
    async def _checkForRegisterMessage(self,message:discord.message):
        if  self.config.isUserWatched(message.author.id):
            if self.registerMessageRegex.match(message.clean_content):
                self.config.registerChannel(message.channel.id)
                try: 
                    await message.reply("Hey! I don't automatically post to channels anymore, far less spam! :+1: \ntry `!btn stats` to manually check the stats, if you want! :slight_smile:")                
                except Exception as e:
                    logging.warning("Couldn't reply to a message - possibly missing the read_message_history permission? _checkForRegisterMessage")  
    async def _checkForUnregisterMessage(self,message:discord.message):
        if  self.config.isUserWatched(message.author.id):
            if self.unregisterMessageRegex.match(message.clean_content):
                self.config.unregisterChannel(message.channel.id)
                try:
                    await message.reply("Hey! I don't automatically post to channels anymore, far less spam! :+1: \ntry `!btn stats` to manually check the stats, if you want! :slight_smile:")                

                except Exception as e:
                    logging.warning("Couldn't reply to a message - possibly missing the read_message_history permission? _checkForUnegisterMessage")
                    

    async def onButtonPressed(self):

        
        for messageIDs in self.config.openMessages:
            msg = None 
            try: 
                messageID = messageIDs["message"]
                channelID = messageIDs["channel"]
                chnl = self.get_channel(channelID)
                msg = await chnl.fetch_message(messageID)
            except Exception as e:
                logging.warning("Failed get an Open Message, %s",messageIDs)
            if msg is not None:
                try: 
                    await msg.add_reaction("✅")
                    await msg.remove_reaction("📣",self.user)
                except Exception as e:
                    logging.warning("Couldn't add / remove a reaction to close out a paging message %s", e)
            self.config.unregisterOpenMessage(messageIDs["message"],messageIDs["channel"])

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
        if not channel.id in self.config.messages:
            await self._sendMessageToChannel(messageText,channel)
            return

        try: 
            resultMessage  = await channel.fetch_message(self.config.messages[channel.id])
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

    def _tryGetGuildName(self,message:discord.message) -> str:
        if message.channel.type == discord.ChannelType.text:
            return message.channel.guild.name
        else:
            return "Not from a guild"
        pass 

    def _tryGetChannelName(self,message:discord.message) -> str:
        if message.channel.type == discord.ChannelType.private:
            return "DM channel"
        else:
            return message.channel.name
        pass 

def GPIOActions(bot: ButtonBot):
    
    led = bot.buttonLED
    button = bot.button


    oldState = button.is_active
    firstFoundTimeRemaining = 15
    while firstFoundTimeRemaining > 0:
        firstFoundTimeRemaining -= 1
        sleep(1)
        if bot.is_ready():
            firstFoundTimeRemaining = 0
    
    
    print ("GPIO Active(?)")
    while bot.is_ready():    
        if button.is_active:
            
            led.flash(rate=0.2)  
        if button.is_active and button.is_active != oldState:
            try: 
                asyncio.run_coroutine_threadsafe(bot.onButtonPressed(),bot.loop)
            except Exception as e:
                logging.error("Couldn't do the thing? but the bot is ready? %s", bot.is_ready())

        oldState = button.is_active
        sleep(.025) 
    
    bot.buttonLED.terminate()



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
    
    

