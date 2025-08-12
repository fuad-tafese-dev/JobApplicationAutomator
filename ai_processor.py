import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import logging
from config import AI_CONFIG


class AIQuestionProcessor:
    def __init__(self, question_db):
        self.nlp = spacy.load("en_core_web_sm")
        self.question_db = question_db
        self.vectorizer = TfidfVectorizer()
        self._prepare_question_vectors()

    def _prepare_question_vectors(self):
        """Preprocess questions and create TF-IDF vectors"""
        self.questions = [q['question'] for q in self.question_db]
        self.answers = [q['answer'] for q in self.question_db]

        # Train TF-IDF vectorizer
        self.question_vectors = self.vectorizer.fit_transform(self.questions)

    def find_best_answer(self, input_question):
        """Find the best matching answer for a given question"""
        try:
            # Preprocess input question
            processed_input = self._preprocess_text(input_question)

            # Vectorize input
            input_vector = self.vectorizer.transform([processed_input])

            # Calculate similarities
            similarities = cosine_similarity(input_vector, self.question_vectors)
            max_index = np.argmax(similarities)
            max_score = similarities[0, max_index]

            # Return best match if above threshold
            if max_score >= AI_CONFIG['similarity_threshold']:
                return self.answers[max_index]

            return AI_CONFIG['default_answer']

        except Exception as e:
            logging.error(f"AI processing failed: {str(e)}")
            return AI_CONFIG['default_answer']

    def _preprocess_text(self, text):
        """Clean and normalize text for comparison"""
        doc = self.nlp(text.lower())
        tokens = [token.lemma_ for token in doc if not token.is_stop and not token.is_punct]
        return " ".join(tokens)