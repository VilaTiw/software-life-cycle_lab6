import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, Bidirectional, LSTM, Dense, GlobalMaxPool1D
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.model_selection import train_test_split
import pandas as pd
import pickle


# Завантаження та підготовка даних
data = pd.read_csv('https://storage.googleapis.com/jigsaw-unintended-bias-in-toxicity-classification/train.csv')
data = data[['comment_text', 'target']]

# Бінаризація мети (цільове значення)
data['target'] = (data['target'] >= 0.5).astype(int)

# Видалення пропущених значень
data = data.dropna(subset=['comment_text'])

# Перетворення всіх значень на рядки
data['comment_text'] = data['comment_text'].astype(str)

# Розділення даних на тренувальний і тестовий набори
train_data, test_data = train_test_split(data, test_size=0.2, random_state=42)

# Підготовка текстових даних
max_features = 20000
max_len = 200

tokenizer = Tokenizer(num_words=max_features)
tokenizer.fit_on_texts(train_data['comment_text'])

X_train = tokenizer.texts_to_sequences(train_data['comment_text'])
X_train = pad_sequences(X_train, maxlen=max_len)

X_test = tokenizer.texts_to_sequences(test_data['comment_text'])
X_test = pad_sequences(X_test, maxlen=max_len)

y_train = train_data['target'].values
y_test = test_data['target'].values

# Створення моделі
model = Sequential([
    Embedding(max_features, 128, input_length=max_len),
    Bidirectional(LSTM(64, return_sequences=True)),
    GlobalMaxPool1D(),
    Dense(1, activation='sigmoid')
])

model.compile(loss='binary_crossentropy', optimizer='adam', metrics=['accuracy'])

# Тренування моделі
history = model.fit(X_train, y_train, epochs=3, batch_size=32, validation_split=0.2)

# Збереження навченої моделі
model.save('toxic_comment_model.h5')

# Збереження токенайзера
with open('tokenizer.pickle', 'wb') as handle:
    pickle.dump(tokenizer, handle, protocol=pickle.HIGHEST_PROTOCOL)