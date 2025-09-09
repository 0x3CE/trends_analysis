# analyze_hashtags.py
import re
from collections import Counter

def extract_hashtags(tweets):
    hashtags = []
    for tweet in tweets:
        found = re.findall(r'#(\w+)', tweet)
        hashtags.extend(found)
    return hashtags

def top_hashtags(tweets, n=10):
    hashtags = extract_hashtags(tweets)
    return Counter(hashtags).most_common(n)

if __name__ == "__main__":
    import sys
    tweets = sys.stdin.read().splitlines()
    for hashtag, count in top_hashtags(tweets):
        print(f"{hashtag}: {count}")
