from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# Initialize the VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Sample texts to analyze
texts = [
    "I’m so glad to see Elianna Farhar’s testimony regarding the Uncommitted Movement’s platform requests (starting at 4:30). But I have little hope that it will be included given the way her testimony was treated in follow up by AG Ellison, compared to how the testimony of Haile Soifer CEO of the Jewish Democratic Council of America was treated. It’s almost as if AG Ellison wasn’t expecting the accuracy and coherence of Elianna’s excellent representation of the 700k+ Uncommitted Movement members.",
    "This is the worst thing I've ever bought.",
    "I'm not sure how I feel about this.",
    "It's okay, not great but not bad either.",
    "Absolutely fantastic! Couldn't be happier."
]

# Analyze the sentiment of each text
for text in texts:
    sentiment = analyzer.polarity_scores(text)
    print(f"Text: {text}")
    print(f"Sentiment: {sentiment}")
    print("\n")
