# DiscordHueButton
An application that uses a rasberry pi's gpio pins to make hue bulbs flash red and announce to configured discord channels that a press has occurred.


# Permissions

* Read Messages/view Channels (to find existing messages and update them)
* Send messages
* add reactions (not used yet)
* Read message history (to reply to messages & get channels)

# intents
* **members** - to get roles and memberships, to capture role_mentions as well as just normal mentions
* **messages** - because it passively detects mentions in messages rather than requiring active slash commends
* guilds 
* emojis
* dm_messages 

# Scribbled installation instructions

from inside SSH
1. sudo apt-get install python3-distutils git -y
2. git clone https://github.com/Ctri-The-Third/DiscosudordHueButton.git
3. wget https://bootstrap.pypa.io/get-pip.py
4. sudo apt-get install python3.8 python3.8-venv python3-venv -y
6. sudo python3 get-pip.py
7. sudo python3 -m pip install -r /home/btn/DiscordHueButton/requirements.txt
8. echo "{}" > save.json
9. sudo cp thebutton.service /etc/systemd/system
10. sudo systemctl enable thebutton.service