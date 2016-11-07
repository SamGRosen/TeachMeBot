# Teach Me Bot
# Python 2.7.8 w/ Tweepy , 3.4 compatible
from configparser import ConfigParser
import random
import tweepy
import diary
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

log = diary.Diary("bot.log")
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
        try:
            if self.running:
                self.main_stream()
        except KeyboardInterrupt:
            self.disconnect()
            pass

    def main_stream(self):
        self.english_stream.filter(track=tracking_words, languages=['en'], async=True)

    def disconnect(self):
        self.running = False
        self.english_stream.disconnect()
        self.mention_stream.disconnect()

    def toggle_stream(self):
        self.english_stream.disconnect()
        # WAIT UNTIL THE HOUR IN STREAM.FILTER
        self.english_stream.filter(track=tracking_words, languages=['en'], async=True)

    def handle_data(self, data):
        if self.is_readable(data):
            self.brain.add_sequence(data["text"])
            self.checker.check()

    def handle_mention(self, data):
        if self.is_readable(data):
            self.brain.add_sequence(data["text"])
            self.reply(data["text"], data["user"])

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


def main_loop():
    t = TeachMeBot()
    t.load()
    try:
        t.loop()
    except BaseException as e:
        log.error("ERROR OCCURED -- sleep for 3 min")
        log.error(e)
        t.disconnect()
        del t
        tweepy.streaming.sleep(180)
        main_loop()


if __name__ == '__main__':
    pass
