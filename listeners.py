from diary import Diary
from time import sleep

import tweepy

log = Diary("streaming.log")


class EnglishListener(tweepy.streaming.StreamListener):
    def __init__(self, robot):
        super(EnglishListener, self).__init__()
        self.robot = robot

    def on_data(self, data):
        self.robot.handle_data(data)
        return True

    def on_error(self, error):
        if error == 88 or error == 420:
            self.on_limit("Rate limit exceeded")
        else:
            log.error('Sleeping for 30 min due to --')
            log.error(error)
            print(error)
            sleep(1800)

    def on_exception(self, status):
        log.error('Sleeping for 3 min due to --')
        log.error(str(status.args))
        print(status)
        sleep(180)

    def on_limit(self, track):
        log.warn('Sleeping for 30 minutes due to --')
        log.warn(track)
        print(track)
        sleep(1800)

    def on_close(self, resp):
        log.error("Twitter closed connection -- ")
        log.error(resp)
        print(resp)
        return False

    def manual_stop(self):
        self.robot.stream.disconnect()


class MentionListener(EnglishListener):
    def __init__(self, robot, handle="@TeachMeBot"):
        super(MentionListener, self).__init__(robot)
        self.robot = robot
        self.handle = handle

    def on_data(self, data):
        self.robot.handle_mention(data)
