"""
Flask backend for Next Word Prediction
Uses a trigram language model trained on a small corpus - fast & lightweight
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import re
from collections import defaultdict, Counter

app = Flask(__name__)
CORS(app)  # Allow frontend to call this API

# ── Corpus: diverse sentences covering common English patterns ──────────────
CORPUS = """
the quick brown fox jumps over the lazy dog
i want to go to the store today
she is going to the market tomorrow
he said that he would be there soon
the weather is very nice today outside
i think we should go for a walk
can you please help me with this problem
the machine learning model is very accurate
i love to read books every night before sleeping
the sun rises in the east and sets in the west
we are going to have a great time at the party
please make sure you complete the task on time
the new technology is changing the world rapidly
i need to buy some groceries from the store
the children are playing in the park happily
she wants to learn how to play the piano
the project deadline is coming up very soon
we should start working on the assignment now
the food at that restaurant is really delicious
i am trying to improve my programming skills
the cat sat on the mat near the window
he went to the gym early in the morning
she called her friend on the phone last night
the team worked hard to finish the project
i would like to have a cup of coffee please
the movie was very interesting and entertaining
we need to find a solution to this problem
the students are studying for their final exams
i hope you have a wonderful day today
the company is planning to launch a new product
she decided to take a break from work today
he is one of the best players on the team
the library has many books on different subjects
i am looking forward to the weekend trip
the doctor advised him to rest for a few days
we had a meeting about the new business plan
the garden looks beautiful in the spring season
i forgot to bring my umbrella to work today
the train arrives at the station at noon
she is very talented and works extremely hard
he bought a new laptop for his college studies
the internet has made communication much easier
i enjoy spending time with my family on weekends
the concert was amazing and the crowd loved it
we are planning a vacation to the mountains
the baby is sleeping peacefully in the crib
i need to call my mother this evening
the office is closed on public holidays
she learned to drive a car last summer
he is reading a very interesting novel right now
the birds are singing beautifully in the morning
we should always be kind to other people
the hospital is located near the city center
i want to learn a new language this year
the sky is clear and the stars are bright tonight
she cooked a delicious meal for the whole family
he fixed the broken chair in the living room
the school starts at eight in the morning
i am very excited about the upcoming event
the river flows gently through the green valley
we decided to adopt a puppy from the shelter
the music festival takes place every summer
i need to finish reading this chapter tonight
the bus stop is just around the corner
she painted a beautiful picture of the sunset
he is planning to start his own business soon
the flowers in the garden are blooming nicely
i would love to visit paris one day
the homework assignment is due on friday morning
we are having dinner with friends this evening
the laptop battery needs to be charged now
i think the answer to this question is correct
the swimming pool is open during summer months
she enjoys hiking in the mountains on weekends
he sent an email to his professor about the project
the supermarket is open until ten at night
i am learning to play the guitar these days
the weather forecast says it will rain tomorrow
we should save money for future emergencies
the new restaurant downtown has great reviews
i need to wake up early for the morning flight
the children love to play video games after school
she is writing a book about her travel experiences
he joined a yoga class to improve his health
the museum has an interesting exhibition this month
i forgot where i put my house keys again
the football match starts at seven in the evening
we are renovating the kitchen in our house
the professor explained the concept very clearly
i want to improve my cooking skills this year
she is very good at solving math problems
he decided to go for a run in the park
the airport is about thirty minutes from here
i need to prepare a presentation for tomorrow
the bookstore has a great collection of novels
we should drink more water every single day
the cat is sleeping on the couch right now
i am going to the gym after work today
the new phone model has excellent camera quality
she is taking an online course in data science
he helped his neighbor carry the heavy boxes
the park is a great place to relax and unwind
i would like to order a pizza for dinner tonight
the meeting has been rescheduled to next monday
we are very happy with the results of the test
the dog barked loudly when the stranger approached
i need to renew my passport before the trip
the coffee shop on the corner makes great lattes
she is very passionate about environmental issues
he is learning to cook new recipes every week
the sunset over the ocean was absolutely breathtaking
i am planning to read more books this year
the gym is very crowded on monday mornings
we should try to reduce our carbon footprint
the new update fixed many bugs in the application
i need to buy a birthday gift for my friend
the hospital staff was very helpful and caring
she is working on a research paper about climate
he loves to travel to new places every year
the children are excited about the school trip
i want to start a healthy lifestyle this month
the library closes at nine in the evening
we are going to watch a movie tonight together
the smartphone has become an essential part of life
i need to finish this report by end of day
the bakery near my house makes fresh bread daily
she is very creative and has many great ideas
he is preparing for his job interview next week
the national park is a wonderful place to visit
i am very grateful for all the support received
the new semester begins at the end of august
we should always try to learn something new daily
"""

def build_model(corpus):
    """Build trigram model from corpus text"""
    # Tokenize
    words = re.findall(r'\b[a-z]+\b', corpus.lower())
    
    # Build bigram and trigram frequency maps
    bigram_model = defaultdict(Counter)
    trigram_model = defaultdict(Counter)
    
    for i in range(len(words) - 1):
        bigram_model[words[i]][words[i+1]] += 1
    
    for i in range(len(words) - 2):
        key = (words[i], words[i+1])
        trigram_model[key][words[i+2]] += 1
    
    return bigram_model, trigram_model

# Build model at startup
bigram_model, trigram_model = build_model(CORPUS)

def predict_next_words(text, top_n=3):
    """Predict next words using trigram → bigram fallback"""
    words = re.findall(r'\b[a-z]+\b', text.lower())
    
    if not words:
        # Return common starters if no input
        return ["the", "i", "we"]
    
    candidates = Counter()
    
    # Try trigram first (last 2 words)
    if len(words) >= 2:
        key = (words[-2], words[-1])
        candidates.update(trigram_model.get(key, {}))
    
    # Fallback to bigram (last word)
    if len(candidates) < top_n:
        candidates.update(bigram_model.get(words[-1], {}))
    
    # Get top N predictions
    if candidates:
        return [word for word, _ in candidates.most_common(top_n)]
    
    return ["the", "a", "is"]  # Default fallback

@app.route('/predict', methods=['POST'])
def predict():
    """API endpoint: receives text, returns top 3 next-word predictions"""
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
    
    text = data['text'].strip()
    
    if not text:
        return jsonify({'predictions': ['the', 'i', 'we']})
    
    predictions = predict_next_words(text, top_n=3)
    return jsonify({'predictions': predictions})

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("✅ Next Word Prediction API running at http://localhost:5000")
    app.run(debug=True, port=5000)
