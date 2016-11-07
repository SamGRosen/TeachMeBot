# Teach Me Bot
# Python 2.7.8 w/ Tweepy , 3.4 compatible
import datetime
import tinydb
import random
import tweepy
import timeit
import diary
import json

import markov
from configparser import ConfigParser

secret = ConfigParser()
secret.read("secret.cfg")
credentials = secret["SECRET"]
consumer_token = credentials["ConsumerToken"]
consumer_secret = credentials["ConsumerSecret"]
auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
# TeachMeBot credentials
access_key = credentials["AccessKey"]
access_secret = credentials["AccessSecret"]
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)
tracking_words = ['@TeachMeBot', 'the', 'is', 'a', 'for', 'be', 'to', 'and' 'in', 'that', 'have', 'I',
                  ' ', 'it', 'not', 'on', 'with', 'he', 'as', 'you', 'she', 'do', 'at', 'but', 'why', 'this',
                  'by', 'from', 'they', 'did', 'we', 'say', 'him', 'or', 'an', 'will', 'my', 'one', 'all',
                  'would', 'there', 'their', 'what', 'so', 'up', 'out', 'if', 'about', 'who']
last_tweet = None

log = diary.Diary("bot.log")


def utf(text):
    return tweepy.utils.convert_to_utf8_str(text)

class TeachMeBot():
    def __init__(self, wait=3600, pages=5, rpp=50):
        ''' loop - # of seconds until next tweetsweep
                        pages - # of pages to grab during tweetsweep
                        rpp - # of results per page '''
        self.wait = wait
        self.pages = pages
        self.rpp = rpp
        self.brain = markov.MarkovChainer()
        self.count = 0
        self.replies = 0
        self.period = '{.}'
        self.running = True

    def load(self):
        self.listener = TweetListener(robot=self)
        self.stream = tweepy.Stream(auth, self.listener)
        self.query = api.saved_searches()[0].query

    def tweet_sweep(self, query):  # Manual Stream
        for page in api.search(query):
            for tweet in page:
                data = json.loads(tweet)
                self.add_to_data(data['text'])

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
        self.stream.filter(track=tracking_words, languages=['en'], async=False)

    def disconnect(self):
        self.running = False
        self.stream.disconnect()

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

    def __clean_timeline(self, count=100):
        timeline = api.user_timeline(count=count)
        for tweet in timeline:
            api.destroy_status(tweet.id)


class TweetListener(tweepy.streaming.StreamListener):
    def __init__(self, robot):
        super(TweetListener, self).__init__()
        self.count = 0
        self.robot = robot

    def on_data(self, data):
        try:
            d = json.loads(data)
        except ValueError:  # given bad json, skip
            return True
        if not self.readable(d):
            return True
        text = d["text"].encode('utf-8')
        if '@teachmebot' in text.lower():
            self.handle_mention(data)
            return True
        self.process_new(data)
        self.robot.add_to_data(d["text"])
        if self.count % 1000 == 0:
            log.info("Tweet Count -- ".format(self.count))
        if self.count % 5000 == 0:
            self.robot.stream.disconnect()
            log.info("Saving data -- ".format(self.count))
            log.info("Brain length -- {}".format(len(self.robot.brain)))
            self.robot.save_data()
            self.robot.save_stats()
            log.info("Saved successfully")
            try:
                api.update_status(status=self.robot.random_tweet())
            except:
                pass

            self.robot.main_stream()
        # if self.count % 10000 == 0: # wont activate on 0 bc count is > 0
        # self.cycle()

        return True

    def cycle(self, tweets_per_hour=10000):
        log.warn("Reached cycle limit -- {}".format(tweets_per_hour))
        t = datetime.datetime.now()
        try:
            api.update_status(status=self.robot.random_tweet())
        except:
            log.warn("Could not create random status -- ")
            pass
        time_to_sleep = (60 * (60 - t.minute) - t.second)
        start = timeit.default_timer()
        log.info("Seconds to next cycle -- {}".format(time_to_sleep))
        self.robot.stream.disconnect()
        self.robot.stream.filter(
            track=['@TeachMeBot'], languages=['en'], async=True)
        while timeit.default_timer() - start < time_to_sleep:
            pass
        self.robot.stream.disconnect()
        self.robot.main_stream()
        log.info("Cycle Starting")

    def process_new(self, data):
        self.count += 1
        self.robot.count += 1
        global last_tweet
        last_tweet = data

    def readable(self, data):
        # or data["text"][:3] == 'RT':
        if (not "text" in data) or "retweeted_status" in data:
            return False
        return True

    def on_direct_message(self, dm):
        log.info("CONTACT SYSADMIN PLS")
        log.info(dm)
        return True

    def on_error(self, error):
        if error == 88 or error == 420:
            self.on_limit("Rate limit exceeded")
        else:
            log.error('Sleeping for 30 min due to --')
            log.error(error)
            tweepy.streaming.sleep(1800)

    def on_exception(self, status):
        log.warn('Sleeping for 3 min due to --')
        log.warn(status.args)
        tweepy.streaming.sleep(180)

    def on_limit(self, track):
        log.warn('Sleeping for 30 minutes due to --')
        log.warn(track)
        tweepy.streaming.sleep(1800)

    def on_close(self, resp):
        log.error("Twitter closed connection -- ")
        log.error(resp)
        return False

    def manual_stop(self):
        self.robot.stream.disconnect()

    def handle_mention(self, data):
        d = json.loads(data)
        self.robot.count += 1
        self.robot.replies += 1
        self.robot.add_to_data(d["text"])
        self.robot.reply(d["text"], d["user"]["screen_name"])
        log.log("Responded to -- ", d["user"]["screen_name"])


def main_loop():
    t = TeachMeBot()
    t.load()
    try:
        t.loop()
    except BaseException as e:
        log.error("ERROR OCCURED -- sleep for 3 min", e)
        t.disconnect()
        del t
        tweepy.streaming.sleep(180)
        main_loop()


if __name__ == '__main__':
    try:
        main_loop()
        pass
    except:
        main_loop()
