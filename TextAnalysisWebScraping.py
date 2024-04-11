import pandas as pd
from nltk.tokenize import sent_tokenize, word_tokenize
from textblob import TextBlob
import textstat
import os
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.corpus import stopwords, cmudict

# Download NLTK resources
nltk.download('all')

# Load input data from the Excel file
input_data = pd.read_excel('Input.xlsx')

# Load positive and negative dictionaries
positive_dict = set(pd.read_csv('positive-words.txt', header=None, comment=';', encoding='ISO-8859-1')[0])
negative_dict = set(pd.read_csv('negative-words.txt', header=None, comment=';', encoding='ISO-8859-1')[0])

# Load stop words
stop_words_set = set()
stop_words_files = [
    'StopWords_Auditor.txt',
    'StopWords_Currencies.txt',
    'StopWords_DatesandNumbers.txt',
    'StopWords_Generic.txt',
    'StopWords_GenericLong.txt',
    'StopWords_Geographic.txt',
    'StopWords_Names.txt'
]

for file_path in stop_words_files:
    with open(file_path, 'r', encoding='ISO-8859-1') as file:
        stop_words_set.update(file.read().splitlines())

# Initialize variables for analysis
output_data = []

# Function to calculate various metrics
def analyze_text(url_id, url, text):
    blob = TextBlob(text)

    # POSITIVE SCORE and NEGATIVE SCORE
    positive_score = sum(word in positive_dict for word in blob.words)
    negative_score = sum(word in negative_dict for word in blob.words)

    # POLARITY SCORE and SUBJECTIVITY SCORE
    polarity_score = (positive_score - negative_score) / ((positive_score + negative_score) + 0.000001)
    subjectivity_score = (positive_score + negative_score) / (len(blob.words) + 0.000001)

    # AVG SENTENCE LENGTH
    sentences = sent_tokenize(text)
    avg_sentence_length = sum(len(word_tokenize(sentence)) for sentence in sentences) / len(sentences)

    # PERCENTAGE OF COMPLEX WORDS
    complex_words = [word for word in blob.words if textstat.syllable_count(word) > 2]
    percentage_complex_words = len(complex_words) / len(blob.words)

    # FOG INDEX
    fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)

    # AVG NUMBER OF WORDS PER SENTENCE
    avg_words_per_sentence = len(blob.words) / len(sentences)

    # COMPLEX WORD COUNT
    complex_word_count = len(complex_words)

    # WORD COUNT
    word_count = len([word for word in blob.words if word not in stop_words_set and word.isalnum()])

    # SYLLABLE PER WORD
    syllables_per_word = textstat.syllable_count(text) / len(blob.words)

    # PERSONAL PRONOUNS
    personal_pronouns = sum(1 for word in blob.words if word.lower() in ['i', 'we', 'my', 'ours', 'us'])

    # AVG WORD LENGTH
    avg_word_length = sum(len(word) for word in blob.words) / len(blob.words)

    # Append results to output_data
    output_data.append([url_id, url, positive_score, negative_score, polarity_score, subjectivity_score,
                        avg_sentence_length, percentage_complex_words, fog_index, avg_words_per_sentence,
                        complex_word_count, word_count, syllables_per_word, personal_pronouns, avg_word_length])

# Load the Excel file
excel_file = 'Input.xlsx'
df = pd.read_excel(excel_file)

# Function to extract article text from URL
def extract_article_text(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        article_title = soup.title.text.strip()
        article_text = ' '.join([p.text for p in soup.find_all('p')])
        return article_title, article_text
    except Exception as e:
        print(f"Error extracting text from {url}: {e}")
        return None, None

# Create a folder to save text files
output_folder = 'extracted_articles'
os.makedirs(output_folder, exist_ok=True)

# Iterate through each row in the DataFrame
for index, row in df.iterrows():
    url_id = row['URL_ID']
    url = row['URL']

    # Extract article text
    article_title, article_text = extract_article_text(url)

    if article_title and article_text:
        # Save the extracted text to a text file
        file_name = f"{output_folder}/{url_id}.txt"
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(f"{article_title}\n\n{article_text}")

        print(f"Extracted and saved: {file_name}")

print("Extraction completed.")


# Iterate through each row in the input data
for index, row in input_data.iterrows():
    url_id = row['URL_ID']
    url = row['URL']
    text_file_path = f'extracted_articles/{url_id}.txt'  # Adjust the path accordingly

    # Read the extracted text from the file
    with open(text_file_path, 'r', encoding='utf-8') as file:
        text = file.read()

    # Perform analysis
    analyze_text(url_id, url, text)

# Columns for the output data
output_columns = [
    'URL_ID', 'URL',  # Include these columns from Input.xlsx
    'POSITIVE SCORE', 'NEGATIVE SCORE', 'POLARITY SCORE', 'SUBJECTIVITY SCORE',
    'AVG SENTENCE LENGTH', 'PERCENTAGE OF COMPLEX WORDS', 'FOG INDEX',
    'AVG NUMBER OF WORDS PER SENTENCE', 'COMPLEX WORD COUNT', 'WORD COUNT',
    'SYLLABLE PER WORD', 'PERSONAL PRONOUNS', 'AVG WORD LENGTH'
]

# Create a DataFrame for the output data
output_df = pd.DataFrame(output_data, columns=output_columns)

# Save the final output to the specified Excel file
output_df.to_excel('Output.xlsx', index=False)
