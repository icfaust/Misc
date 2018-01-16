import scipy
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import time
import urllib
try:
    from urllib2 import urlopen
except ImportError:
    from urllib.request import urlopen

import json
import warnings

def AUGspecWarning(message, error=None, email=None, dweet=None, name='CSXR@ipp.mpg.de'):
        if not email is None:
            emailOut(message, recipient=email, name=name, subject = 'Spectrometer Error')

        if not dweet is None:
            dweetOut(message, dweet)
        
        warnings.warn(message)

        
def emailOut(text, recipient=None, name='CSXR@ipp.mpg.de', subject='Spectrometer Message'):
    """ Send an email for a spectrometer error """
    
    # Create message container - the correct MIME type is multipart/alternative.
    msg = MIMEMultipart('alternative')
    msg['Subject'] = name+': '+subject
    msg['From'] = name
    # find time of the fault
    occurence = time.strftime('%X %x %Z')
    
    plaintext = "ALERT: "+text+", this occured at " + occurence
    # Create the body of the message (a plain-text and an HTML version).
    html = """\
    <html>
      <head></head>
        <body>
        <p>SPECTROMETER ALERT:<br> <br>
        ========================= <br>
        <br>
        """+text+"""<br>
        <br>
        ========================= <br>
          This event occured at """ + occurence + """<br>
          </p>
        </body>
    </html>
          """
    # Record the MIME types of both parts - text/plain and text/html.
    part1 = MIMEText(plaintext, 'plain')
    part2 = MIMEText(html, 'html')

    #attach portions of message
    msg.attach(part1)
    msg.attach(part2)
    
    #SEND MAIL VIA IPP SERVERS
    mailserver = smtplib.SMTP('mailhost.rzg.mpg.de', 587)
    # identify ourselves to smtp ipp client
    mailserver.ehlo()
    # secure our email with tls encryption
    mailserver.starttls()
    # re-identify ourselves as an encrypted connection
    mailserver.ehlo()
    mailserver.login('csxr', '06expo00') #we should remove this hard coding

    if not type(recipient) is str:
        for i in recipient:
            msg['To'] = i #add all recipients
    else:
        msg['To'] = recipient

    # send it out    
    mailserver.sendmail(name, recipient, msg.as_string())
    mailserver.quit()
    
def dweetOut(value, name):
    """value is a dictionary, and posts a dweet to name. Responds with a JSON """
    if value is str:
        value = {'shot':value} # when message is just a string (as when emailing) change it to a dict
    
    vals = urllib.urlencode(value)
    dweeturl = 'https://dweet.io/dweet/for/'+ name + '?' + vals
    webpage = urlopen(dweeturl)
    response = json.loads(webpage.read())
    return response
