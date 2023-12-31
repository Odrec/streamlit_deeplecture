import src.utils as ut
import nltk
from pathlib import Path
from src.config import JSON_DIR, NEIGHBORHOODS_DIR, CSV_DIR
import os
import csv
import pandas as pd
import src.utils as utils


def tokenize(text):
    """
        Tokenize the input text using NLTK's word_tokenize for the Spanish language.

        Parameters:
        - text (str): Input text.

        Returns:
        - list: List of tokens.
    """
    return nltk.word_tokenize(text, language='spanish')


def keep_corrections_csv_clean(corrections_file_name):
    """
    Keep the corrections CSV file clean by removing duplicate and invalid entries.

    Args:
        corrections_file_name (str): Name of the corrections CSV file.

    Returns:
        None
    """
    corrections_file_path = Path(CSV_DIR, corrections_file_name)
    # Read the CSV file into a DataFrame
    df = pd.read_csv(corrections_file_path)

    # Drop rows where the first column has no pair in the second column
    df = df.dropna(subset=[df.columns[1]])

    # Drop duplicate values in the first column
    df = df.drop_duplicates(subset=[df.columns[0]])

    # Convert all values to lowercase
    df = df.map(lambda x: x.lower() if isinstance(x, str) else x)

    # Sort the DataFrame based on the second column
    df = df.sort_values(by=[df.columns[1]])

    # Write the processed DataFrame to a new CSV file
    df.to_csv(corrections_file_path, index=False)

    return corrections_file_path


def collect_neighborhoods(sequences_list, size, json_file='all_extracted_text_2023_corrected_all.json'):
    """
    Collect neighborhoods of a specified sequence in a JSON file and save to another file.

    Args:
        sequences_list (list): List of sequences to search for in the content.
        size (int): Size of the neighborhood (number of words on each side of the sequence).
        json_file (str): Name of the JSON data file.

    Returns:
        dict: Dictionary containing neighborhoods for each document.
    """
    documents_content = ut.open_json_data_file(Path(JSON_DIR, json_file))
    neighborhoods = {}
    count_neighborhoods = 0
    unique_terms = set()
    size = int(size)

    for key, value in documents_content.items():
        neighborhoods[key] = []

        tokenized_content = tokenize(value['text'])
        for i, term in enumerate(tokenized_content):
            for sequence in sequences_list:
                if sequence in term:
                    # Calculate the indices for the neighborhood
                    start_index = max(0, i - size)
                    end_index = min(len(tokenized_content), i + size + 1)
                    # Add unique lowercase terms to add to corrections.csv
                    unique_terms.add(term.lower())

                    # Extract the neighborhood
                    neighborhood = tokenized_content[start_index:end_index]
                    count_neighborhoods += 1

                    # Add the neighborhood and indices to the result
                    neighborhoods[key].append({
                        'neighborhood': " ".join(neighborhood),
                        'start_index': start_index,
                        'end_index': end_index,
                        'num_pages': value['num_pages'],
                        'doc_total_words': len(tokenized_content),
                        'edited': False,  # Manually edited in textarea
                        'updated': False  # Already updated in corpus
                    })
                    # Break from sequences loop to avoid repeated neighborhoods since we already found a match
                    break
    save_file = Path(NEIGHBORHOODS_DIR, '_'.join(sequences_list) + '_size_' + str(size) + '.json')
    ut.save_json_data_file(save_file, neighborhoods)

    # Save unique terms to a CSV file
    unique_terms_file = Path(NEIGHBORHOODS_DIR, f'unique_terms/', f'{'_'.join(sequences_list)}.csv')
    os.makedirs(unique_terms_file.parent, exist_ok=True)
    with open(unique_terms_file, 'w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL)
        csv_writer.writerows([[term] for term in unique_terms])

    print(f"Unique terms with {','.join(sequences_list)}: {unique_terms}")
    print(f"Amount of neighborhoods: {count_neighborhoods}")
    return neighborhoods


def save_edited_neighborhoods_to_corpus(corpus_file_name, neighborhoods_file_name):
    corpus_path = Path(JSON_DIR, corpus_file_name)
    neighborhoods_path = Path(NEIGHBORHOODS_DIR, neighborhoods_file_name)
    corpus_content = utils.open_json_data_file(corpus_path)
    neighborhoods_content = utils.open_json_data_file(neighborhoods_path)
    for key, neighborhoods in neighborhoods_content.items():
        for i, neighborhood in enumerate(neighborhoods):
            if neighborhood['edited'] and not neighborhood['updated']:
                tokenized_corpus_text = tokenize(corpus_content[key]['text'])
                start_index = neighborhood['start_index']
                end_index = neighborhood['end_index']
                updated_content = tokenized_corpus_text[:start_index]
                updated_content.extend(tokenize(neighborhood['neighborhood']))
                updated_content.extend(tokenized_corpus_text[end_index:])
                corpus_content[key]['text'] = ' '.join(updated_content)
                neighborhoods_content[key][i]['updated'] = True
    utils.save_json_data_file(corpus_path, corpus_content)
    utils.save_json_data_file(neighborhoods_path, neighborhoods_content)
