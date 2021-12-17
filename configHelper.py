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
        self.buttons = [] 
        self._pressProgress = {}
        try: 
            with open("save.json","r") as f :
                keys = json.load(f)
        except Exception as e:
            self.logger.error("Failed to load save: %s", e)

        if "buttons" in keys:
            for button in keys.get("buttons"):
                prg = buttonProgress()
                prg.fromDict(button)
                self._pressProgress[prg.buttonID] = prg

        self.openMessages = [] if "openMessages" not in keys else keys["openMessages"]

                
        try: 
            with open("config.json","r") as f :
                keys = json.load(f)

        except Exception as e:
            self.logger.error("Failed to load config: %s", e)


        
            
        self.channels = [] if "announcementChannels" not in keys else keys["announcementChannels"]
        btns = keys.get("buttons")
        for btn in btns:
            newBtn = buttonCfg(btn)
            self.buttons.append(newBtn)
            if newBtn.btnInPin not in self._pressProgress:
                prg = buttonProgress()
                prg.buttonID = newBtn.btnInPin
                self._pressProgress[prg.buttonID] = prg
        self.users = []
        if "usersToWatchFor" in keys:
            for userID in keys["usersToWatchFor"]:
                if isinstance(userID,int):
                    self.users.append(userID)
        self.despairMessages = [] if "despairMessages" not in keys else keys["despairMessages"]
        self.notificationEndpoint = keys.get("notificationEndpointHost")
        self.notificationAuthtoken = keys.get("notificationEndpointHeaderToken")
        self.notificationEnabled = True if self.notificationEndpoint is not None and self.notificationAuthtoken is not None else None
        

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

    def incrementPresses(self, buttonID ):
        prg = self._pressProgress[buttonID]
        prg.timesPressed += 1
        pass 

    def updateLastPressed(self, buttonID, timestamp = datetime.datetime.now()):
        self._pressProgress[buttonID].lastPressed = timestamp
        
        
        pass

    def isUserWatched(self,userID):
        if userID in self.users:
            return True
        return False

    def getProgress(self,buttonID):
        return self._pressProgress[buttonID]

    def saveProgress(self):
        outObj = {}
        f =  open("save.json.new","w") 
        outObj["buttons"] = []
        for key in self._pressProgress:
            button = self._pressProgress[key]
            
            outObj["buttons"].append(button.toDict())
            
        try:
            outObj["openMessages"] = self.openMessages
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
        
        
        
        
class buttonCfg():
    def __init__(self, dict:dict) -> None:
        self.LEDOutPin = int(dict.get("LEDOutPin"))
        self.btnInPin = int(dict.get("btnInPin"))
        self.btnReactEmoji = dict.get("btnReactEmoji")
        self.hueShade = dict.get("hueHue")
        pass

class buttonProgress():
    def __init__(self, buttonID:int = None, timesPressed:int = None, lastPressed:datetime = None) -> None:
        self.buttonID = 0 if buttonID is None else buttonID
        self.timesPressed = 0 if timesPressed is None else timesPressed
        self.lastPressed = datetime.datetime.now() if lastPressed is None else lastPressed
            
    
    def toDict(self) -> dict:
        returnObj = {}
        returnObj["buttonID"] = self.buttonID
        returnObj["timesPressed"] = self.timesPressed
        returnObj["lastPressed"] = self.lastPressed.strftime(r"%Y-%m-%d %H:%M:%S")
        return returnObj

    def fromDict(self, dict:dict):
         
            if "buttonID" in dict and isinstance(dict["buttonID"],int):
                self.buttonID = dict["buttonID"]
            
            if "timesPressed" in dict and isinstance(dict["timesPressed"],int):
                self.timesPressed = dict["timesPressed"]

            if "lastPressed" is not None:
                try: 
                    self.lastPressed = datetime.datetime.strptime(dict["lastPressed"],r"%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    self.logger.error("Couldn't properly parse 'last pressed' %s",e)
            
                
            

