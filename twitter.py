import os
import re
import tweepy
import json
import pandas as pandas
import argparse
import time
import datetime
from collections import Counter
from emoji import UNICODE_EMOJI


with open('config.json') as f:
    config = json.load(f)


auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
auth.set_access_token(config['access_token'], config['access_token_secret'])
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)


def get_tweets(user, n=100):
    tweets = []
    for i, status in enumerate(tweepy.Cursor(api.user_timeline, count=200, screen_name=user, tweet_mode="extended", include_rts=False).items()):
        tweets.append(status)
        if i == n-1:
            break
        if i % 100 == 0:
            print(f'{datetime.datetime.now()} | {user} | {i:5d}')
    return tweets


def tweet_to_dict(tweet):
    return {
        'name': tweet.author.name,
        'login': tweet.author.screen_name,
        'likes': tweet.favorite_count,
        'retweets': tweet.retweet_count,
        'text': tweet.full_text,
        'date': tweet.created_at,
        'in_reply': tweet.in_reply_to_screen_name,
        'source': tweet.source,
        'coordinates': tweet.coordinates,
        'geo': tweet.geo,
        'id': tweet.id,
    }


def get_follower_ids(user, n=0):
    followers = []
    for i, follower in enumerate(tweepy.Cursor(api.followers_ids, count=5000, screen_name=user).items()):
        followers.append(follower)
        if i == n-1:
            break
    return followers


def ids_to_users(userids):
    '''
    Taken from https://stackoverflow.com/a/58234314/4110059
    '''
    users = []
    u_count = len(userids)
    for i in range(int(u_count/100) + 1):
        end_loc = min((i + 1) * 100, u_count)
        users.extend(api.lookup_users(user_ids=userids[i * 100:end_loc]))
    return users


def get_followers(user, n=0):
    ids = get_follower_ids(user, n=n)
    return ids_to_users(ids)


def user_to_dict(user):
    return {
        'name': user.name,
        'screen_name': user.screen_name,
        'date': user.created_at,
        'description': user.description,
        'followers_count': user.followers_count,
        'following_count': user.friends_count,
        'statuses_count': user.statuses_count,
        'likes_count': user.favourites_count,
        'default_background':  user.default_profile,
        'default_avatar': user.default_profile_image,
        'verified': user.verified,
        'listed_count': user.listed_count,
        'protected': user.protected,
        'id': user.id,
    }


def build_dataframe(obj_list, dict_func):
    obj_list = [dict_func(obj) for obj in obj_list]
    return pandas.DataFrame(obj_list)


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


def count_patterns(df, patterns):
    counts = []
    for pat in patterns:
        tmp = get_pattern(df, pat).reset_index()
        tmp = tmp[['name', 'login', 'tweet']].drop_duplicates().groupby(['name', 'login']).count().reset_index()
        tmp['pattern'] = pat
        counts.append(tmp)
    return pandas.concat(counts).sort_values(by=['tweet', 'name'], ascending=False)


def tweet_to_words(tweet, min_length=5):
    words = tweet.split()
    words = [w.lower() for w in words if len(w) >= min_length]
    dumb_words = {'dans', 'cette', 'leur', 'merci', 'très', 'nous', 'pour', 'grenoble', 'notre',
            'avec'}
    words = [w for w in words if w not in dumb_words]
    words = [w for w in words if not w.startswith('#') and not w.startswith('@')]
    return words


def tweet_to_words_nltk(tweet, language='french', min_length=5):
    import nltk
    is_noun = lambda pos: pos[:2] == 'NN'
    tokenized = nltk.word_tokenize(tweet, language=language)
    words = [w for w in tokenized if len(w) >= min_length]
    words = [w.lower() for w in words]
    #words = [word for (word, pos) in nltk.pos_tag(words) if is_noun(pos)]
    return words


def is_emoji(s):
    '''
    From https://stackoverflow.com/a/36217640/4110059
    '''
    return s in UNICODE_EMOJI


def tweet_to_emojis(tweet, min_length=None):
    return [char for char in tweet if is_emoji(char)]


def count_words(df, split_func=tweet_to_words_nltk, min_length=5):
    counters = {login: Counter() for login in df['login'].unique()}
    for _, row in df.iterrows():
        login = row['login']
        words = split_func(row['text'], min_length=min_length)
        for w in words:
            counters[login][w] += 1
    rows = []
    for login, c in counters.items():
        rows.extend([{'login': login, 'word': word, 'count': count} for word, count in c.items()])
    df = pandas.DataFrame(rows)
    return df


def tweets_of_user(obj, max_n):
    return build_dataframe(get_tweets(obj, n=max_n), tweet_to_dict)


def followers_of_user(obj, max_n):
    return build_dataframe(get_followers(obj, n=max_n), user_to_dict)


def main():
    functions = [tweets_of_user, followers_of_user]
    choices = {func.__name__: func for func in functions}
    parser = argparse.ArgumentParser(description='Download twitter data and dump it in a CSV')
    parser.add_argument('--max_number', type=int, default=100,
                        help='Maximal number of items to download')
    parser.add_argument('--output', type=str, default='/tmp/data.csv',
                        help='Output CSV file')
    parser.add_argument('mode', choices=choices)
    parser.add_argument('obj', type=str,
                        help='List of twitter ID (e.g. user logins)')
    args = parser.parse_args()
    t = time.time()
    df = choices[args.mode](args.obj, args.max_number)
    df.to_csv(args.output, index=False)
    t = time.time() - t
    print(f'Downloaded {len(df)} objects from twitter in {t:.2f} seconds')


if __name__ == '__main__':
    main()
