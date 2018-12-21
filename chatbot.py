# -*- coding: utf-8 -*-
import json
import os
import re
import urllib.request

from bs4 import BeautifulSoup
from slackclient import SlackClient
from flask import Flask, request, make_response, render_template

app = Flask(__name__)

slack_token = "xoxb-508681412357-508418624083-TWwEly9yAjCitGsYI5X3hyb0"
slack_client_id = "508681412357.508522322018"
slack_client_secret = "d7963296c35389369cfe66339a1196a2"
slack_verification = "Gwx1ovCeoDd8wV88KJFjzAiT"
sc = SlackClient(slack_token)

# 크롤링 함수 구현하기
def _crawl_naver_keywords(text):
    
    #여기에 함수를 구현해봅시다.
#     sourcecode = urllib.request.urlopen("https://media.daum.net/").read()
#     soup = BeautifulSoup(sourcecode, "html.parser")
    
#     keywords=[]
#     if news in text:
#         for data in (soup.find_all("h3", class_="tit_view")):
#             if not data.get_text() in keywords:
#                 if len(keywords)>=10:
#                     break
#                 keywords.append(data.get_text())
    
    list_href = []
    list_content=[]
    if "news" in text:
        url = "https://news.naver.com"
        req = urllib.request.Request(url)
        sourcecode = urllib.request.urlopen(url).read()
        soup = BeautifulSoup(sourcecode, "html.parser")

        for href in soup.find_all("a", class_="nclicks(rig.ranksoc)"):
            list_href.append("https://news.naver.com" + href['href'])
        for i in range(0, 10):
            url = list_href[i]
            print(list_href[i])
            req = urllib.request.Request(url)
            sourcecode = urllib.request.urlopen(url).read()
            soup = BeautifulSoup(sourcecode, "html.parser")
            # print(soup.find("h3", id="articleTitle"))
            list_content.append(soup.find("h3", id="articleTitle").get_text().strip())
        
    
    # 한글 지원을 위해 앞에 unicode u를 붙혀준다.
    return u'\n'.join(list_content)

# 이벤트 핸들하는 함수
def _event_handler(event_type, slack_event):
    print(slack_event["event"])

    if event_type == "app_mention":
        channel = slack_event["event"]["channel"]
        text = slack_event["event"]["text"]

        keywords = _crawl_naver_keywords(text)
        sc.api_call(
            "chat.postMessage",
            channel=channel,
            text=keywords
        )

        return make_response("App mention message has been sent", 200,)

    # ============= Event Type Not Found! ============= #
    # If the event_type does not have a handler
    message = "You have not added an event handler for the %s" % event_type
    # Return a helpful error message
    return make_response(message, 200, {"X-Slack-No-Retry": 1})

@app.route("/listening", methods=["GET", "POST"])
def hears():
    slack_event = json.loads(request.data)

    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"content_type":
                                                             "application/json"
                                                            })

    if slack_verification != slack_event.get("token"):
        message = "Invalid Slack verification token: %s" % (slack_event["token"])
        make_response(message, 403, {"X-Slack-No-Retry": 1})
    
    if "event" in slack_event:
        event_type = slack_event["event"]["type"]
        return _event_handler(event_type, slack_event)

    # If our bot hears things that are not events we've subscribed to,
    # send a quirky but helpful error response
    return make_response("[NO EVENT IN SLACK REQUEST] These are not the droids\
                         you're looking for.", 404, {"X-Slack-No-Retry": 1})

@app.route("/", methods=["GET"])
def index():
    return "<h1>Server is ready.</h1>"

if __name__ == '__main__':
    app.run('0.0.0.0', port=8080)