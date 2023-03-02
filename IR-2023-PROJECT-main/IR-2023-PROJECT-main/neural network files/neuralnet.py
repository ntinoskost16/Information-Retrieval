import numpy as np
import pandas as pd
from keras.preprocessing.text import one_hot
from keras.utils import pad_sequences
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import Flatten
from keras.layers import Embedding




# Word Embedding Parameters
INPUT_DIM = 112350  # Size of vocabulary
OUTPUT_DIM = 1000  # Size of the output vectors
INPUT_LENGTH = 50   # Size of largest input text
CLUSTERS = 6        # Number of clusters


final_uids = []
final_isbns = []
final_ratings = []
for i in range(CLUSTERS):
    # Train Data
    ratings = []
    summaries = []
    df_data = pd.read_csv(f'cluster{i+1}.csv')
    for i,row in df_data.iterrows():
        ratings.append(int(row['rating']))
        summaries.append(row['summary'])


    # Encode summaries for embedding
    encoded_summaries = [one_hot(d, INPUT_DIM) for d in summaries]
    padded_summaries = pad_sequences(encoded_summaries, maxlen=INPUT_LENGTH, padding='post')

    # Create One Hot Encoding For Rating
    ratings = np.array(ratings)
    labels = to_categorical(ratings - 1, num_classes=10)


    # define the model
    model = Sequential()
    model.add(Embedding(INPUT_DIM, OUTPUT_DIM, input_length=INPUT_LENGTH, name="embeddings"))
    model.add(Flatten())
    model.add(Dense(10, activation='softmax'))
    # compile the model
    model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
    # summarize the model
    print(model.summary())
    # fit the model
    model.fit(padded_summaries, labels, epochs=15, verbose=1)

    df_pending = pd.read_csv('pending_reviews.csv')
    # Get missing ratings for cluster
    df_pending = df_pending[df_pending['cluster'] == i]


    # Predict missing ratings
    pending_summaries = []
    uids = []
    isbns = []
    ratings = []
    for i,row in df_data.iterrows():
        uids.append(row['uid'])
        isbns.append(row['isbn'])
        pending_summaries.append(row['summaries'])
        
    encoded_summaries = [one_hot(d, INPUT_DIM) for d in pending_summaries]
    padded_summaries = pad_sequences(encoded_summaries, maxlen=INPUT_LENGTH, padding='post')
    
    for s in padded_summaries:
        prediction = model.predict(s)
        rating = np.argmax(prediction) + 1
        ratings.append(rating)
    
    final_uids.extend(uids)
    final_isbns.extend(isbns)
    final_ratings.extend(ratings)

df_final = pd.DataFrame({'uid' : final_uids, 'isbn' : final_isbns, 'rating' : final_ratings})
df_final.to_csv('temp.csv', index=False)
