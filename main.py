from google.appengine.ext import ndb
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler

import webapp2
import jinja2

import os
from datetime import datetime,timedelta

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class Dork(ndb.Model):
  email = ndb.StringProperty(indexed=True)
  count = ndb.ComputedProperty(lambda self: self.getDorkCount())
  def getCleanEmail(self):
    return "%s..." % self.email[:self.email.index('@')+3]
  def getDorkCount(self):
    return DorkRecord.query(DorkRecord.dork==self.key).count()

class DorkRecord(ndb.Model):
  dork = ndb.KeyProperty(kind=Dork)
  subject = ndb.StringProperty(indexed=False)
  timestamp = ndb.DateTimeProperty(auto_now_add=True)

class LogSenderHandler(InboundMailHandler):
  def receive(self, mail_message):
    if "dork" in mail_message.subject.lower():
      email = mail_message.sender
      if '<' in email:
        email = email[email.index('<')+1:email.index('>')]
      # find dork
      dork = Dork.query(Dork.email==email).get()
      # if not dork yet, make dork
      if not dork:
        dork = Dork(email=email)
        dork.put()
      recent_dork = DorkRecord.query(
          ndb.AND(
            DorkRecord.dork==dork.key, 
            DorkRecord.timestamp > datetime.utcnow() - timedelta(minutes=15)
            )
          ).get()
      if not recent_dork: 
        # add dork record
        dork_record = DorkRecord(dork=dork.key, subject=mail_message.subject)
        dork_record.put()

class MainPage(webapp2.RequestHandler):
    def get(self):
        dorks = Dork.query().order(-Dork.count)
        template = JINJA_ENVIRONMENT.get_template('index.html')
        self.response.write(template.render({"dorks":dorks}))

app = webapp2.WSGIApplication([
  LogSenderHandler.mapping(),
  ('/', MainPage),
], debug=False)
