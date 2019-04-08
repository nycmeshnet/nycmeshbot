import time
from slackclient import SlackClient
from flask import current_app
 
# instantiate Slack client
#SLACK_API_TOKEN = appconfig['SLACK_API_TOKEN']
#slack_client = SlackClient(SLACK_API_TOKEN)
#slack_client = SlackClient("xoxb-2725312681-484840581858-QAao02pafVBArxGMBkfhvIrR")
slack_client = SlackClient("xoxp-2725312681-282878884706-555503039892-7157277e7cbe09bc2552e82e60d9d42f")
#slack_client = SlackClient(current_app['SLACK_API_TOKEN'])
bot_name = "nycmeshbot"
#bot_id = get_bot_id()
    
#if bot_id is None:
#    exit("Error, could not find " + bot_name)

    
def get_bot_id():
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        print("api call is ok")
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == bot_name:
                return "<@" + user.get('id') + ">"
            
        return None

def get_channel_id(channel_name):
    #channels_call = slack_client.api_call("channels.list", exclude_archived=True, exclude_members=True)
    channels_call = slack_client.api_call("conversations.list", exclude_archived=True, types='public_channel,private_channel')
    channelID = channel_name
    if channels_call['ok']:
        for channel in channels_call['channels']:
            if channel['name'] == channel_name:
                channelID = channel['id']
    
    return channelID
    
def listen():
    if slack_client.rtm_connect(with_team_state=False):
        print("Successfully connected, listening for commands")
        while True:
            #slf.event.wait_for_event()
            api.run()
            time.sleep(1)
    else:
        exit("Error, Connection Failed")

def post_to_channel(text, channel, attachments=None):
    return slack_client.api_call("chat.postMessage", channel=get_channel_id(channel), text=text, as_user=False)

def pin_to_channel(channel, ts):
    return slack_client.api_call("pins.add", channel=get_channel_id(channel), timestamp=ts)

def delete_pin(channel, ts):
    return slack_client.api_call("pins.remove", channel=get_channel_id(channel), timestamp=ts)

def delete_message(channel, ts):
    return slack_client.api_call("chat.delete", channel=get_channel_id(channel), timestamp=ts)

def get_pinned_messages(channel):
    #return get_channel_id(channel)
    return slack_client.api_call("pins.list", channel=get_channel_id(channel))

def edit_message(text, channel, ts):
    return slack_client.api_call("chat.update", channel=get_channel_id(channel), text=text, ts=ts, as_user=True)
