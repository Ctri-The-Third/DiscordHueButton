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

