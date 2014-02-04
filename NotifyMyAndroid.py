#!/usr/bin/env python

##############################################################################
### NZBGET POST-PROCESSING SCRIPT                                          ###

# Notify a user's NotifyMyAndroid account of NZBGet events
#
# NOTE: This script requires Python to be installed on your system.

##############################################################################
### OPTIONS                                                       ###

# Your NotifyMyAndroid API key.
#
# Use commas to separate multiple keys if you want to send multiple notifications. E.g.: 12345,67890
#APIKey=

# The name of the application we should report ourselves as.
#ApplicationName=NZBGet NotifyMyAndroid PPScript

# What event is being reported.
#EventName=Download Complete

# Further description of what was downloaded.
#
# Available variables:
# %directory% - The path to the downloaded files.
# %nzbname% - The friendly name of the release that was downloaded (NZB filename with path and extension removed).
# %nzbfilename% - The filename of the process NZB file.
# %category% - The category of this download.
# %parstatus% - Par check result.
# %unpackstatus% - Unpack result.
#Description=%nzbname% download is complete.

### NZBGET POST-PROCESSING SCRIPT                                          ###
##############################################################################

import sys
try:
	import urllib.request as urllibRequest
	import urllib.parse as urllibParse
except:
	import urllib
	urllibRequest = urllib
	urllibParse = urllib
import os

# Exit codes used by NZBGet
POSTPROCESS_SUCCESS=93
POSTPROCESS_ERROR=94

# Check if the script is called from nzbget 11.0 or later
if not 'NZBOP_SCRIPTDIR' in os.environ:
        print('*** NZBGet post-processing script ***')
        print('This script is supposed to be called from nzbget (11.0 or later).')
        sys.exit(POSTPROCESS_ERROR)

required_options = ('NZBPO_APIKEY', 'NZBPO_APPLICATIONNAME', 'NZBPO_EVENTNAME', 'NZBPO_DESCRIPTION')
for optname in required_options:
        if (not optname in os.environ):
                print('[ERROR] Option %s is missing in configuration file. Please check script settings' % optname[6:])
                sys.exit(POSTPROCESS_ERROR)

print('[DETAIL] Script successfully started')
sys.stdout.flush()

class AuthURLOpener(urllib.FancyURLopener):
        def __init__(self, user, pw):
                self.username = user
                self.password = pw
                self.numTries = 0
                urllib.FancyURLopener.__init__(self)

        def prompt_user_passwd(self, host, realm):
                if self.numTries == 0:
                        self.numTries = 1
                        return (self.username, self.password)
                else:
                        return ('', '')

        def openit(self, url, params):
                self.numTries = 0
                return urllib.FancyURLopener.open(self, url, params)

url='https://www.notifymyandroid.com/publicapi/notify'

apikey=os.environ['NZBPO_APIKEY']
applicationName=os.environ['NZBPO_APPLICATIONNAME']
eventName=os.environ['NZBPO_EVENTNAME']
description=os.environ['NZBPO_DESCRIPTION'] \
	.replace("%directory%", os.environ['NZBPP_DIRECTORY']) \
	.replace("%nzbname%", os.environ['NZBPP_NZBNAME']) \
	.replace("%nzbfilename%", os.environ['NZBPP_NZBFILENAME']) \
	.replace("%category%", os.environ['NZBPP_CATEGORY']) \
	.replace("%parstatus%", os.environ['NZBPP_PARSTATUS']) \
	.replace("%unpackstatus%", os.environ['NZBPP_UNPACKSTATUS'])

bSuccess = True
for key in apikey.split(','):
	params = urllib.urlencode({'apikey': key, 'application': applicationName, 'event': eventName, 'description': description})

	myOpener = AuthURLOpener('', '')

	try:
        	urlObj = myOpener.openit(url, params)
	except IOError as e:
		print('[ERROR] Unable to open URL: ' + str(e))
		sys.exit(POSTPROCESS_ERROR)

	if urlObj.getcode() != 200:
		print('[ERROR] Unexpected error code returned for key ' + key + ': ' + str(urlObj.getcode()))
		print(urlObj.readlines())
		bSuccess = False

if not bSuccess:
	sys.exit(POSTPROCESS_ERROR)
else:
#	print('SUCCESS!')
	sys.exit(POSTPROCESS_SUCCESS)
