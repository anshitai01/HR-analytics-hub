# download_nltk_data.py
import nltk
import os

# Define a local directory to store the NLTK data
DOWNLOAD_DIR = os.path.join(os.getcwd(), 'nltk_data')
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

print(f"Starting NLTK data download into local folder: {DOWNLOAD_DIR}")

# The 'punkt' tokenizer model for splitting text into sentences/words
nltk.download('punkt', download_dir=DOWNLOAD_DIR)

# A list of common 'stopwords' (e.g., 'the', 'a', 'is') to ignore
nltk.download('stopwords', download_dir=DOWNLOAD_DIR)

# The 'wordnet' model for lemmatization (reducing words to their base form)
nltk.download('wordnet', download_dir=DOWNLOAD_DIR)

print("\nAll required NLTK data packages have been downloaded locally.")
print("You can now run the Streamlit application.")