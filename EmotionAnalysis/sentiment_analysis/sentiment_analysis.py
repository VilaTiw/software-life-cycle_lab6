import nltk
from textblob import TextBlob
from newspaper import Article

nltk.download('punkt')

class SentimentAnalyser:
    def __init__(self, strategy):
        self.strategy = strategy

    def analyze_sentiment(self, object: str):
        return self.strategy.analyze(object)

class TextBlobStrategy:
    def analyze(self, text):
        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        print('Bot: ', sentiment)

        return sentiment

class ArticleBlobStrategy:
    def analyze(self, url):
        article = Article(url)
        article.download()
        article.parse()
        article.nlp()

        text = article.summary
        print('Text from article: ', text)

        blob = TextBlob(text)
        sentiment = blob.sentiment.polarity
        print('Bot: ', sentiment)

        return sentiment

def bot_sentiment_analysis(text):
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    print('Bot: ', sentiment)
    #print("Кількість речень у тексті:", len(blob.sentences))
    #print("Сентимент тексту:", blob.sentiment)

    return sentiment

if __name__ == "__main__":
    strategy1 = TextBlobStrategy()
    strategy2 = ArticleBlobStrategy()

    sentiment_analyzer1 = SentimentAnalyser(strategy1)
    sentiment_analyzer2 = SentimentAnalyser(strategy2)

    text = 'Good job'
    url = 'https://en.wikipedia.org/wiki/World_War_II'

    sentiment1 = sentiment_analyzer1.analyze_sentiment(text)
    sentiment2 = sentiment_analyzer2.analyze_sentiment(url)

