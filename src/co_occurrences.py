import src.utils as utils
import src.data_utils as data_utils
import src.spanish_stopwords as stopwords
import src.config as config
from scipy.sparse import coo_matrix
from pymongo import MongoClient
import numpy as np
import concurrent.futures
from functools import partial

import time


def process_context_word(context_word_index, vocabulary, row):
    local_context_word_sum = {}
    context_word = next((k for k, v in vocabulary.items() if v == context_word_index), None)

    if context_word is not None:
        # Use direct indexing of the row
        value = int(row[0, context_word_index])

        # Check if the context word already has a sum
        if context_word in local_context_word_sum:
            local_context_word_sum[context_word] += value
        else:
            local_context_word_sum[context_word] = value

    return local_context_word_sum


def get_top_co_occurrences(co_occurrence_matrix, vocabulary, target_words, maximum_co_occurrences=5000):
    context_word_sum = {}
    ww_flag = False
    indices_subset = []
    extended_target_words = set()
    for target_word in target_words:
        # If the next target word is a whole word set the flag and move to next word
        if target_word == 'ww':
            ww_flag = True
            continue
        # Check if the target word is a whole word in the vocabulary
        if ww_flag:
            # If it's a whole word then it's only one case
            indices_subset.append(vocabulary[target_word])
            extended_target_words.add(target_word)
            ww_flag = False
        else:
            # If not a whole word, find all words in the vocabulary that include the target word
            prefix_matches = []
            for k, v in vocabulary.items():
                if target_word in k and k not in extended_target_words:
                    prefix_matches.append(v)
                    extended_target_words.add(k)
            indices_subset.extend(prefix_matches)

    print(extended_target_words)

    print(indices_subset)

    co_occurrence_matrix_subset = co_occurrence_matrix.tocsr()[indices_subset][:, :]

    print(co_occurrence_matrix_subset)

    # Sort target words by overall frequency
    extended_target_words = list(extended_target_words)
    print(extended_target_words)
    sum_sorted_cm = -np.sum(co_occurrence_matrix_subset, axis=1)
    print(sum_sorted_cm)
    sorted_indices = np.argsort(sum_sorted_cm, axis=0)
    print(sorted_indices)
    sorted_target_words = [extended_target_words[int(i)] for i in sorted_indices]

    # Find the top N co-occurrences for each word
    print(sorted_target_words)
    for i, word in enumerate(sorted_target_words):
        print(i, word)
        row = co_occurrence_matrix_subset.getrow(sorted_indices[i])
        nonzero_indices = row.nonzero()[1]

        start_time = time.time()

        # Use ProcessPoolExecutor for parallel processing
        with concurrent.futures.ProcessPoolExecutor() as executor:

            process_partial = partial(process_context_word, vocabulary=vocabulary, row=row)

            # Map the function to each non-zero index
            results = executor.map(process_partial, nonzero_indices)

        # Combine the results from each process into a single dictionary
        for result in results:
            for k, v in result.items():
                if k in context_word_sum:
                    context_word_sum[k] += v
                else:
                    context_word_sum[k] = v

        end_time = time.time()
        elapsed_time = end_time - start_time

        print(f"Time taken: {elapsed_time} seconds")

    top_co_occurrences = []
    # Convert the summed co-occurrences back to the required format
    for context_word, sum_value in context_word_sum.items():
        co_occurrence = {"word": context_word, "count": sum_value}
        top_co_occurrences.append(co_occurrence)

    # Sort the co-occurrences by count from higher to lower
    top_co_occurrences.sort(key=lambda x: x["count"], reverse=True)

    # Limit the number of top co-occurrences to a maximum
    top_co_occurrences = top_co_occurrences[:maximum_co_occurrences]

    return top_co_occurrences


def extract_neighborhoods(filtered_neighborhoods_dictionary):
    # Getting the neighborhoods data
    neighborhoods_list = [content['neighborhoods'] for doc, content in filtered_neighborhoods_dictionary.items()]

    # Flattening the neighborhoods list to a single list of dictionaries
    neighborhoods = [neighborhood for neighborhoods_sublist in neighborhoods_list for neighborhood in
                     neighborhoods_sublist]

    return neighborhoods


class CoOccurrences:

    def __init__(self):
        self.StopWords = stopwords.StopWords()
        self.StopWords.set_stopwords()
        client = MongoClient(config.mongo_connection)
        self.db = client[config.mongo_database]

        self.context_word_sum = {}

    def fetch_top_co_occurrences_from_mongodb(self):
        # Initialize a dictionary to store collections and their data
        co_occurrences_data_dict = {}

        # Iterate over collections whose names end with "co_occurrences"
        for collection_name in self.db.list_collection_names():
            if collection_name.endswith("_co_occurrences"):
                co_occurrences_collection = self.db[collection_name]
                # Assuming there is only one document in each collection
                co_occurrences_data = co_occurrences_collection.find_one()
                co_occurrences_data_dict[collection_name] = co_occurrences_data

        # Check if any matching collections were found
        if co_occurrences_data_dict:
            # Sort the dictionary by collection name in alphabetical order
            sorted_data_dict = dict(sorted(co_occurrences_data_dict.items()))
            return sorted_data_dict

        # Return an empty dictionary if none were found
        return {}

    def store_top_co_occurrences_in_mongodb(self, top_co_occurrences, window_size,
                                            filters, target_words):
        target_words_list = []
        ww_flag = False
        for target_word in target_words:
            if target_word == 'ww':
                ww_flag = True
                continue
            if ww_flag:
                target_words_list.append(f'"{target_word}"')
                ww_flag = False
            else:
                target_words_list.append(target_word)

        # Store the top co-occurrences in MongoDB
        co_occurrences_collection_name = f'{("_".join(target_words))}_{window_size}'

        if filters:
            co_occurrences_collection_name += '_' + '_'.join(['_'.join(v) for k, v in filters.items()])
        co_occurrences_collection_name += '_co_occurrences'
        co_occurrences_collection = self.db[co_occurrences_collection_name]

        # Drop the existing collection if it exists for replacement
        co_occurrences_collection.drop()

        co_occurrences_data = {
            'top_co_occurrences': top_co_occurrences,
            'window_size': window_size,
            'filters': filters,
            'target_words': target_words_list
        }

        co_occurrences_collection.insert_one(co_occurrences_data)

    def clean_tokenize_neighborhood(self, neighborhood):
        neighborhood_lowercase = neighborhood.lower()
        neighborhood_no_stopwords = self.StopWords.remove_stopwords(neighborhood_lowercase)
        neighborhood_no_stopwords_filtered = utils.remove_accents(neighborhood_no_stopwords)
        neighborhood_no_stopwords_filtered = utils.remove_non_letters(neighborhood_no_stopwords_filtered)
        neighborhood_no_stopwords_filtered = self.StopWords.remove_stopwords(neighborhood_no_stopwords_filtered)

        # Tokenize and remove words smaller than 3 letters
        tokenized_neighborhood = [word for word in data_utils.tokenize(neighborhood_no_stopwords_filtered) if
                                  len(word) >= 3]

        return tokenized_neighborhood

    def generate_co_occurrences_matrix(self, neighborhoods_dict, window_size=config.co_occurrence_neighborhood_size):

        vocabulary = {}

        neighborhoods = extract_neighborhoods(neighborhoods_dict)
        print(len(neighborhoods))

        row_indices, col_indices, data = [], [], []

        for neighborhood_data in neighborhoods:
            neighborhood = neighborhood_data.get('neighborhood', '')  # Extracting the 'neighborhood' field
            tokens = self.clean_tokenize_neighborhood(neighborhood)

            for i, target_word in enumerate(tokens):
                for j in range(max(0, i - window_size), min(len(tokens), i + window_size + 1)):
                    if i != j:
                        context_word = tokens[j]

                        if target_word not in vocabulary:
                            vocabulary[target_word] = len(vocabulary)

                        if context_word not in vocabulary:
                            vocabulary[context_word] = len(vocabulary)

                        target_idx = vocabulary[target_word]
                        context_idx = vocabulary[context_word]

                        row_indices.append(target_idx)
                        col_indices.append(context_idx)
                        data.append(1)

        co_occurrence_matrix = coo_matrix((data, (row_indices, col_indices)),
                                          shape=(len(vocabulary), len(vocabulary)))

        return co_occurrence_matrix, vocabulary
