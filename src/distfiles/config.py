import sys
reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding

import wx

def readPyValFromConfig(conf, name):
    value = conf.Read(name).replace('\r\n', '\n')+'\n'
    try:
        return eval(value)
    
    except:
        print "'"+value+"'"
        raise

def getConfig(configFile):
    if not os.path.exists(configFile):
        raise Exception, 'Config file %s not found'%configFile
    cfg = wx.FileConfig(localFilename=configFile, style= wx.CONFIG_USE_LOCAL_FILE)
#    cfg.SetExpandEnvVars(False)

    # read in all group names for this language
    groupNames = []
    cont, val, idx = cfg.GetFirstGroup()
    while cont:
        groupNames.append(val)
        cont, val, idx = cfg.GetNextGroup(idx)

    # read in common elements
#    uname = readPyValFromConfig(cfg, "USERNAME")
#    assert type(uname) is type({}), \
#          'Common definitions (%s) not a valid dict'%commonDefsFile

    # read in predefined settings
    settingsGroups = {}
    for group in groupNames:
        settingsGroups[group] = readSettingsFromConfig(cfg, group)

    return (cfg, settingsGroup)

def readSettingsFromConfig(config, group):
    config.SetPath('')
    config.SetPath(group)
    settings = []
    cont, val, idx = config.GetFirstEntry()
    while cont:
        settings.append(val+'='+config.Read(val))
        cont, val, idx = config.GetNextEntry(idx)
    config.SetPath('')

    return settings

def writeSettingsToConfig(config, group, settings):
    config.SetPath('')
    config.DeleteGroup(group)
    config.SetPath(group)

    for setting in settings:
        name, value = setting.split('=')
        config.Write(name, value.strip())

    config.SetPath('')


    
if __name__ == '__main__':
    app = wx.PySimpleApp()
    #config = os.path.abspath(os.path.join(home, 'settings.cfg'))
    configFile = os.path.join('','settings.cfg')
    if not os.path.exists(configFile):
        raise Exception, 'Config file %s not found'%configFile
    cfg = wx.FileConfig(localFilename=configFile, style= wx.CONFIG_USE_LOCAL_FILE)
    cfg.Write("test",1)
    print cfg
    print readSettingsFromConfig(cfg, u'Login')



