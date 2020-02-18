import os
import re
import tweepy
import json
import pandas as pandas


with open('config.json') as f:
    config = json.load(f)


auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
auth.set_access_token(config['access_token'], config['access_token_secret'])
api = tweepy.API(auth, wait_on_rate_limit=True)


def get_tweets(user, n=100):
    tweets = []
    for i, status in enumerate(tweepy.Cursor(api.user_timeline, screen_name=user, tweet_mode="extended", include_rts=False).items()):
        tweets.append(status)
        if i == n-1:
            break
    return tweets


def build_dataframe(tweets):
    tweet_list = []
    for t in tweets:
        tweet_list.append({
            'name': t.author.name,
            'login': t.author.screen_name,
            'likes': t.favorite_count,
            'retweets': t.retweet_count,
            'text': t.full_text,
            'date': t.created_at,
            'in_reply': t.in_reply_to_screen_name,
            'source': t.source,
            'coordinates': t.coordinates,
            'geo': t.geo,
        })
    return pandas.DataFrame(tweet_list)


def get_data(user, n=100, tag=None):
    df = build_dataframe(get_tweets(user, n=n))
    if tag is not None:
        df['tag'] = tag
    return df


def get_pattern(df, pattern):
    df = df.reset_index(drop=True)
    matches = df['text'].str.extractall(r'(?P<mention>%s)' % pattern, re.IGNORECASE)
    matches.index = matches.index.rename(['tweet', 'match'])
    df.index = df.index.rename('tweet')
    return matches.join(df)


def get_mentions(df):
    return get_pattern(df, '@[a-zA-Z0-9_]+')

def get_hashtags(df):
    return get_pattern(df, '#[a-zA-Z0-9_]+')
