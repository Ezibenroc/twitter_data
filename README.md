# Twitter analysis

This repository contains some functions to download and plot Twitter data using Python.

In the following, we assume you have a working Python environment.


## Downloading tweets

You need to install `pandas` and `tweepy`:
```sh
pip install --user pandas tweepy
```

Then, you need to rename the file `example_config.json` into `config.json` and modify it to include your authentication
details. You will have to create your own [Twitter application](https://developer.twitter.com/en/apps).

When this is done, the following command will download the 50 last tweets of the users @gvanrossum and @hadleywickham.
It will create a file `my_twitter_data.csv`.
```sh
python twitter.py --max_tweets=50 --output=my_twitter_data.csv gvanrossum hadleywickham
```

On my laptop, it downloads about 30 tweets per second, so you may have to wait a bit.

## Plotting tweets

The notebook [analysis.ipynb](analysis.ipynb) contains several plots made using some functions of the file
[twitter.py](twitter.py). To run it, you need to install `jupyterlab` and `plotnine` (and `nltk` for some specific
functions):
```sh
pip install --user jupyterlab plotnine nltk
```

Then, start the jupyter server:
```sh
jupyter lab
```
