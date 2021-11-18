import logging
import threading
from discord import client
from gpiozero import PWMLED
from time import sleep
import discord
import statusLED
import gpiozero
import json
import asyncio



class ButtonBot(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')
    async def on_message(self,message: discord.message):
        if message.author.id != self.user.id:
            await message.reply("hello!", mention_author=True)
        return 

    async def onButtonPressed(self):
        print("Bot has triggered button-press!")
        sleep(10)
        print("Button press finished")
        return 

    async def _onButtonPressed():
        return 
def GPIOActions(bot: ButtonBot):
    led = statusLED.statusLight(18)
    button = gpiozero.DigitalInputDevice(4)
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
            asyncio.run(bot.onButtonPressed())

        oldState = button.is_active
        sleep(.025) 



if __name__ == "__main__":
    bot = ButtonBot()
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
    
    

