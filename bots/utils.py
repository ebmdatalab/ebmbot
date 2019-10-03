import contextlib
import io
import logging
import traceback

from fabric.api import settings

from fabric.tasks import execute
from slackbot_settings import FABRIC_ENV

import slackbot
from slackbot.slackclient import SlackClient
from slackbot.dispatcher import Message


class NonExitingError(Exception):
    def __init__(self, original, stderr, stdout):
        self.stderr = stderr
        self.stdout = stdout

    def __str__(self):
        msg = """
---------------------------------
STDERR:

{}

---------------------------------
last lines of STDOUT:

{}

(see ebmbot logs for traceback)"""
        stdout_tail = "\n".join(self.stdout.splitlines()[-200:])
        msg = msg.format(
            self.stderr,
            stdout_tail)
        return msg


def safe_execute(cmd, *args, **kwargs):
    """Execute fabric command, catching and logging SystemExit along with
    stderr, so we have a chance to close threads cleaning with an exit
    message.

    Requires explicit `hosts` value. This is because by convention
    fabfiles set this in a global-and-non-threadsafe module; in turn,
    this means that running more than one fabric operation at a time
    may lead to the commands running on the wrong hosts.

    """

    captured_stderr = io.StringIO()
    captured_stdout = io.StringIO()
    assert 'hosts' in kwargs, "You must supply a `hosts` keyword argument"
    try:
        with contextlib.redirect_stderr(captured_stderr):
            with contextlib.redirect_stdout(captured_stdout):
                with settings(**FABRIC_ENV):
                    result = execute(cmd, *args, **kwargs)
    except BaseException as e:
        # BaseException includes SystemExit, whereas Exception doesn't.
        captured_stderr.seek(0)
        stderr = captured_stderr.read()
        captured_stdout.seek(0)
        stdout = captured_stdout.read()
        if isinstance(e, SystemExit):
            msg = "Fabric aborted with exiting exception %s, %s, %s\n\n%s"
        else:
            msg = "Fabric aborted with exception %s, %s, %s\n\n%s"
        stack = traceback.format_tb(e.__traceback__)
        logging.info(msg, type(e), e, stderr, "".join(stack))
        raise NonExitingError(e, stderr, stdout)

    # execute() returns a dictionary mapping the name of a host to the output
    # of running the command on that host.  At the moment, we expect commands
    # to only ever be run on one host, so we return the output from that host.
    assert len(result) == 1
    return list(result.values())[0]


def send_message_to_channel(message, channel):
    assert channel.startswith('#')
    msg = {'channel': channel, 'ts': None}
    client = SlackClient(slackbot.settings.API_TOKEN)
    Message(client, msg).send_webapi(message)


def reply(message, text, do_log=True):
    '''Send reply to Slack, and log it with the original message id.

    Note that `message` in an instance of `slackbot.dispatcher.Message`.

    If `message.body['ts']` is None then the message was not created by a `respond_to`
    handler, so we cannot reply to it.
    '''
    if do_log:
        logging.info(str(id(message)) + ' ' + text)

    if message.body['ts']:
        message.reply(text)
    else:
        message.send_webapi(text)
