#######################################################################
"""
CSLib (part of CouchSurfing Notification)

CouchSurfing Notifier is a software program that shows you a popup
window whenever someone posts a message on the forum of a
couchsurfing.org group.

Copyright (c) 2009, Gianpaolo Terranova
email: gianpaoloterranova@gmail.com
"""
#######################################################################

import urllib, urllib2, re

BASE_URL = "http://www.couchsurfing.org"
LOGIN_URL = BASE_URL + "/profile.html"
GROUP_URL = BASE_URL + "/group.html?gid=%s"
INBOX_URL = BASE_URL + "/messages.html?message_status=inbox"

NEW_EMAIL_MSG = 'You have %d new messages.'
NEW_THREAD_MSG = 'New thread %s by %s.'
NEW_POST_MSG = '%s (%d new message).'
NEW_POSTS_MSG = '%s (%d new messages).'
NO_MESSAGES_MSG = 'There are no new messages in the forums.'
READ_POST_MSG = 'Read more...'
READ_EMAIL_MSG = 'Check your inbox!'

re_messages = re.compile('\<a href="/messages\.html\?message_status=inbox"\>([\d]*)\<', re.I|re.M)
re_list = re.compile(r"(<a href='/group_read\.html\?gid=[\d]*\&post.*)", re.I|re.M)
re_table_tags = re.compile('\<[/]?t[dr][^>]*>', re.I)
re_fields = re.compile(r"<a href='(/group_read\.html[^']*)'>\s+([^<]*)</a><a href='(/profile\.html[^']*)'>([^<]*)</a>(-?[0-9]*)", re.I|re.M)

class cslib:
    def __init__(self, log=None):
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
        urllib2.install_opener(self.opener)
        self.logged = False

        if log:
            self.log = log
        else:
            self.log = self.dummylog

    def dummylog(self, text, c=None):
        return

    def GetLoginPage(self, username, password):
        self.log("Login...", "gray")
        params = urllib.urlencode({'auth_login[un]':username, 'auth_login[pw]':password})
        f = self.opener.open(LOGIN_URL, params)
        data = f.read()
        f.close()
        self.logged = True        
        return data.decode("utf-8")

    def isLogged(self):
        return self.logged

    def GetForumPage(self, group_id):
        self.log("Retrieving forum page (%s)..." % group_id, "gray")
        f = self.opener.open(GROUP_URL % group_id)
        data = f.read()
        f.close()
        return data.decode("utf-8")

    def GetUnreadMessages(self, data):
        if not self.logged:
            return 0
       
        self.log("Parsing page for new messages...", "gray")
        messages_unread = 0
        m = re_messages.search(data)
        if m:
            try:
                messages_unread = m.group(1)
            except:
                pass
        return messages_unread
    
    def ParseForumPage(self, data):
        #self.log("Parsing forum page for new posts...", "gray")        
        forumPosts = []
        posts = re_list.findall(data)
        for post in posts:
            post = re_table_tags.sub('',post)
            m = re_fields.match(post)

            if m:
                try:
                    alink = m.group(1)
                    postid = alink.split('=')[2]
                    link = BASE_URL+alink
                    title = m.group(2)
                    author = m.group(4)
                    replies = m.group(5)
                    if replies == '-': replies = "0"
                    newitem = {'postid': postid, 'title':title, 'author':author, 'replies':replies, 'link':link}
                    forumPosts.append(newitem)
                    #self.log(title + " [" + replies + "]", "gray")
                except: 
                    self.log("Error parsing post (previous item was '"+title+"'.", 'red')
            else:
                self.log("Unable to parse: "+post, 'red')
        return forumPosts
    

    
