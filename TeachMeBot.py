# Teach Me Bot
# Python 2.7.8 w/ Tweepy , 3.4 compatible
from configparser import ConfigParser
from threading import Thread
from diary import Diary
from time import sleep

import datetime
import random
import tweepy
import json

from listeners import EnglishListener, MentionListener
import markov

secret = ConfigParser()
secret.read("secret.cfg")
credentials = secret["SECRET"]
consumer_token = credentials["ConsumerToken"]
consumer_secret = credentials["ConsumerSecret"]
access_key = credentials["AccessKey"]
access_secret = credentials["AccessSecret"]
auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)

tracking_words = ['the', 'is', 'a', 'for', 'be', 'to', 'and' 'in', 'that', 'have', 'I',
                  ' ', 'it', 'not', 'on', 'with', 'he', 'as', 'you', 'she', 'do', 'at', 'but', 'why', 'this',
                  'by', 'from', 'they', 'did', 'we', 'say', 'him', 'or', 'an', 'will', 'my', 'one', 'all',
                  'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who']

log = Diary("bot.log")
END_STOP = u"\u3002"


def utf(text):
    return tweepy.utils.convert_to_utf8_str(text)


class Checker:
    def __init__(self, marker, action=None):
        self.marker = marker
        self.action = action
        self.count = 0

    def check(self):
        self.count += 1
        if self.count % self.marker == 0:
            if self.action:
                self.action()


class TeachMeBot:
    def __init__(self):
        self.checker = Checker(1000, self.toggle_stream)
        self.brain = markov.MarkovChainer()
        self.running = True

    def load(self):
        self.english_listener = EnglishListener(robot=self)
        self.english_stream = tweepy.Stream(auth, self.english_listener)
        self.mention_listener = MentionListener(robot=self, handle="@TeachMeBot")
        self.mention_stream = tweepy.Stream(auth, self.mention_listener)

        self.query = api.saved_searches()[0].query

    def loop(self):
        log.info("Bot loop and cycle start")
        self.running = True
        self._thread = Thread(target=self.main_stream)
        self._thread.start()
        self.mention_stream.filter(track=[self.mention_listener.handle], languages=['en'], async=True)

    def main_stream(self):
        self.english_stream.filter(track=tracking_words, languages=['en'], async=False)

    def disconnect(self):
        self.running = False
        self.english_stream.disconnect()
        self.mention_stream.disconnect()

    def toggle_stream(self):
        self.english_stream.disconnect()
        status = self.random_tweet()
        api.update_status(status=status)
        log.log("Status: {}".format(status))
        now = datetime.datetime.now()
        seconds = 60 * (60 - now.minute) - now.second
        log.log("Waiting {} seconds until next hour".format(seconds))
        sleep(seconds)
        self.english_stream.filter(track=tracking_words, languages=['en'], async=False)

    def handle_data(self, data):

        if self.is_readable(data):
            as_json = json.loads(data)
            self.brain.add_sequence(as_json["text"])
            self.checker.check()

    def handle_mention(self, data):
        if self.is_readable(data):
            as_json = json.loads(data)
            self.brain.add_sequence(as_json["text"])
            self.reply(as_json["text"], as_json["user"])

    def is_readable(self, data):
        return "text" in data and "retweeted_status" not in data

    def reply(self, text, screen_name):
        tweet = screen_name
        line = text.split()
        if len(line) < 2:
            tweet += self.random_tweet()
            api.update_status(status=tweet)
            return

        doubles = [(word, line[i + 1]) for i, word in enumerate(line[:-1])]
        random.shuffle(doubles)

        for double in doubles:
            if double in self.brain:
                tweet += self.brain.chain(double)
        else:
            tweet += self.random_tweet()
        api.update_status(status=tweet)

    def random_tweet(self):
        return self.brain.chain(self.brain.get_random_key())

    def tweet_sweep(self, query):  # Manual Stream
        for page in api.search(query):
            for tweet in page:
                data = json.loads(tweet)
                self.brain.add_sequence(data['text'])

    def __clean_timeline(self, count=100):
        timeline = api.user_timeline(count=count)
        for tweet in timeline:
            api.destroy_status(tweet.id)


def main():
    t = TeachMeBot()
    t.load()
    t.loop()


if __name__ == '__main__':
    main()
