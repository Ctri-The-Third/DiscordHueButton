import logging
from discord import channel, client
from gpiozero import PWMLED
from time import sleep
import discord
import json
import subprocess

from configHelper import *
from buttonBot import *
LOGOUTPUT = "log" 

        
if __name__ == "__main__":
    logging.basicConfig(filename="thebutton.log", level = logging.WARN, format="%(asctime)s:%(levelname)s:%(message)s")
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
    for i in range(0,4):
        #check wifi state, ping google, on success break
        try:
            wifistate =  subprocess.run("iwconfig", capture_output=True)
            result = requests.get(url="http://www.gstatic.com/generate_204")
            if result.status_code == 204:
                break
        except Exception as e:
            logging.warn("Couldn't connect to the internet - %s", e)
        sleep(i*5)
    bot.run(token)
    
    

