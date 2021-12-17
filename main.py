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
    bot.run(token)
    
    

