#######################################################################
"""
CouchSurfing Notification (ver. 1.2)

CouchSurfing Notifier is a software program that shows you a popup
window whenever someone posts a message on the forum of a
couchsurfing.org group.

Copyright (c) 2009, Gianpaolo Terranova
email: gianpaoloterranova@gmail.com
"""
licenseText = """
This program is free software: you can redistribute it and/or modify 
it under the terms of the GNU General Public License as published by 
the Free Software Foundation, either version 3 of the License, or 
(at your option) any later version.

This program is distributed in the hope that it will be useful, 
but WITHOUT ANY WARRANTY; without even the implied warranty of 
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the 
GNU General Public License for more details.

You should have received a copy of the GNU General Public License 
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
#######################################################################

import sys
reload(sys)
sys.setdefaultencoding('utf-8')
del sys.setdefaultencoding

import cslib
import autoupdate as AU

from time import gmtime, strftime
import os, json

import wx
import wx.stc as stc
import wx.lib.hyperlink as hyperlink
from wx.lib.wordwrap import wordwrap
import toasterbox as TB

import settings
import resources as res

# Check we're not using an old version of Python. We need 2.4 above because some modules (like subprocess)
# were only introduced in 2.4.
if int(sys.version_info[1]) <= 3:
    print 'You are using an outdated version of Python. Please update to v2.4 or above (v3 is not supported).'
    sys.exit(2)
  
NEW_EMAIL_MSG = 'You have %d new messages.'
NEW_THREAD_MSG = 'New thread %s by %s.'
NEW_POST_MSG = '%s (%d new message).'
NEW_POSTS_MSG = '%s (%d new messages).'
NO_MESSAGES_MSG = 'There are no new messages in the forums.'
READ_POST_MSG = 'Read more...'
READ_EMAIL_MSG = 'Check your inbox!'

class RedirectStdOut:
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self,string):
        self.out.write(string, 'gray')

class RedirectStdErr:
    def __init__(self,aWxTextCtrl):
        self.out=aWxTextCtrl

    def write(self,string):
        string = string.replace ( "\n", "" )        
        self.out.write(string, 'red')

class Log(stc.StyledTextCtrl):
    """
    Subclass the StyledTextCtrl to provide  additions
    and initializations to make it useful as a log window.
    """
    def __init__(self, parent, style=wx.SIMPLE_BORDER):
        """
        Constructor
             
        """
        stc.StyledTextCtrl.__init__(self, parent, style=style)
        self._styles = [None]*32
        self._free = 1

    def getStyle(self, c='black'):
        """
        Returns a style for a given colour if one exists.  If no style
        exists for the colour, make a new style.
             
        If we run out of styles, (only 32 allowed here) we go to the top
        of the list and reuse previous styles.
        """
        free = self._free
        if c and isinstance(c, (str, unicode)):
            c = c.lower()
        else:
            c = 'black'

        try:
            style = self._styles.index(c)
            return style

        except ValueError:
            style = free
            self._styles[style] = c
            self.StyleSetForeground(style, wx.NamedColour(c))

            free += 1
            if free >31:
                free = 0
            self._free = free
            return style

    def write(self, text, c=None):
        """
        Add the text to the end of the control using colour c which
        should be suitable for feeding directly to wx.NamedColour.
   
        'text' should be a unicode string or contain only ascii data.
        """
        text = strftime("[%H:%M] ", gmtime()) + text + "\n"
        style = self.getStyle(c)
        lenText = len(text.encode('utf8'))
        end = self.GetLength()
        self.AddText(text)
        self.StartStyling(end, 31)
        self.SetStyling(lenText, style)
        self.EnsureCaretVisible()

    __call__ = write

class MyFrame(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title, pos=(100, 100))
       
        self.tbicon = wx.TaskBarIcon()
        self.tbicon.SetIcon(res.cs_icon.GetIcon(), "CS Notifier")

        # Bind some events to it
        wx.EVT_TASKBAR_LEFT_DCLICK(self.tbicon, self.OnMenuCheck) # left click
        wx.EVT_TASKBAR_RIGHT_UP(self.tbicon, self.ShowMenu) # single left click
        wx.EVT_CLOSE(self,self.OnClose) # triggered when the app is closed, which deletes the icon from tray

        # build the menu that we'll show when someone right-clicks
        self.menu = wx.Menu() # the menu object

        self.menu.Append(101, 'Check now...') # Check
        wx.EVT_MENU(self, 101, self.OnMenuCheck) # Bind a function to it
        
        self.menu.AppendSeparator() # Separator

        if settings.DEBUG:
            self.menu.Append(102, 'Show log...') # Show log
            wx.EVT_MENU(self, 102, self.OnMenuShowLog) # Bind a function to it

        if settings.AUTOUPDATE:
            self.menu.Append(105, 'Check for updates') # AutoUpdate
            wx.EVT_MENU(self, 105, self.OnUpdate) # Bind a function to it

        self.menu.Append(103, 'About...') # About
        wx.EVT_MENU(self, 103, self.OnMenuShowAboutBox) # Bind a function to it

        self.menu.Append(104, 'Close') # Close
        wx.EVT_MENU(self, 104, self.OnMenuClose) # Bind a function to it

        if settings.DEBUG:
            self.log = Log(self)
            sys.stdout=RedirectStdOut(self.log)
            sys.stderr=RedirectStdErr(self.log)

            log = self.log
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            sizer.Add(log, 1, wx.EXPAND)
            self.SetSizer(sizer)
            self.Layout()
            log('CouchSurfing Notifier 1.0.0 (beta) started...', 'blue')

        else:
            self.log = self.dummylog

        self.cs = cslib.cslib(self.log)

        self.posts = []       
        if os.path.exists('current.dat'):
            f = file('current.dat', 'rb')
            self.posts = json.loads(f.read())
            f.close()
        else:
            self.posts.append({'postid':''})
            
        self.messages_unread = 0

        self.timer = wx.Timer(self, -1)
        self.Bind(wx.EVT_TIMER, self.OnTimer, self.timer)
        self.timer.Start(settings.CHECK_INTERVAL*1000)
        self.OnTimer(evt=True)

    def OnClose(self, evt):
        self.Show(False)
        pass
        
    def ShowMenu(self, event):
        self.PopupMenu(self.menu) # show the popup menu

    def dummylog(self, text, c=None):
        return
        
    def OnMenuCheck(self, event):
        self.OnTimer(None)

    def OnMenuShowLog(self, event):
        if settings.DEBUG:
            if not self.IsShown():
                self.Show()
            else:
                self.Show(False)
                
    def OnMenuShowAboutBox(self, evt):
        # First we create and fill the info object
        info = wx.AboutDialogInfo()
        info.Name = "CouchSurfing Notifier"
        info.Version = settings.APP_VERSION
        info.Copyright = "Copyright (c) 2009, Gianpaolo Terranova"
        info.Description = wordwrap(
            "CouchSurfing Notifier is a software program that shows you "
            "a popup window whenever someone posts a message on "
            "the forum of a couchsurfing.org group. ",
            350, wx.ClientDC(self))
        info.WebSite = ("http://www.terranovanet.it", "Author's website")
        info.Developers = [ "Gianpaolo Terranova" ]

        info.License = wordwrap(licenseText, 500, wx.ClientDC(self))

        # Then we call wx.AboutBox giving it that info object
        wx.AboutBox(info)
        
    def OnMenuClose(self, evt):
        self.tbicon.RemoveIcon() # remove the systemtray icon when the program closes
        self.Unbind(wx.EVT_TIMER)
        self.timer.Stop()
        self.timer = None
        wx.GetApp().ExitMainLoop()        

    def OnTimer(self, evt):

        popupWindows = []
        newposts = []
        
        if settings.USERNAME == "<username>":
            dlg = wx.MessageDialog(self, "Hey dude, you did not edit your settings, right?\n\nEdit your settings before starting CouchSurfing Notifier!", "Edit your settings", wx.OK | wx.ICON_ERROR)
            dlg.ShowModal()
            self.Destroy()           
            return
        
        if not self.cs.isLogged():
            data = self.cs.GetLoginPage(settings.USERNAME, settings.PASSWORD)        

        ParseNewMessages = True
        for group_id in settings.ID_GROUP.split(','):          
            data = self.cs.GetForumPage(group_id)
            if ParseNewMessages:
                messages_unread = self.cs.GetUnreadMessages(data)

                if (int(messages_unread) - self.messages_unread) > 0:
                    newmessage = NEW_EMAIL_MSG % (int(messages_unread) - self.messages_unread)
                    popupWindows.append({'message': newmessage,  'link':READ_EMAIL_MSG, 'url':cslib.INBOX_URL})
                    self.messages_unread = int(messages_unread)
                ParseNewMessages = False

            newposts.extend(self.cs.ParseForumPage(data))

        if not os.path.exists('current.dat'):
            f = file('current.dat', 'w')
            f.write(json.dumps(newposts))
            f.close()
            self.posts = newposts
            return
              
        for newpost in newposts:
            found = 0
            for post in self.posts:
                if post['postid'] == newpost['postid']:
                    found = 1
                    new_msg = int(newpost['replies']) - int(post['replies'])
                    if new_msg > 0:
                        tmpl =  NEW_POST_MSG
                        if (new_msg>1):
                            tmpl = NEW_POSTS_MSG                            
                        newmessage = tmpl % (newpost['title'], new_msg)
                        popupWindows.append({'message': newmessage, 'link':READ_POST_MSG, 'url':newpost['link']})
                        post['replies'] = newpost['replies']
                    break
            if found == 0:
                newmessage = NEW_THREAD_MSG % (newpost['title'], newpost['author'])
                popupWindows.append({'message': newmessage, 'link':READ_POST_MSG, 'url':newpost['link']})
                self.posts.append(newpost)

        if len(popupWindows) == 0:
            if evt == None:
                self.ToastMessage(NO_MESSAGES_MSG, cslib.BASE_URL, cslib.BASE_URL)
        else:
            for notification in popupWindows:
                self.ToastMessage(notification['message'], notification['link'], notification['url'])
        pass

        f = file('current.dat', 'w')
        f.write(json.dumps(self.posts))
        f.close()

    def ToastMessage(self, message, link, url):
        self.log(message, 'green')
        message += "\n\n"
        tb = TB.ToasterBox(self, TB.TB_COMPLEX, TB.DEFAULT_TB_STYLE, TB.TB_ONCLICK)
        tb.SetTitle("Couchsurfing Notification")

        tb.SetPopupSize(wx.Size(200, 120))

        client_display = wx.ClientDisplayRect () # get the screen size without taskbar
        pos = wx.Point(client_display[2] - 200 + 3, client_display[3] - 120 - 3)
        tb.SetPopupPosition(pos)
        tb.SetPopupPositionByInt(3)
        
        tb.SetPopupPauseTime(settings.POPUP_PAUSE*1000)
        tb.SetPopupScrollSpeed(20)

        # This Is The New Call Style: The Call To GetToasterBoxWindow()
        # Is Mandatory, In Order To Create A Custom Parent On ToasterBox.
        
        tbpanel = tb.GetToasterBoxWindow()
        panel = wx.Panel(tbpanel, -1)
        panel.SetBackgroundColour("white")

        sizer = wx.BoxSizer(wx.VERTICAL)
        horsizer1 = wx.BoxSizer(wx.HORIZONTAL)

        stbmp = wx.StaticBitmap(panel, -1, res.cs_logo.GetBitmap())
        horsizer1.Add(stbmp, 0)

        sttitle = wx.StaticText(panel, -1, "CouchSurfing Notification")
        fg_colour = wx.Color(51, 152, 255)
        sttitle.SetForegroundColour(fg_colour)
        sttitle.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.BOLD, False, "Verdana"))
        horsizer1.Add(sttitle, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        horsizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sttext = wx.StaticText(panel, -1, message)
        sttext.SetFont(wx.Font(8, wx.SWISS, wx.NORMAL, wx.NORMAL, False, "Verdana"))
        horsizer2.Add(sttext, 1, wx.EXPAND | wx.LEFT | wx.RIGHT, 5)

        hl = hyperlink.HyperLinkCtrl(panel, -1, link, URL=url)

        sizer.Add((5,5))        
        sizer.Add(horsizer1, 0, wx.EXPAND)
        sizer.Add(horsizer2, 0, wx.EXPAND | wx.TOP)

        horsizer3 = wx.BoxSizer(wx.HORIZONTAL)
        horsizer3.Add((5, 0))
        horsizer3.Add(hl, 0, wx.EXPAND | wx.TOP, 10)
        sizer.Add(horsizer3, 0)
        
        sizer.Layout()
        panel.SetSizer(sizer)
        
        tb.AddPanel(panel)
        tb.Play()

    def OnUpdate(self, evt):
        self.log('Checking if there is a new version')
        (status, msg) = AU.update(self.log, settings.APP_VERSION)
        self.ToastMessage(msg, cslib.BASE_URL, cslib.BASE_URL)
        
class MyApp(wx.App): 
    def OnInit(self):
        self.frame = MyFrame(None, -1, "CS Notifier")     
        self.frame.Show(False)
        self.SetTopWindow(self.frame)
        return True

def main():
    app = MyApp(redirect=False)
    app.MainLoop()


if __name__ == "__main__":
    main()

    
