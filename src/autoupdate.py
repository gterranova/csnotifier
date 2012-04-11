import os
import urllib, urllib2, md5
import platform

# We need to return the data using JSON. As of Python 2.6+, there is a core JSON
# module. We have a 2.4/2.5 compatible lib included with the agent but if we're
# on 2.6 or above, we should use the core module which will be faster
pythonVersion = platform.python_version_tuple()

JSON_ENABLED = (int(pythonVersion[1]) >= 6)
# Decode the JSON
if JSON_ENABLED: # Don't bother checking major version since we only support v2 anyway
    import json

def update(log, appVersion):

    if not JSON_ENABLED:
        log("Python 2.6 or above is needed for the software update. Auto-update disabled")
        return (-1, "Python 2.6 or above is needed for the software update. Auto-update disabled")

    # Get the latest version info
    try:            
        request = urllib2.urlopen('http://terranovanet.it/lab/csnotifier/src/version.dat')
        response = request.read()
       
    except Exception, e:
        import traceback
        msg = 'Unable to get latest version info - ' + traceback.format_exc().splitlines()[-1]
        return (-1, msg)

    updateInfo = json.loads(response)

    # Do the version check	
    if updateInfo['version'] != appVersion:			
       
        log('A new version is available.')
        
        def downloadFile(agentFile, recursed = False):
            log('Update: downloading ' + agentFile['name'])
            log('Downloading ' + agentFile['name'])
            
            downloadedFile = urllib.urlretrieve('http://www.terranovanet.it/lab/csnotifier/src/' + agentFile['name'])
            
            # Do md5 check to make sure the file downloaded properly
            checksum = md5.new()
            f = file(downloadedFile[0], 'rb')
            
            # Although the files are small, we can't guarantee the available memory nor that there
            # won't be large files in the future, so read the file in small parts (1kb at time)
            while True:
                part = f.read(1024)
                
                if not part: 
                        break # end of file
        
                checksum.update(part)
                
            f.close()
            
            # Do we have a match?
            if checksum.hexdigest() == agentFile['md5']:
                return downloadedFile[0]
                    
            else:
                # Try once more
                if recursed == False:
                    downloadFile(agentFile, True)
                else:
                    log(agentFile['name'] + ' did not match its checksum - it is corrupted. This may be caused by network issues so please try again in a moment.')
                    return
        
        # Loop through the new files and call the download function
        for agentFile in updateInfo['files']:
            agentFile['tempFile'] = downloadFile(agentFile)			
        
        # If we got to here then everything worked out fine. However, all the files are still in temporary locations so we need to move them
        # This is to stop an update breaking a working agent if the update fails halfway through
        
        for agentFile in updateInfo['files']:
            log('Updating ' + agentFile['name'])
                
            if os.path.exists(agentFile['name']):
                os.remove(agentFile['name'])
                        
            os.rename(agentFile['tempFile'], agentFile['name'])
                       
        return (1, 'Update completed. Please restart the agent (python agent.py restart).')
            
    else:
        return (0, 'The agent is already up to date')

