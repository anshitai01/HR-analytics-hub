# components/exit_analysis/logic.py

import pandas as pd
import logging
import nltk
import re
import os

# --- Import our core AI service for theme interpretation ---
from core import ai_services

# --- NLTK Setup: Self-Contained and Robust ---
# We ensure the app looks for NLTK data within our project folder first.
LOCAL_NLTK_DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'nltk_data')
if os.path.exists(LOCAL_NLTK_DATA_PATH):
    nltk.data.path.insert(0, LOCAL_NLTK_DATA_PATH)

from nltk.stem import WordNetLemmatizer
# This will reliably download the 'wordnet' package to our local folder if it's missing.
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True, download_dir=LOCAL_NLTK_DATA_PATH)
# --- End of NLTK Setup ---

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation

# --- Global Configuration ---
logger = logging.getLogger(__name__)

STOP_WORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any', 'are', "aren't", 'as', 'at',
    'be', 'because', 'been', 'before', 'being', 'below', 'between', 'both', 'but', 'by', 'can', "can't", 'cannot',
    'could', "couldn't", 'did', "didn't", 'do', 'does', "doesn't", 'doing', 'don', "don't", 'down', 'during', 'each',
    'few', 'for', 'from', 'further', 'had', "hadn't", 'has', "hasn't", 'have', "haven't", 'having', 'he', "he'd",
    "he'll", "he's", 'her', 'here', "here's", 'hers', 'herself', 'him', 'himself', 'his', 'how', "how's", 'i', "i'd",
    "i'll", "i'm", "i've", 'if', 'in', 'into', 'is', "isn't", 'it', "it's", 'its', 'itself', 'let', "let's", 'me',
    'more', 'most', "mustn't", 'my', 'myself', 'no', 'nor', 'not', 'of', 'off', 'on', 'once', 'only', 'or', 'other',
    'ought', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 'same', 'shan', "shan't", 'she', "she'd", "she'll",
    "she's", 'should', "shouldn't", 'so', 'some', 'such', 'than', 'that', "that's", 'the', 'their', 'theirs', 'them',
    'themselves', 'then', 'there', "there's", 'these', 'they', "they'd", "they'll", "they're", "they've", 'this',
    'those', 'through', 'to', 'too', 'under', 'until', 'up', 'very', 'was', "wasn't", 'we', "we'd", "we'll", "we're",
    "we've", 'were', "weren't", 'what', "what's", 'when', "when's", 'where', "where's", 'which', 'while', 'who',
    "who's", 'whom', 'why', "why's", 'with', 'won', "won't", 'would', "wouldn't", 'you', "you'd", "you'll", "you're",
    "you've", 'your', 'yours', 'yourself', 'yourselves',
    # Custom words added to ignore based on data review
    'na', 'yes', 'good', 'fair', 'excellent', 'agree', 'better', 'best', 'company', 'organization', 'work', 'working',
    'employee', 'phronesis', 'partner', 'team', 'sometimes', 'nothing', 'issue', 'backed', 'left', 'join', 'fill'
}

# --- Core AI and NLP Helper Functions ---

def _preprocess_text(text: str) -> str:
    """Cleans and prepares text for NLP analysis."""
    if not isinstance(text, str): return ""
    lemmatizer = WordNetLemmatizer()
    tokens = re.findall(r'\b\w+\b', text.lower())
    cleaned_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in STOP_WORDS and len(word) > 2]
    return " ".join(cleaned_tokens)

def _get_sentiment(text: str, analyzer) -> str:
    """Analyzes the sentiment of a text string."""
    if not isinstance(text, str) or not text.strip(): return "Neutral"
    scores = analyzer.polarity_scores(text)
    compound_score = scores['compound']
    if compound_score >= 0.05: return "Positive"
    elif compound_score <= -0.05: return "Negative"
    else: return "Neutral"

def _get_human_readable_theme_name(keywords: list, theme_type: str) -> str:
    """Uses the Gemini LLM to generate a professional name for a theme."""
    prompt = f"""
    As an expert HR analyst, provide a concise, professional, and insightful theme name for a set of keywords from employee exit interviews.
    Theme Type: {theme_type}
    Keywords: {', '.join(keywords)}
    Please provide only the theme name, without any extra explanation or quotation marks.
    """
    theme_name = ai_services.generate_narrative(prompt)
    return theme_name.strip().replace('"', '').replace("Theme Name:", "").strip()

def _extract_specialized_themes(corpus: pd.Series, theme_type: str, num_topics: int = 4, num_words: int = 5) -> tuple:
    """
    Performs Topic Modeling and then calls the AI interpreter to name the themes.
    Returns the interpreted themes, the trained LDA model, and the vectorizer.
    """
    if corpus.empty or len(corpus) < num_topics: return [], None, None
    vectorizer = TfidfVectorizer(max_df=0.9, min_df=2, ngram_range=(1, 2), stop_words=list(STOP_WORDS))
    tfidf_matrix = vectorizer.fit_transform(corpus)
    if tfidf_matrix.shape[1] < num_topics: return [], None, None

    lda = LatentDirichletAllocation(n_components=num_topics, random_state=42)
    lda.fit(tfidf_matrix)

    interpreted_themes = []
    feature_names = vectorizer.get_feature_names_out()
    for topic_idx, topic in enumerate(lda.components_):
        keywords = [feature_names[i].replace(' ', '_') for i in topic.argsort()[:-num_words - 1:-1]]
        theme_name = _get_human_readable_theme_name(keywords, theme_type)
        interpreted_themes.append({"name": theme_name, "keywords": keywords})
    return interpreted_themes, lda, vectorizer

# --- Main Orchestration Function ---

def generate_exit_insights(df: pd.DataFrame) -> dict:
    """
    This is the main function that orchestrates the entire analysis pipeline,
    including multi-theme tagging for the interactive drill-down.
    """
    if df.empty: return {"praise_themes": [], "concern_themes": [], "employee_data": []}

    logger.info("Starting advanced insight generation...")

    # 1. Preprocessing and Sentiment Analysis
    df['full_feedback'] = df[[col for col in df.columns if df[col].dtype == 'object']].fillna('').agg(' '.join, axis=1)
    df['cleaned_feedback'] = df['full_feedback'].apply(_preprocess_text)
    sentiment_analyzer = SentimentIntensityAnalyzer()
    df['sentiment'] = df['full_feedback'].apply(lambda text: _get_sentiment(text, sentiment_analyzer))

    # 2. Split data by intent for specialized modeling
    positive_corpus = df[df['sentiment'] == 'Positive']['cleaned_feedback'].dropna()
    negative_corpus = df[df['sentiment'] == 'Negative']['cleaned_feedback'].dropna()

    # 3. Run the specialized theme discovery and interpretation engines
    praise_themes, praise_lda, praise_vec = _extract_specialized_themes(positive_corpus, "Praise / Satisfaction")
    concern_themes, concern_lda, concern_vec = _extract_specialized_themes(negative_corpus, "Concern / Attrition Driver")

    # 4. THE DRILL-DOWN ENGINE: Assign all relevant themes to each employee
    df['assigned_themes'] = [[] for _ in range(len(df))]

    # Assign Praise Themes based on probability scores
    if praise_themes and praise_lda:
        probs = praise_lda.transform(praise_vec.transform(positive_corpus))
        for i, doc_idx in enumerate(positive_corpus.index):
            # Assign any theme with > 20% probability to enable multi-theme discovery
            assigned = [praise_themes[topic_idx]['name'] for topic_idx, prob in enumerate(probs[i]) if prob > 0.2]
            df.at[doc_idx, 'assigned_themes'].extend(assigned)

    # Assign Concern Themes based on probability scores
    if concern_themes and concern_lda:
        probs = concern_lda.transform(concern_vec.transform(negative_corpus))
        for i, doc_idx in enumerate(negative_corpus.index):
            assigned = [concern_themes[topic_idx]['name'] for topic_idx, prob in enumerate(probs[i]) if prob > 0.2]
            df.at[doc_idx, 'assigned_themes'].extend(assigned)

    # 5. Prepare the final, clean output for the application
    output_df = df.drop(columns=['full_feedback', 'cleaned_feedback'])
    results = {
        "praise_themes": praise_themes,
        "concern_themes": concern_themes,
        "employee_data": output_df.to_dict(orient='records')
    }

    logger.info("Successfully generated AI-interpreted, multi-tagged insights.")
    return results