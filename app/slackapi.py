import time
from slackclient import SlackClient
 
# instantiate Slack client
#SLACK_API_TOKEN = appconfig['SLACK_API_TOKEN']
#slack_client = SlackClient(SLACK_API_TOKEN)
slack_client = SlackClient("xoxb-2725312681-484840581858-WLfKLXyN3nXkR8v1Xwcj360i")
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
    channels_call = slack_client.api_call("channels.list")
    if channels_call['ok']:
        for channel in channels_call['channels']:
            if channel['name'] == channel_name:
                return channel['id']
    
    return None
    
def listen():
    if slack_client.rtm_connect(with_team_state=False):
        print "Successfully connected, listening for commands"
        while True:
            #slf.event.wait_for_event()
            api.run()
            time.sleep(1)
    else:
        exit("Error, Connection Failed")

def post_to_channel(text, channel, attachments=None):
    return slack_client.api_call("chat.postMessage", channel=channel, text=text, as_user=True)

def pin_to_channel(channel, ts):
    return slack_client.api_call("pins.add", channel=channel, timestamp=ts)

