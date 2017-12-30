import string
import glob
import re
import csv

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter, resolve1
from pdfminer.pdfdocument import PDFDocument
from pdfminer.converter import TextConverter
from pdfminer.pdfparser import PDFParser
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO

import nltk
from nltk.corpus import stopwords

import pandas as pd

import matplotlib.pyplot as plt
from wordcloud import WordCloud

from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

#####################################################################################################################


def extract_text(file_path):
    out = StringIO()
    # Preparing for reading pdf file
    manager = PDFResourceManager()
    converter = TextConverter(manager, out, laparams=LAParams())
    interpreter = PDFPageInterpreter(manager, converter)

    file = open(file_path, 'rb')

    # Getting page numbers as list
    parser = PDFParser(file)
    document = PDFDocument(parser)
    pages = set(range(resolve1(document.catalog['Pages'])['Count']))

    # Getting each page's text
    for page in PDFPage.get_pages(file, pages):
        interpreter.process_page(page)
    file.close()
    converter.close()
    text = out.getvalue()
    out.close()

    # Clearing the string
    text = re.sub('\s\s+', ' ', text)
    text = text.lower()
    text = text.replace('\n', ' ')
    exclude = set(string.punctuation)
    exclude.add('®')
    text = ''.join(ch for ch in text if ch not in exclude)
    return text


def get_stopwords():
    f = open('stopwords.txt', 'r', encoding="utf8")
    text = f.read()
    words = text.split('\n')
    f.close()
    return words

# #########################################                 FUNCTIONS                 #################################

input_paths = glob.glob('downloadable_input_files/*.pdf')

extra_stopwords = get_stopwords()
stops = set(stopwords.words('english')).union(set(extra_stopwords))

tf_dict = {}
lemma = nltk.wordnet.WordNetLemmatizer()

for path in input_paths:
    print('>> Processing ' + path)
    full_text = extract_text(path)
    tokens = nltk.word_tokenize(full_text)
    tokens = [lemma.lemmatize(word) for word in tokens]
    # Removing stopwords here
    filtered = [word for word in tokens if word not in stops]
    # Removing the words which has the length one or less
    for item in filtered:
        if len(item) < 2:
            filtered.remove(item)
    # Calculating Term Frequency
    vec = CountVectorizer(input='content', binary=False, ngram_range=(1, 1))
    vec_fit = vec.fit_transform(filtered)
    # Getting term frequency matrix and words
    tf_vector = vec_fit.toarray().sum(axis=0).tolist()
    feature_names = vec.get_feature_names()
    for i in range(len(feature_names)):
        if feature_names[i] not in tf_dict.keys():
            tf_dict[feature_names[i]] = tf_vector[i]
        else:
            tf_dict[feature_names[i]] += tf_vector[i]


# Creating term frequency data for DataFrame
tf_data = {'Words': list(tf_dict.keys()),
           'TF': list(tf_dict.values())}
df = pd.DataFrame(tf_data, columns=['Words', 'TF'])
df = df.sort_values('TF', ascending=False)
df[:50].to_csv('out/tf_list.csv', encoding='utf-8', sep=';', mode='w', index=False, header=False)
print('\n>> Term Frequency List is ready as a csv file...\n')

# Getting most frequent 50 words and their frequencies from the csv file in order to create a word cloud
tf_first_50_dict = {}
with open('out/tf_list.csv', newline='\n') as csvfile:
    reader = csv.reader(csvfile, delimiter=';')
    for row in reader:
        tf_first_50_dict[row[0]] = float(row[1])
csvfile.close()

# Word cloud for term frequency
tf_cloud = WordCloud(background_color='White', relative_scaling=0.7, width=1366,
                     height=768).generate_from_frequencies(tf_first_50_dict)
plt.imshow(tf_cloud)
plt.axis('off')
plt.savefig('out/tf_wordCloud.pdf', format='pdf')