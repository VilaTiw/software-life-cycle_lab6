from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle

# Функція для передбачення токсичності
def predict_toxicity(comment):
    sequence = tokenizer.texts_to_sequences([comment])
    padded_sequence = pad_sequences(sequence, maxlen=max_len)
    prediction = model.predict(padded_sequence)
    return prediction[0][0]

def bot_toxicity_analysis(text):
    max_len = 200

    model = load_model('EmotionAnalysis/toxicity_analysis/toxic_comment_model.h5')

    with open('EmotionAnalysis/toxicity_analysis/tokenizer.pickle', 'rb') as handle:
        tokenizer = pickle.load(handle)

    sequence = tokenizer.texts_to_sequences([text])
    padded_sequence = pad_sequences(sequence, maxlen=max_len)
    prediction = model.predict(padded_sequence)
    return str(prediction[0][0])


if __name__ == "__main__":
    # Приклад використання
    max_features = 20000
    max_len = 200

    model = load_model('toxic_comment_model.h5')

    with open('tokenizer.pickle', 'rb') as handle:
        tokenizer = pickle.load(handle)

    comment = "You are idiot!"
    print(predict_toxicity(comment))
