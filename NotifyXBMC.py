#!/usr/bin/env python

##############################################################################
### NZBGET POST-PROCESSING SCRIPT                                          ###

# Quick-update XBMC Frodo (12.x) library after a download completes successfully.
# Can optionally display an on-screen notification on XBMC as well.
#
# NOTE: This script requires Python to be installed on your system.

##############################################################################
### OPTIONS                                                       ###

# Your XBMC host IP/hostname
#
# Use commas to separate multiple hosts. E.g.: 192.168.0.2,192.168.0.3
#Host=

# Username (if authorization is required)
#Username=

# Password (if authorization is required)
#Password=

# Display a notification on XBMC (yes, no).
#DisplayNotification=yes

# Notification title
#NotificationTitle=NZBGet download finished

# Notification message
#
# %nzbname% is the NZB name that was downloaded (without path or extension)
#NotificationMessage=%nzbname% successfully downloaded.

# Notification image
#
# Path to the image you want to send with the notification e.g. ${MainDir}/ppscripts/nzbget.png 
#NotificationImage=

# Library update type (full, targeted).
#
# A full update will send a generic re-scan request to XBMC.
# A targeted update will use LocalRootPath and RemotePath to figure out how the downloaded directory maps to the XBMC server.
#LibraryUpdateType=targeted

# Local root path
#
# This is the local root path that should be replaced with the below remote path. Use this for cases where
# your XBMC server looks for videos in smb://SERVER/media which equates to the local path /mnt/allmedia.
# In that example, "local root path" would be /mnt/allmedia. Leave this blank if NZBGet downloads to the same box as XBMC and the paths should match.
#LocalRootPath=

# Remote path
#
# This is what the above "local root path" will map to on the XBMC server. In the aforementioned example,
# this would be set to smb://SERVER/media. Leave this blank if NZBGet downloads to the same box as XBMC and the paths should match.
#RemotePath=

### NZBGET POST-PROCESSING SCRIPT ###
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
import re

# Exit codes used by NZBGet
POSTPROCESS_SUCCESS=93
POSTPROCESS_ERROR=94

# Check if the script is called from nzbget 11.0 or later
if not 'NZBOP_SCRIPTDIR' in os.environ:
        print('*** NZBGet post-processing script ***')
        print('This script is supposed to be called from nzbget (11.0 or later).')
        sys.exit(POSTPROCESS_ERROR)

required_options = ('NZBPO_HOST', 'NZBPO_USERNAME', 'NZBPO_PASSWORD', 'NZBPO_DISPLAYNOTIFICATION',
        'NZBPO_NOTIFICATIONTITLE', 'NZBPO_NOTIFICATIONMESSAGE', 'NZBPO_LOCALROOTPATH', 'NZBPO_REMOTEPATH',
        'NZBPO_LIBRARYUPDATETYPE')
for optname in required_options:
        if (not optname in os.environ):
                print('[ERROR] Option %s is missing in configuration file. Please check script settings' % optname[6:])
                sys.exit(POSTPROCESS_ERROR)

if os.path.exists(os.environ['NZBPP_FINALDIR']):
    print('[DETAIL] FINALDIR found. Using %s as updateDir' % os.environ['NZBPP_FINALDIR'])
    updateDir = os.environ['NZBPP_FINALDIR']
else:
    updateDir = os.environ['NZBPP_DIRECTORY']
host = os.environ['NZBPO_HOST']
username = os.environ['NZBPO_USERNAME']
password = os.environ['NZBPO_PASSWORD']
displayNotification = os.environ['NZBPO_DISPLAYNOTIFICATION']
title = os.environ['NZBPO_NOTIFICATIONTITLE']
imagepath = os.environ['NZBPO_NOTIFICATIONIMAGE']
body = os.environ['NZBPO_NOTIFICATIONMESSAGE'].replace('%nzbname%', os.environ['NZBPP_NZBNAME'])
localRoot = os.environ['NZBPO_LOCALROOTPATH']
remotePath = os.environ['NZBPO_REMOTEPATH']
updateType = os.environ['NZBPO_LIBRARYUPDATETYPE']

print('[DETAIL] Script successfully started')
sys.stdout.flush()

class AuthURLOpener(urllibRequest.FancyURLopener):
        def __init__(self, user, pw):
                self.username = user
                self.password = pw
                self.numTries = 0
                urllibRequest.FancyURLopener.__init__(self)

        def prompt_user_passwd(self, host, realm):
                if self.numTries == 0:
                        self.numTries = 1
                        return (self.username, self.password)
                else:
                        return ('', '')

        def openit(self, url, params=None):
                self.numTries = 0
                return urllibRequest.FancyURLopener.open(self, url, params)

def sendToXbmc(inHost, inUsername, inPassword, inCommand):
        myOpener = AuthURLOpener(inUsername, inPassword)

        try:
                urlObj = myOpener.openit('http://%s/jsonrpc?request=%s' % (inHost, inCommand.encode('utf-8')))
        except IOError as e:
                print('[ERROR] Unable to open URL: ' + str(e))
                return False

        if urlObj.getcode() != 200:
                print('[ERROR] Unexpected error code returned: ' + str(urlObj.getcode()))
                print(urlObj.readlines())
                return False

        print(urlObj.readlines())
        return True

def lreplace(pattern, sub, string):
        return re.sub('^%s' % pattern, sub, string)

#  NZBPP_PARSTATUS    - result of par-check:
#                       0 = not checked: par-check is disabled or nzb-file does
#                           not contain any par-files;
#                       1 = checked and failed to repair;
#                       2 = checked and successfully repaired;
#                       3 = checked and can be repaired but repair is disabled.
#                       4 = par-check needed but skipped (option ParCheck=manual);

#  NZBPP_UNPACKSTATUS - result of unpack:
#                       0 = unpack is disabled or was skipped due to nzb-file
#                           properties or due to errors during par-check;
#                       1 = unpack failed;
#                       2 = unpack successful.
if 'NZBPP_TOTALSTATUS' in os.environ:
	downloadSuccess = os.environ['NZBPP_TOTALSTATUS'] == 'SUCCESS'
else:
	parSuccess = os.environ['NZBPP_PARSTATUS'] == '0' or os.environ['NZBPP_PARSTATUS'] == '2'
	unpackSuccess = os.environ['NZBPP_UNPACKSTATUS'] == '2'
	downloadSuccess = parSuccess and unpackSuccess

if downloadSuccess:
        if updateType == 'full':
                updateDir = ""
        elif localRoot and remotePath:
                updateDir = lreplace(localRoot, remotePath, updateDir)

        updateCommand = '{"jsonrpc":"2.0","method":"VideoLibrary.Scan","params":{"directory":"%s"},"id":1}' % updateDir
        bSuccess = True
        for currhost in host.split(','):
                print("Sending update command: " + updateCommand + " to " + currhost)
                if not sendToXbmc(currhost, username, password, updateCommand):
#                       sys.exit(POSTPROCESS_ERROR)
                        bSuccess = False

                if displayNotification == 'yes':
                        print("Displaying notification...")
                        notifyCommand = '{"jsonrpc":"2.0","method":"GUI.ShowNotification","params":{"title":"%s","image":"%s","message":"%s","displaytime":10000},"id":1}' % (title.encode("utf-8"), imagepath, body.encode("utf-8"))
                        if not sendToXbmc(currhost, username, password, notifyCommand):
                                bSuccess = False
#                               sys.exit(POSTPROCESS_ERROR)

                if bSuccess:
                        print("Succeeded.")
                else:
                        print("Failed.")

        if not bSuccess:
                sys.exit(POSTPROCESS_ERROR)
else:
        print("Not doing anything due to par or unpack failure.")

sys.exit(POSTPROCESS_SUCCESS)
