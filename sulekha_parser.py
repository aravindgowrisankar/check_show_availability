#!/usr/bin/env python


import urllib2
import urllib
import pandas as pd
import smtplib
from email.mime.text import MIMEText
import datetime

pd.set_option("display.max_colwidth",-1)
now=datetime.datetime.now()
now_str=now.strftime("%A, %d. %B %Y %I:%M%p")

############## CONFIGS ############## 
### Set these up
cities_of_interest=["san jose","austin","houston","dallas","boston"]
alert_city="san jose"#Send Email only if alert city has a show

email_to="your_to_address"
email_from="your_from_address"
smtp_server="your_sftp_server"
email_subject= "Alex in Wonderland Update for "+alert_city.upper()+" " +now_str
############## CONFIGS ############## 

def city_check(line):
    for city in cities_of_interest:
        if city in line:
            return True
    return False

def parse_custom_site(url="http://alexinwonderland.in/#shows"):
    page = urllib2.urlopen(url)
    lines=page.readlines()
    lines_of_interest=[line for line in lines if city_check(line.lower())]

    show_dict={"Scheduled":[],"Coming Soon":[]}
    for line in lines_of_interest:
        if "Coming Soon to" in line:
            show_dict["Coming Soon"].append(line.split("Coming Soon to ")[1].split("-")[0].strip())
        else:
            show_dict["Scheduled"].append(line.split("<p>")[1].split(" &nbsp")[0].strip())

    return pd.DataFrame.from_dict(show_dict)

def sulekha_link_cleanup(line):
    title=line.split('title="')[1].split('" href')[0]
    title=title.strip()
    url="http://events.sulekha.com"+(line.split('href="')[1].split('">')[0])
    url=url.strip()
    #print ("url",line.split('href="'))
    #url=line
    return (title,url)


def parse_sulekha(artist_url='http://events.sulekha.com/alex_tickets_artist_673'):
    url = artist_url
    response = urllib2.urlopen(url)
    sulekha_lines = response.readlines()

    alex_shows=[line for line in sulekha_lines if "Alex in Wonderland" in line 
                and city_check(line.lower()) and '<div class="tktdecs">' in line ]#and "<li" in line

    #return (words[2],words[3]) if len(words)>2 else (words[0],'N/A')

    cleaned_up_info=[sulekha_link_cleanup(line) for line in alex_shows]

    sulekha_dict={"Title":[],"URL":[]}
    for show in cleaned_up_info:
        sulekha_dict["Title"].append(show[0])
        sulekha_dict["URL"].append(show[1])

    return pd.DataFrame.from_dict(sulekha_dict)

if "__main__"==__name__:
    send_email=False
    web_results=parse_custom_site()

    web_results_html=web_results.to_html()
    sulekha_html=parse_sulekha().to_html()
    
    send_email=web_results[web_results.Scheduled==alert_city.upper()]["Scheduled"].count()>0
    if send_email:    
        msg = MIMEText("<h2>Web Results</h2>"+web_results_html+"<h2>Sulekha Results</h2>"+sulekha_html,"html")
        
        msg['Subject'] = email_subject
        msg['From'] = email_from
        msg['To'] = email_to
        
        s = smtplib.SMTP(smtp_server)
        s.sendmail(email_from, email_to.split(","), msg.as_string())
        s.quit()

