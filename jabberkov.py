# made by augment/aura/kyle
# @youmusec // https://github.com/its-youmu
# built off of the following: markov-text, sleekxmpp
# configuration of settings can be done in config.ini
# ver 0.0.1

import sleekxmpp
import logging
import getpass
import sys
import ssl
import configparser

from sleekxmpp.componentxmpp import ComponentXMPP
from optparse import OptionParser
from os import path

# force utf8
if sys.version_info < (3, 0):
    from sleekxmpp.util.misc_ops import setdefaultencoding
    setdefaultencoding('utf8')

### init configuration file (config.ini) in same dir ###
config = configparser.ConfigParser()

# added in a few lines for some extensibility on where the config is, if needed
_file_path = path.relpath("config.ini")
config.read(_file_path)

# define the config items as variables

# usage is as follows:
# print "words %s %s words" % (NAME, PASS)
NAME = config.get('Auth', 'name') # also jid
PASS = config.get('Auth', 'pass')
SERV = config.get('Auth', 'serv')
MUCC = config.get('Auth', 'muc')
PORT = config.get('Auth', 'port')
ROOM = config.get('Auth', 'room')
JID0 = NAME + '@' + SERV
JID1 = NAME + '@' + SERV
JIDR = ROOM + '@' + MUCC
NICK = NAME # i'll bother with this later

# bool values when needed (more extensibility for features)
# Config.getboolean(section, option)
# LOGG = Config.getboolean("Features", "logging")
# MRKV = Config.getboolean("Features", "markov")

### main class ###

class JabberCawk(sleekxmpp.ClientXMPP):

# connection
    def __init__(self, jid, password, room, nick):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)

        self.room = JIDR
        self.nick = NICK

        self.add_event_handler("session_start", self.start)
        self.add_event_handler("groupchat_message", self.muc_message)
        self.add_event_handler("muc::%s::got_online" % self.room,
                               self.muc_online)

# starting
    def start(self, event):
        self.get_roster()
        self.send_presence()
        self.plugin['xep_0045'].joinMUC(self.room,
                                        self.nick,
                                        wait=True)

    def muc_message(self, msg):
        if msg['mucnick'] != self.nick and self.nick in msg['body']:
            self.send_message(mto=msg['from'].bare,
                              mbody="%s gobbles cocks" % msg['mucnick'],
                              mtype='groupchat')

    def muc_online(self, presence):
        if presence['muc']['nick'] != self.nick:
            self.send_message(mto=presence['from'].bare,
                              mbody="%s is gay" % (presence['muc']['nick']),
                              mtype='groupchat')


if __name__ == '__main__':
    # Setup the command line arguments.
    optp = OptionParser()

    # Output verbosity options.
    optp.add_option('-q', '--quiet', help='set logging to ERROR',
                    action='store_const', dest='loglevel',
                    const=logging.ERROR, default=logging.INFO)
    optp.add_option('-d', '--debug', help='set logging to DEBUG',
                    action='store_const', dest='loglevel',
                    const=logging.DEBUG, default=logging.INFO)
    optp.add_option('-v', '--verbose', help='set logging to COMM',
                    action='store_const', dest='loglevel',
                    const=5, default=logging.INFO)

    # JID and password options.
    optp.add_option("-j", "--jid", dest="jid",
                    help="JID to use")
    optp.add_option("-p", "--password", dest="password",
                    help="password to use")
    optp.add_option("-r", "--room", dest="room",
                    help="MUC room to join")
    optp.add_option("-n", "--nick", dest="nick",
                    help="MUC nickname")

    opts, args = optp.parse_args()

    # Setup logging.
    logging.basicConfig(level=opts.loglevel,
                        format='%(levelname)-8s %(message)s')

    # login
    opts.jid = JID1
    opts.password = PASS
    opts.room = JIDR
    opts.nick = NICK

    xmpp = JabberCawk(opts.jid, opts.password, opts.room, opts.nick)
    xmpp.register_plugin('xep_0030') # Service Discovery
    xmpp.register_plugin('xep_0004') # Data Forms
    xmpp.register_plugin('xep_0060') # PubSub
    xmpp.register_plugin('xep_0071') # using HTML in messages
    xmpp.register_plugin('xep_0199') # XMPP Ping
    xmpp.register_plugin('xep_0045') # MUC shit

    if xmpp.connect():
        # If you do not have the dnspython library installed, you will need
        # to manually specify the name of the server if it does not match
        # the one in the JID. For example, to use Google Talk you would
        # need to use:
        #
        # if xmpp.connect(('talk.google.com', 5222)):
        #     ...
        xmpp.process(block=True)
        print("Done")
    else:
        print("Unable to connect.")
