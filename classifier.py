import joblib
import spacy
import numpy as np
from scipy.sparse import hstack
from langdetect import detect, DetectorFactory
DetectorFactory.seed = 2025  

#load spacy models

nlp_en = spacy.load("en_core_web_sm")
nlp_fr = spacy.load("fr_core_news_sm")

#preprocessing function
def preprocess_text(text,language):
    try:

        if language == "fr":
            doc = nlp_fr(text)
        else:
            doc = nlp_en(text)

        tokens = [
            token.lemma_.lower().strip()
            for token in doc
            if not token.is_stop and not token.is_punct
        ]
        return " ".join(tokens)
    except Exception as e:
        print(f"[ERROR] Preprocessing failed: {e}")
        return text 

#load models
model = joblib.load("log_reg_model.pkl")
vectorizer = joblib.load("tfidf_vect.pkl")
model_info = joblib.load("model_info_file.pkl")

category_names = model_info['category_names']
categorical_features = model_info['categorical_features']

#classification function
def classify_legal_query(text):
    try:
        # Detect language once
        language = detect(text)

        # Preprocess text
        processed_text = preprocess_text(text, language)

        # Vectorize preprocessed text
        text_vector = vectorizer.transform([processed_text])

        # Encode language feature
        lang_vector = np.zeros(len(categorical_features))
        lang_col = f"lang_{language}"
        if lang_col in categorical_features:
            lang_index = categorical_features.index(lang_col)
            lang_vector[lang_index] = 1
        lang_vector = lang_vector.reshape(1, -1)

        # Combine TF-IDF + language encoding
        combined_features = hstack([text_vector, lang_vector])

        # Predict category + confidence
        prediction = model.predict(combined_features)[0]
        probabilities = model.predict_proba(combined_features)[0]
        confidence = float(np.max(probabilities) * 100)

        # Reverse-map to category name
        predicted_category = category_names[prediction]

        # Return structured response
        return {
            "query": text,
            "prediction": predicted_category,
            "confidence": round(confidence, 2),
            "language": language
        }

    except Exception as e:
        print(f"[ERROR] Classification failed: {e}")
        return {
            "query": text,
            "prediction": "unknown",
            "confidence": 0.0,
            "language": "unknown"
        }
