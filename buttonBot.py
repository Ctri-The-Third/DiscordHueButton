import discord
import logging
import gpiozero
import asyncio
import re
import datetime
import math
import json
import requests


from configHelper import configHelper, buttonProgress, buttonCfg
from statusLED import buttonWithLED
LOGOUTPUT = "log"

class ButtonBot(discord.Client):
    def __init__(self, *, loop=None, **options):
        super().__init__(loop=loop, **options)
        logging.basicConfig(filename=LOGOUTPUT, filemode="a+")
        self.config = configHelper()
        
        self.buttons = [] 
        for button in self.config.buttons:
            newButton = buttonWithLED(button.LEDOutPin,button.btnInPin,button.btnReactEmoji, button.hueShade)
            newButton.connectingFlash(.5)
            self.buttons.append(newButton)

        
        self.matchingRegex = re.compile(r"""(It had been [0-9]* days*, [0-9]* hours*, and [0-9]* minutes* since the button was pressed.)""")
        self.registerMessageRegex = re.compile(r"""!btn register""")
        self.pingMessageRegex = re.compile(r"""!btn ping""")
        self.unregisterMessageRegex = re.compile(r"""!btn unregister""")
        self.statsRequestMessageRegex = re.compile(r"""!btn(?: statu?s)?""") #!btn stats or !btn
        self.helpMessageRegex = re.compile(r"""!btn help""")
    


    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!btn help"))

        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
        for button in self.buttons:
            button.onShortPress = self.onButtonPressShort
            button.onLongPress = self.onButtonPressLong
            button.pulse(0.01)
        
        if len(self.config.openMessages) >= 1:
            for button in self.buttons:
                button.setPulseSpeed(0.04) 

        foundUser = self.get_user(self.config.users[0])
        if self.config.error != "":
            await self.messagePersonOfInterest("Something went wrong during startup, here's the error: \n%s" % (self.config.error), foundUser)
        
        if len(self.config.buttons) > 0:
            message = "Button startup complete here's your save progress:\n"
            for button_id in self.config._pressProgress:
                message += "\nPIN_ID {} pressed {} times, last pressed {}" .format(
                    button_id,
                    self.config._pressProgress[button_id].timesPressed,
                    self.config._pressProgress[button_id].lastPressed.strftime(r"%Y-%m-%d %H:%M:%S")
                )
            await self.messagePersonOfInterest(message,foundUser)

        
    async def on_message(self,message: discord.message):
        await self._checkForMentions(message)
        #await self._checkForButtonMessages(message)
        await self._checkForRegisterMessage(message)
        await self._checkForUnregisterMessage(message)
        await self._checkForStatsRequestMessage(message)  
        await self._checkForHelpMessage(message)  
        await self._checkForPingMessage(message)


    async def _checkForPingMessage(self,message:discord.message) -> None:
        if self.pingMessageRegex.match(message.clean_content):
            members = self.get_all_members()
            for member in members:
                outStr = "{}\t{}#{}".format(member.id,member.display_name,member.discriminator)
                print(outStr)
        pass


    async def _checkForHelpMessage(self,message:discord.message) -> None:
        if self.helpMessageRegex.match(message.clean_content):
            await message.reply("""Well hey there! I'm a bot attached to a big button that belongs to {}. I'm a bit like a pager. If I see you mentioning them, I'll make that button flash until they press it! 
Each time they press it, I keep track. Curious? Check in with !btn stats. I used to announce button presses regularly, but it was noisey so I stopped. Have a smiley day!""")
        pass 

    async def _checkForStatsRequestMessage(self, message:discord.message):
        if self.statsRequestMessageRegex.match(message.clean_content):
            messageText = ""
            for button in self.config.buttons:
                
                progress = self.config.getProgress(button.btnInPin)

                timeSince = (datetime.datetime.now() - progress.lastPressed )
                timeSinceDays = timeSince.days
                timeSinceHours = math.floor(timeSince.seconds / 60 /60) % 60
                timeSinceMinutes = math.floor(timeSince.seconds / 60) % 60
                despairMessage = self.config.getDespairMessage()
                emoji = "" if  button.btnReactEmoji == None or button.btnReactEmoji == "" else "{} ".format(button.btnReactEmoji)
                messageText += "**The {emoji}Button:** was last pressed at {7}\nIt has now been pressed {0} times\nIt had been {1} day{2}, {3} hour{4}, and {5} minute{6} since it was pressed.\n\n".format(
                    progress.timesPressed,
                    timeSinceDays,
                    "s" if timeSinceDays != 1 else "",
                    timeSinceHours,
                    "s" if timeSinceHours != 1 else "",
                    timeSinceMinutes,
                    "s" if timeSinceMinutes != 1 else "",
                    progress.lastPressed.strftime(r"%d-%b %H:%M"),
                    emoji = emoji
                )
            messageText += "\n> {}".format(despairMessage)
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
                for button in self.buttons:
                    button.setPulseSpeed(0.04)
                await self.notifyPersonOfInterest(message,foundUser)
                authorNick = "" if message.author.nick is None else message.author.nick
                desc = """Hey there {3}

Looks like {0} ({1}#{2}) is trying to get your attention.
The mention originated on **{4}** in the server **{5}**. Here's a [direct link]({6})

---------------------
Message content copied below for you:

{7}""".format( message.author.nick, message.author.name,message.author.discriminator,
                foundUser.name,
                self._tryGetChannelName(message),
                self._tryGetGuildName(message),
                message.jump_url,
                message.clean_content)

                self.maybeNotifyWebhook(title = "Discord alert - {0} ({1}#{2}) ".format(message.author.nick,message.author.name,message.author.discriminator),
                desc=desc,
                author="TheButton:{}#{}".format(message.author.name,message.author.discriminator))
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

    async def messagePersonOfInterest(self,message,foundUser=None):
        if foundUser == None:
            foundUser = self.get_user(self.config.users[0])
        await foundUser.send(message)

    def onButtonPressShort(self,button:buttonWithLED):
        if not self.is_ready():
            return
        print("Short press! {}".format(button.notificationEmoji))
        button.flash(rate=0.2)
        asyncio.run_coroutine_threadsafe(self.onButtonPressed(button.identifier,additionalReaction=button.notificationEmoji,overideShade=button.notificationShade),self.loop)
        
        
    def onButtonPressLong(self,button:buttonWithLED):
        if not self.is_ready():
            return  
        print("long press! {}".format(button.notificationEmoji))
        button.flash(rate=0.1)
        asyncio.run_coroutine_threadsafe(self.onButtonPressed(button.identifier,additionalReaction=button.notificationEmoji,overideShade=button.notificationShade),self.loop)
        
    async def _checkForButtonMessages(self, message:discord.message) -> None:
        logging.warning("Using depreciated method _checkForButtonMessages - shouldn't be necessary anymore.")
        if message.author.id == self.user.id:
            #check if it's one of our messages, if so register its' ID for updates.
            result = self.matchingRegex.search(message.clean_content)
            if result is not None: 
                self.config.messages[message.channel.id] = message.id
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
                    

    async def onButtonPressed(self,buttonID,additionalReaction = "",overideShade = None):

        
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
                    if additionalReaction != "":
                        try:
                            await msg.add_reaction(additionalReaction)
                        except Exception as e:
                            logging.warning("Custom button emojoi couldn't be added to message")

                except Exception as e:
                    logging.warning("Couldn't add / remove a reaction to close out a paging message %s", e)
            self.config.unregisterOpenMessage(messageIDs["message"],messageIDs["channel"])

        self.config.incrementPresses(buttonID)
        self.config.updateLastPressed(buttonID, datetime.datetime.now())
        self.config.saveProgress()
        self.maybeNotifyWebhook(overideShade=overideShade)

    def maybeNotifyWebhook(self,title=None,desc=None,author=None,overideShade=None):
        if self.config.notificationEnabled:
            sendMessage = True if title is not None and desc is not None and author is not None else False
            url = self.config.notificationEndpoint % (sendMessage)
            headers = {"Authorization":"Basic {}".format(self.config.notificationAuthtoken)}
            body = json.dumps({"title":title,"description":desc,"author":author})
            params = {}
            if overideShade is not None:
                params["shade"] = overideShade
            try:
                
                requests.post(url=url,headers=headers,data=body,params=params)
            except Exception as e:
                logging.warning("Tried and failed to hit the notification endpoint- %s",e)
                print("Tried and failed to hit the notification endpoint - %s",e)
        return 


    async def _tryUpdateMessage(self,messageText,channelDeets):
        channel = self.get_channel(channelDeets)
        if channel == None:
            channel = await self.fetch_channel(channelDeets)
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
