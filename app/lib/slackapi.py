import logging
import time
import slack as SlackClient
from django.conf import settings

# set up logging namespace
logger = logging.getLogger(__name__)

# instantiate Slack client
slack_client = SlackClient.WebClient(settings.SLACK_API_TOKEN)
# TODO: Migrate to "New Slack Apps" where bot users have better scope support
slack_admin = SlackClient.WebClient(settings.SLACK_API_SECRET)
bot_name = "nycmeshbot"
# bot_id = get_bot_id()

# if bot_id is None:
#     exit("Error, could not find " + bot_name)


def get_bot_id():
    """ Gets the User ID of the Bot User
    Returns
    =======
    botuserid : str
        Bot User ID from Slack
    """
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        logger.debug("api call is ok")
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == bot_name:
                botuserid = "<@" + user.get('id') + ">"
                logging.debug(f"Bot User ID: {botuserid}")
                return botuserid

        return None


def get_channel_id(channel_name):
    """ Gets the Channel ID
    Parameters
    ==========
    channel_name : str
        Human readable channel name (ie. "general")

    Returns
    =======
    channelID : str
        Channel ID from Slack
    """
    channels_call = slack_client.conversations_list(exclude_archived="true", types='public_channel')
    channelID = channel_name
    if channels_call['ok']:
        logger.debug(f"api call is ok.")
        for channel in channels_call['channels']:
            if channel['name'] == channel_name:
                logger.debug(f"{channel}")
                channelID = channel['id']
    if channel_name == channelID:
        channels_call = slack_client.conversations_list(exclude_archived="true", types='private_channel')
        channelID = channel_name
        if channels_call['ok']:
            logger.debug(f"api call is ok.")
            for channel in channels_call['channels']:
                if channel['name'] == channel_name:
                    logger.debug(f"{channel}")
                    channelID = channel['id']
    return channelID


def listen():
    """ Starts Slack RTM socket
    """
    if slack_client.rtm_connect(with_team_state=False):
        logger.info("Successfully connected to Slack RTM, listening for commands")
        while True:
            time.sleep(1)
    else:
        logger.exception("Error, connection to Slack RTM failed.")
        exit("Error, Connection Failed")


def post_to_channel(text, channel, attachments=None, blocks=None):
    """ Post Message to Slack channel
    Parameters
    ==========
    text : str
        Formatted Text block to send to the channel
    channel : str
        Human readable channel name (ie. "general")
    attachments : dict
        Dictionary of message attachments to send with the message

    Returns
    =======
    dict
        Slack API Call Response
    """
    return slack_admin.chat_postMessage(channel=get_channel_id(channel), text=text, as_user=False, blocks=blocks)


def pin_to_channel(channel, ts):
    """ Pin Message to Slack channel
    Parameters
    ==========
    channel : str
        Human readable channel name (ie. "general")
    ts : str
        Timestamp of Slack message

    Returns
    =======
    dict
        Slack API Call Response
    """
    return slack_client.pins_add(channel=get_channel_id(channel), timestamp=ts)


def delete_pin(channel, ts):
    """ Delete Pin from Slack channel
    Parameters
    ==========
    channel : str
        Human readable channel name (ie. "general")
    ts : str
        Timestamp of Slack message

    Returns
    =======
    dict
        Slack API Call Response
    """
    return slack_client.pins_remove(channel=get_channel_id(channel), timestamp=ts)


def delete_message(channel, ts):
    """ Delete Message from Slack channel
    Parameters
    ==========
    channel : str
        Human readable channel name (ie. "general")
    ts : str
        Timestamp of Slack message

    Returns
    =======
    dict
        Slack API Call Response
    """
    return slack_client.api_call("chat.delete", channel=get_channel_id(channel), timestamp=ts)


def get_pinned_messages(channel):
    """ Get all Pinned Messages in Slack channel
    Parameters
    ==========
    channel : str
        Human readable channel name (ie. "general")

    Returns
    =======
    dict
        Slack API Call Response
    """
    return slack_admin.pins_list(channel=get_channel_id(channel))


def edit_message(text, channel, ts, blocks):
    """ Edit Message in Slack channel
    Parameters
    ==========
    text : str
        Formatted Text block to send to the channel
    channel : str
        Human readable channel name (ie. "general")
    ts : str
        Timestamp of Slack message

    Returns
    =======
    dict
        Slack API Call Response
    """
    return slack_admin.chat_update(channel=get_channel_id(channel), text=text, ts=ts, as_user=False, blocks=blocks)


def open_modal(trigger_id, view):
    """ Edit Message in Slack channel
    Parameters
    ==========
    trigger_id : str
        Trigger ID of an interactive component
    view : dict
        Dictionary of the modal view to create

    Returns
    =======
    dict
        Slack API Call Response
    """
    return slack_client.views_open(trigger_id=trigger_id, view=view)
