import logging
import threading
from discord import channel, client
from gpiozero import PWMLED
from time import sleep
import discord
import asyncio
import gpiozero
import json
import asyncio
import math 
import statusLED
import re
import requests

from configHelper import *
from buttonBot import *
LOGOUTPUT = "log" 

class GPIOManager():
    def __init__(self,bot: ButtonBot):
        self.bot = bot     
        self.buttons = bot.buttons

    def mainThread(self):
        firstFoundTimeRemaining = 15
        while firstFoundTimeRemaining > 0:
            firstFoundTimeRemaining -= 1
            sleep(1)
            if bot.is_ready():
                firstFoundTimeRemaining = 0
        for button in self.buttons:
            button.onShortPress = self.onButtonPressShort
            button.onLongPress = self.onButtonPressLong
        
        print ("GPIO Active(?)")
        while bot.is_ready():    
            for button in self.buttons:
                if button.is_active:
                    button.flash(rate=0.2)  
                #if button.is_active and button.is_active != button.oldState:
                #    try: 
                #        asyncio.run_coroutine_threadsafe(bot.onButtonPressed(),bot.loop)
                #    except Exception as e:
                #        logging.error("Couldn't do the thing? but the bot is ready? %s", bot.is_ready())

                #oldState = button.is_active
            
        
    def onButtonPressShort(self,button):
        asyncio.run_coroutine_threadsafe(self.bot.onButtonPressed(additionalReaction=button.notificationEmoji,overideShade=button.notificationShade),bot.loop)
        #print("Short press! {}".format(button.notificationEmoji))
    def onButtonPressLong(self,button):
        print("Long press! {}".format(button.notificationEmoji))
        #asyncio.run_coroutine_threadsafe(print("Long press!"))

def startGPIOManager(bot) -> threading.Thread :
    obj = GPIOManager(bot)
    buttonThread = threading.Thread(target=obj.mainThread)
    buttonThread.start()
    return buttonThread

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
    buttonThread = startGPIOManager(bot)
    bot.run(token)
    buttonThread.join()
    
    

