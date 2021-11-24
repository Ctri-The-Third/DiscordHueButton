import logging
import datetime
import json 
import os 
import random

class configHelper():
    def __init__(self) -> None:
        self.logger = logging.getLogger("configHelper")
        
        self.openMessages = []
        self.channels = [] #the ID is the key, the object is the 
        keys = {} 

        try: 
            with open("save.json","r") as f :
                keys = json.load(f)
        except Exception as e:
            self.logger.error("Failed to load save: %s", e)
        self.presses = 0 if "timesPressed" not in keys else keys["timesPressed"]
        self.lastPressed = datetime.datetime(1990,1,1,0,0)
        try: 
            self.lastPressed = datetime.datetime.strptime(keys["lastPressed"],r"%Y-%m-%d %H:%M:%S")
        except Exception as e:
            self.logger.error("Couldn't properly parse 'last pressed' %s",e)

        self.openMessages = [] if "openMessages" not in keys else keys["openMessages"]

                
                
                


        try: 
            with open("config.json","r") as f :
                keys = json.load(f)

        except Exception as e:
            self.logger.error("Failed to load config: %s", e)


        
            
        self.channels = [] if "announcementChannels" not in keys else keys["announcementChannels"]

        self.users = []
        if "usersToWatchFor" in keys:
            for userID in keys["usersToWatchFor"]:
                if isinstance(userID,int):
                    self.users.append(userID)
        self.despairMessages = [] if "despairMessages" not in keys else keys["despairMessages"]


    def getDespairMessage(self) -> str:
        if len(self.despairMessages) == 0:
            return ""

        selection = random.randint(0,len(self.despairMessages)-1)
        return self.despairMessages[selection]

    def registerOpenMessage(self,messageID,channelID):
        self.openMessages.append({"message":messageID,"channel":channelID})
        self.saveProgress()

    def unregisterOpenMessage(self,messageID,channelID):
        self.openMessages.remove({"message":messageID,"channel":channelID})
        self.saveProgress()
    def registerChannel(self, channelID):
        if channelID not in self.channels:
            self.channels.append(channelID)
            self.saveConfig()

    def unregisterChannel(self, channelID):
        if channelID in self.channels:
            self.channels.remove(channelID)
            self.saveConfig()

    def incrementPresses(self ):
        self.presses += 1 
        
        pass 

    def updateLastPressed(self, timestamp = datetime.datetime.now()):
        self.lastPressed = timestamp
        
        pass

    def isUserWatched(self,userID):
        if userID in self.users:
            return True
        return False

    

    
    def saveProgress(self):
        outObj = {}
        f =  open("save.json.new","w") 
        outObj["timesPressed"] = self.presses
        outObj["lastPressed"] = datetime.datetime.strftime(self.lastPressed, r"%Y-%m-%d %H:%M:%S")
        outObj["openMessages"] = self.openMessages
        try:
            outStr = json.dumps(outObj, indent=2)
            f.write(outStr)
            f.close()
        except Exception as e:
            self.logger.error("Couldn't translate savestate to JSON! %s",e)

        try:
            os.remove("save.json.old")
        except Exception as e :
            self.logger.warning("Couldn't delete old json save: %s",e)
        
        try:
            os.rename("save.json","save.json.old")
        except Exception as e :
            self.logger.warning("Couldn't backup stale save: %s",e)

        try:
            os.rename("save.json.new","save.json")
        except Exception as e :
            self.logger.warning("Couldn't make the temp save permanent: %s",e)

    def saveConfig(self):
        
        with open("config.json.new","w+") as f:
            outObj = {}
            outObj["usersToWatchFor"] = self.users

            
            
            outObj["despairMessages"] = self.despairMessages
            
            try:
                outStr = json.dumps(outObj, indent=2)
            except Exception as e:
                self.logger.error("Couldn't translate config & savestate to JSON! %s",e)
            f.write(outStr)
        try:
            os.remove("config.json.old")
        except Exception as e :
            self.logger.warning("Couldn't delete old json save: %s",e)
        
        try:
            os.rename("config.json","config.json.old")
        except Exception as e :
            self.logger.warning("Couldn't backup stale save: %s",e)

        try:
            os.rename("config.json.new","config.json")
        except Exception as e :
            self.logger.warning("Couldn't make the temp save permanent: %s",e)
        
        
        
        
