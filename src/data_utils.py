import src.utils as ut
import nltk
from pathlib import Path
from src.config import JSON_DIR, NEIGHBORHOODS_DIR, CSV_DIR, mongo_connection, mongo_database, mongo_collection
import src.config as config
import os
from bson import ObjectId
import pandas as pd
import src.utils as utils
import concurrent.futures
from tqdm import tqdm
from pymongo import MongoClient
import streamlit as st
import re


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


def apply_corrections_all_collections(corrections_df, neighborhood_collections):
    client = MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    corrections_dict = dict(zip(corrections_df['Original term'], corrections_df['Corrected term']))

    for collection_name in neighborhood_collections:
        st.info(f"Applying corrections to collection {collection_name}. Please wait, this might take a while.")
        print(f"Applying corrections to collection {collection_name}")
        collection = db[collection_name]

        for document in collection.find():
            corrected_neighborhoods = []

            for neighborhood in document['neighborhoods']:
                tokenized_neighborhood = tokenize(neighborhood['neighborhood'])

                # Apply the corrections using set intersection
                corrected_tokens = [corrections_dict.get(token, token) for token in tokenized_neighborhood]

                # Save the updated text back to the JSON data
                neighborhood['neighborhood'] = ' '.join(corrected_tokens)
                corrected_neighborhoods.append(neighborhood)

            # Update the document in the collection with corrected neighborhoods
            collection.update_one(
                {'_id': document['_id']},
                {'$set': {'neighborhoods': corrected_neighborhoods}}
            )

        st.info(f"Corrections applied to collection {collection_name}.")
        print(f"Corrections applied to collection {collection_name}.")

    st.success("All corrections to neighborhood collections applied successfully.")

    collection = db[config.mongo_collection]

    for document in collection.find():
        tokenized_text = tokenize(document['text'])

        # Apply the corrections using set intersection
        corrected_tokens = [corrections_dict.get(token, token) for token in tokenized_text]

        # Save the updated text back to the JSON data
        corrected_document = ' '.join(corrected_tokens)

        collection.update_one(
            {'_id': document['_id']},
            {'$set': {'text': corrected_document}}
        )

    st.info(f"Corrections applied to collection {config.mongo_collection}.")
    print(f"Corrections applied to collection {config.mongo_collection}.")
    st.success(f"Finished applying all corrections.")


def extract_neighborhoods(key, value, sequences_list, size):
    # Tokenize the content
    tokenized_content = tokenize(value['text'])
    unique_terms = set()

    neighborhoods = []
    for i, term in enumerate(tokenized_content):
        for sequence in sequences_list:
            if (sequence.startswith('"') and sequence.endswith('"') and
                re.search(rf'\b{re.escape(sequence[1:-1])}\b', term)) or (
                    sequence not in {'"', "'"} and sequence in term):
                # Calculate the indices for the neighborhood
                start_index = max(0, i - size)
                end_index = min(len(tokenized_content), i + size + 1)

                # Extract the neighborhood
                neighborhood = " ".join(tokenized_content[start_index:end_index])

                neighborhoods.append({
                    'neighborhood': neighborhood,
                    'start_index': start_index,
                    'end_index': end_index,
                    'edited': False,
                    'updated': False,
                })

                # Add the term to unique_terms
                unique_terms.add(term)

                break

    return key, neighborhoods, {'doc_total_words': len(tokenized_content),
                                **value.get('metadata', {})}, unique_terms


def process_document(document, sequences_list, size):
    key, value = document['_id'], document
    return extract_neighborhoods(key, value, sequences_list, size)


def insert_neighborhoods_to_mongo(neighborhoods, sequences_list):
    client = MongoClient(mongo_connection)
    db = client[mongo_database]

    # Modify collection_suffix based on the presence of whole word sequences
    collection_suffix = '_'.join(
        [f'ww_{seq[1:-1]}' if seq.startswith('"') and seq.endswith('"') else seq for seq in sequences_list])

    # Create a new collection for neighborhoods
    neighborhood_collection_name = f'neighborhoods_{collection_suffix}'
    neighborhood_coll = db[neighborhood_collection_name]

    # Insert neighborhoods into the collection
    for key in tqdm(neighborhoods, desc="Inserting Neighborhoods"):
        result = neighborhoods[key]
        # Check if neighborhoods are present before inserting
        if result['neighborhoods']:
            neighborhood_coll.insert_one({
                '_id': key,
                'neighborhoods': result['neighborhoods'],
                'unique_terms': result['unique_terms'],
                'metadata': result['metadata']
            })


def collect_neighborhoods_mongo_parallel(sequences_list, size):
    import time
    start_time = time.time()  # Record start time

    client = MongoClient(mongo_connection)
    db = client[mongo_database]
    documents_collection = db[mongo_collection]

    # Retrieve documents from MongoDB
    documents_content = list(documents_collection.find({}, {'_id': 1, 'text': 1, 'metadata': 1}))
    st.info("Collecting neighborhoods...")
    sequences_list = [seq.strip() for seq in sequences_list]
    # Parallelize processing using ProcessPoolExecutor
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures = [executor.submit(process_document, document, sequences_list, size) for document in documents_content]

        neighborhoods = {}

        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc="Processing Documents"):
            key, result, document_metadata, unique_terms = future.result()
            neighborhoods[key] = {
                'neighborhoods': result,
                'unique_terms': list(unique_terms),
                'metadata': document_metadata
            }
    st.success("Finished collecting neighborhoods.")

    st.info("Inserting neighborhoods to the database.")
    # Insert neighborhoods into MongoDB collection
    insert_neighborhoods_to_mongo(neighborhoods, sequences_list)
    st.success("Finished inserting neighborhoods.")
    end_time = time.time()  # Record end time
    elapsed_time = end_time - start_time
    print(f"Total time taken: {elapsed_time} seconds.")
    return neighborhoods, unique_terms


def update_neighborhood_in_collection():
    collection_name = st.session_state.selected_collection
    current_document_id = st.session_state.filtered_keys[st.session_state.docs_count]
    current_neighborhood_index = st.session_state.hoods_count
    edited_text = st.session_state.hood_text_area

    # Check if the text has been edited
    if edited_text != st.session_state.filtered_docs[current_document_id][current_neighborhood_index]['neighborhood']:

        # Update the MongoDB collection with the edited text
        update_query = {
            '_id': ObjectId(current_document_id),
            'neighborhoods': {
                '$elemMatch': {
                    'start_index': st.session_state.filtered_docs[current_document_id][current_neighborhood_index][
                        'start_index']
                }
            }
        }
        update_operation = {
            '$set': {
                'neighborhoods.$.neighborhood': edited_text,
                'neighborhoods.$.edited': True,
                'neighborhoods.$.updated': False
            }
        }

        client = MongoClient(config.mongo_connection)
        db = client[config.mongo_database]
        neighborhood_collection = db[collection_name]

        neighborhood_collection.update_one(update_query, update_operation)

        # Control if neighbor was successfully saved to show message when rerun
        st.session_state.hood_saved = True
    else:
        st.warning("The original text and the text in the text area are the same.")


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
