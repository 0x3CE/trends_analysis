# analyze_sentiment_vader.py
import re
from collections import defaultdict
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

def extract_hashtags(tweet):
    return re.findall(r'#(\w+)', tweet)

def analyze_sentiment(tweets):
    analyzer = SentimentIntensityAnalyzer()
    hashtag_sentiments = defaultdict(list)
    for tweet in tweets:
        hashtags = extract_hashtags(tweet)
        sentiment = analyzer.polarity_scores(tweet)['compound']
        for hashtag in hashtags:
            hashtag_sentiments[hashtag].append(sentiment)
    return {hashtag: sum(scores)/len(scores) for hashtag, scores in hashtag_sentiments.items()}

if __name__ == "__main__":
    import sys
    tweets = sys.stdin.read().splitlines()
    sentiments = analyze_sentiment(tweets)
    for hashtag, avg_sentiment in sorted(sentiments.items(), key=lambda x: x[1], reverse=True):
        print(f"{hashtag}: {avg_sentiment:.2f}")
