import nltk
from pathlib import Path
from src.config import mongo_connection, mongo_database, mongo_collection, corrections_collection_name
import src.config as config
import pandas as pd
import src.control_widgets as cw
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


def keep_corrections_csv_clean(corrections_file_name='corrections.csv'):
    """
    Keep the corrections CSV file clean by removing duplicate and invalid entries.

    Parameters:
        corrections_file_name (str): Name of the corrections CSV file.

    Returns:
        Path: Path to the corrections CSV file.
    """
    corrections_file_path = Path('../csv/', corrections_file_name)

    # Check if the file exists and is not empty
    if not corrections_file_path.is_file() or corrections_file_path.stat().st_size == 0:
        print(f"Error: The CSV file {corrections_file_path} is empty or does not exist.")
        return None

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


def apply_filters_to_neighborhoods():
    """
    Apply metadata and term filters to the documents and update the session state accordingly.
    """
    cw.enable_neighborhoods_widgets()

    # Apply metadata filters to the documents
    st.session_state.filtered_docs = {}
    for doc_id, doc in st.session_state.hoods_docs.items():
        metadata = doc.get('metadata', {})
        if (not st.session_state.selected_nacionalidad or metadata.get(
                'nacionalidad') in st.session_state.selected_nacionalidad) and \
                (not st.session_state.selected_entidad_territorial or metadata.get(
                    'entidad territorial') in st.session_state.selected_entidad_territorial) and \
                (not st.session_state.selected_periodo or metadata.get('periodo') in st.session_state.selected_periodo):
            st.session_state.filtered_docs[doc_id] = doc

    st.session_state.filters = {}

    # Apply term filter do the documents
    # TODO: manage whole words and multiple filter words
    if st.session_state.filter_by_term != "":
        filtered_by_term_dict = {}
        for doc_id, doc in st.session_state.filtered_docs.items():
            for hood in doc.get('neighborhoods', []):
                if st.session_state.filter_by_term in hood['neighborhood']:
                    if doc_id not in filtered_by_term_dict:
                        filtered_by_term_dict[doc_id] = {'neighborhoods': [], 'unique_terms': doc['unique_terms'],
                                                         'metadata': doc['metadata'],
                                                         'hoods_sequences': doc['hoods_sequences'],
                                                         'hoods:size': doc['hoods_size']}
                    filtered_by_term_dict[doc_id]['neighborhoods'].append(hood)

        st.session_state.filtered_docs = filtered_by_term_dict
        st.session_state.filters['Terms'] = st.session_state.filter_by_term.split(',')

    st.session_state.filtered_keys = list(st.session_state.filtered_docs.keys())
    st.session_state.docs_count = 0
    st.session_state.hoods_count = 0

    if 'selected_periodo' in st.session_state and st.session_state.selected_periodo:
        st.session_state.filters['Periodos'] = st.session_state.selected_periodo
    if 'selected_entidad_territorial' in st.session_state and st.session_state.selected_entidad_territorial:
        st.session_state.filters['Entidad Territorial'] = st.session_state.selected_entidad_territorial
    if 'selected_nacionalidad' in st.session_state and st.session_state.selected_nacionalidad:
        st.session_state.filters['Nacionalidad'] = st.session_state.selected_nacionalidad


def extract_neighborhoods(key, value, sequences_list, size):
    """
    Extract neighborhoods from a document based on given sequences.

    Parameters:
    - key (str): Document key.
    - value (dict): Document content.
    - sequences_list (list): List of sequences to search for neighborhoods.
    - size (int): The size of neighborhoods.

    Returns:
    - tuple: Document key, extracted neighborhoods, metadata, and unique terms.
    """
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
                    'edited': False
                })

                # Add the term to unique_terms
                unique_terms.add(term)

                break

    return key, neighborhoods, {'doc_total_words': len(tokenized_content),
                                **value.get('metadata', {})}, unique_terms


def process_document(document, sequences_list, size):
    """
    Process a document, extracting neighborhoods based on given sequences.

    Parameters:
    - document (dict): The document to process.
    - sequences_list (list): List of sequences to search for neighborhoods.
    - size (int): The size of neighborhoods.

    Returns:
    - tuple: Extracted neighborhoods and related information.
    """
    key, value = document['_id'], document
    return extract_neighborhoods(key, value, sequences_list, size)


def insert_neighborhoods_to_mongo(neighborhoods, neighborhood_collection_name, document_ids=None):
    """
    Insert or update neighborhoods into the MongoDB collection.

    Parameters:
    - neighborhoods (dict): Extracted neighborhoods.
    - neighborhood_collection_name (str): Name of the MongoDB collection to store neighborhoods.
    - document_ids (list): List of document IDs to update.
    """
    client = MongoClient(mongo_connection)
    db = client[mongo_database]

    neighborhood_coll = db[neighborhood_collection_name]

    if document_ids:
        for key in tqdm(neighborhoods, desc="Updating Document"):
            result = neighborhoods[key]
            # Check if neighborhoods are present before updating
            if result['neighborhoods']:
                neighborhood_coll.update_one({'_id': key}, {
                    '$set': {
                        'neighborhoods': result['neighborhoods'],
                        'unique_terms': result['unique_terms'],
                        'metadata': result['metadata'],
                        'hoods_sequences': result['hoods_sequences'],
                        'hoods_size': result['hoods_size']
                    }
                })
    else:
        # Drop the existing collection if it exists for replacement
        neighborhood_coll.drop()

        # Insert neighborhoods into the collection
        for key in tqdm(neighborhoods, desc="Inserting Neighborhoods"):
            result = neighborhoods[key]
            # Check if neighborhoods are present before inserting
            if result['neighborhoods']:
                neighborhood_coll.insert_one({
                    '_id': key,
                    'neighborhoods': result['neighborhoods'],
                    'unique_terms': result['unique_terms'],
                    'metadata': result['metadata'],
                    'hoods_sequences': result['hoods_sequences'],
                    'hoods_size': result['hoods_size']
                })


def collect_neighborhoods_mongo_parallel(sequences_list, size, document_ids=None, all_collections=False, info=True):
    """
    Collect neighborhoods from MongoDB collections, process them in parallel,
    and insert the results back into the database.

    Parameters:
    - sequences_list (list): List of sequences to process.
    - size (int): Size parameter for processing.
    - document_id (str, optional): ID of a specific document to process. Defaults to None.
    - all_collections (bool, optional): Flag indicating whether to process all 'neighborhoods' collections.
                                       Defaults to False.

    Returns:
    - list: List of processed collections or None if document was not found in any collection.
    """
    import time
    start_time = time.time()  # Record start time

    client = MongoClient(mongo_connection)
    db = client[mongo_database]
    documents_collection = db[mongo_collection]

    collections_names = []

    if all_collections:
        # Get all collections
        all_collections = db.list_collection_names()

        # Iterate over collections
        for collection_name in all_collections:
            if collection_name.endswith('neighborhoods'):
                neighborhoods_collection = db[collection_name]

                # Extract sequences_list and size from one of the documents
                query = {"_id": {"$in": [doc_id for doc_id in document_ids]}}
                collection_info = neighborhoods_collection.find_one(query,
                                                                    {'hoods_sequences': 1, 'hoods_size': 1})

                if collection_info:
                    current_sequences_list = collection_info.get('hoods_sequences', [])
                    current_size = collection_info.get('hoods_size', size)

                    collections_names.append({
                        'collection_name': collection_name,
                        'sequences_list': current_sequences_list,
                        'size': current_size
                    })

    else:
        # Modify collection_suffix based on the presence of whole word sequences
        collection_suffix = '_'.join(
            [f'ww_{seq.strip()[1:-1]}' if seq.strip().startswith('"') and seq.strip().endswith('"') else seq.strip()
             for seq in sequences_list])

        # Create a new collection for neighborhoods
        collections_names = [{'collection_name': f'{collection_suffix}_neighborhoods'}]

    for collection_info in collections_names:
        neighborhood_collection_name = collection_info['collection_name']
        current_sequences_list = collection_info.get('sequences_list', sequences_list)
        current_size = collection_info.get('size', size)

        # Retrieve documents from MongoDB
        if document_ids:
            documents_content = []
            for document_id in document_ids:
                documents_content.append(
                    documents_collection.find_one({'_id': document_id},
                                                  {'_id': 1, 'text': 1, 'metadata': 1}))
                if info:
                    st.info(f"Collecting neighborhoods for document {document_id} "
                            f"on collection {neighborhood_collection_name}...")
                    print(f"Collecting neighborhoods for document {document_id} "
                          f"on collection {neighborhood_collection_name}...")
        else:
            documents_content = list(documents_collection.find({}, {'_id': 1, 'text': 1, 'metadata': 1}))
            st.info("Collecting neighborhoods...")
            print("Collecting neighborhoods...")

        current_sequences_list = [seq.strip() for seq in current_sequences_list]
        # Parallelize processing using ProcessPoolExecutor
        with concurrent.futures.ProcessPoolExecutor() as executor:
            futures = [executor.submit(process_document, document, current_sequences_list, current_size)
                       for document in documents_content]

            neighborhoods = {}

            for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures),
                               desc=f"Processing Documents for collection {neighborhood_collection_name}"):
                key, result, document_metadata, unique_terms = future.result()
                neighborhoods[key] = {
                    'neighborhoods': result,
                    'unique_terms': list(unique_terms),
                    'metadata': document_metadata,
                    'hoods_sequences': current_sequences_list,
                    'hoods_size': current_size
                }
        if info:
            st.success("Finished collecting neighborhoods.")
            print("Finished collecting neighborhoods.")

            st.info(f"Inserting neighborhoods to the collection {neighborhood_collection_name}.")
            print(f"Inserting neighborhoods to the collection {neighborhood_collection_name}.")
        # Insert neighborhoods into MongoDB collection
        insert_neighborhoods_to_mongo(neighborhoods, neighborhood_collection_name, document_ids)
        if info:
            st.success("Finished inserting neighborhoods.")
            print("Finished inserting neighborhoods.")
        end_time = time.time()  # Record end time
        elapsed_time = end_time - start_time
        print(f"Total time taken: {elapsed_time} seconds.")
    if collections_names:
        return collections_names[0]
    else:
        # Maybe a specific document is not in any collection so return None
        return None


def update_neighborhood_in_collection():
    """
    Update the edited neighborhood in the MongoDB collection.
    """
    collection_name = st.session_state.selected_collection
    current_document_id = st.session_state.filtered_keys[st.session_state.docs_count]
    current_neighborhood_index = st.session_state.hoods_count
    edited_text = st.session_state.editor_content

    # Check if the text has been edited
    if (edited_text !=
            st.session_state.filtered_docs[current_document_id]['neighborhoods'][current_neighborhood_index]
            ['neighborhood']):

        # Check if the document has been edited in any other collection or neighborhood
        for edited_doc in st.session_state.edited_documents:
            if edited_doc['Document'] == current_document_id and edited_doc['Collection name'] != collection_name:
                st.session_state.hood_saved = (f"Document {current_document_id} has an edited neighborhood "
                                               f"#{edited_doc['Neighborhood index']} in this collection {edited_doc[
                                                   'Collection name']}. "
                                               f"Please update the corpus before editing another neighborhood from "
                                               f"this document.")

                return  # Stop the update if the document has been edited in another collection or neighborhood
            elif edited_doc['Document'] == current_document_id and edited_doc[
                'Neighborhood index'] != current_neighborhood_index:
                st.session_state.hood_saved = (f"Document {current_document_id} has an edited neighborhood "
                                               f"#{edited_doc['Neighborhood index']} in this collection {edited_doc[
                                                   'Collection name']}. "
                                               f"Please update the corpus before editing another neighborhood from "
                                               f"this document.")

                return  # Stop the update if the document has been edited in another collection or neighborhood

        # Update the MongoDB collection with the edited text
        update_query = {
            '_id': current_document_id,
            'neighborhoods': {
                '$elemMatch': {
                    'start_index': st.session_state.filtered_docs[current_document_id]['neighborhoods'][
                        current_neighborhood_index]['start_index']
                }
            }
        }
        update_operation = {
            '$set': {
                'neighborhoods.$.neighborhood': edited_text,
                'neighborhoods.$.edited': True,
            }
        }

        client = MongoClient(config.mongo_connection)
        db = client[config.mongo_database]
        neighborhood_collection = db[collection_name]

        neighborhood_collection.update_one(update_query, update_operation)
        hoods_docs_index = st.session_state.hoods_docs[current_document_id]['neighborhoods'].index(
            st.session_state.filtered_docs[current_document_id]['neighborhoods'][current_neighborhood_index])
        st.session_state.hoods_docs[current_document_id]['neighborhoods'][hoods_docs_index]['neighborhood'] = \
            edited_text
        st.session_state.hoods_docs[current_document_id]['neighborhoods'][hoods_docs_index]['edited'] = True
        st.session_state.filtered_docs[current_document_id]['neighborhoods'][current_neighborhood_index][
            'neighborhood'] = edited_text
        st.session_state.filtered_docs[current_document_id]['neighborhoods'][current_neighborhood_index][
            'edited'] = True

        # Control if neighbor was successfully saved to show message when rerun
        st.session_state.hood_saved = True
        find_edited_neighborhoods()
    else:
        with st.session_state.col9:
            st.warning("The original text and the text in the text area are the same.")


def save_edited_neighborhoods_to_corpus_mongo(neighborhoods_collection_name):
    """
    Save edited neighborhoods to the corpus collection in MongoDB.

    Parameters:
    - neighborhoods_collection_name (str): Name of the neighborhoods' collection.
    """
    # Connect to MongoDB
    client = MongoClient(config.mongo_connection)
    db = client[config.mongo_database]

    # Access the collections
    corpus_collection = db[config.mongo_collection]
    neighborhoods_collection = db[neighborhoods_collection_name]

    # Retrieve documents from MongoDB, filtering only those with edited neighborhoods
    query = {'neighborhoods': {'$elemMatch': {'edited': True}}}
    neighborhoods_documents = list(neighborhoods_collection.find(query, {'_id': 1, 'neighborhoods': 1}))

    # Create an update list to store all updates
    update_list = []

    # Iterate through neighborhoods and update corpus
    for neighborhoods_doc in neighborhoods_documents:
        document_id = neighborhoods_doc['_id']
        neighborhoods = neighborhoods_doc.get('neighborhoods', [])
        # Use MongoDB query to filter only documents with edited neighborhoods
        corpus_document = corpus_collection.find_one({'_id': document_id, 'text': {'$exists': True}})
        if corpus_document:
            tokenized_content = tokenize(corpus_document['text'])
            updated_content = tokenized_content  # Create a copy of tokenized_content

            for neighborhood in neighborhoods:
                if neighborhood['edited']:
                    start_index = neighborhood['start_index']
                    end_index = neighborhood['end_index']
                    updated_content[start_index:end_index] = tokenize(neighborhood['neighborhood'])
                    # Mark neighborhood as not edited anymore
                    neighborhood['edited'] = False

            update_list.append({
                'filter': {'_id': document_id},
                'update': {'$set': {'text': ' '.join(updated_content)}}
            })

        # Update the neighborhoods_collection
        neighborhoods_collection.update_one({'_id': document_id},
                                            {'$set': {'neighborhoods': neighborhoods}})

    # Update the corpus_collection with a single update operation
    for update_operation in update_list:
        corpus_collection.update_one(**update_operation)
    find_edited_neighborhoods()


def find_edited_neighborhoods():
    """
    Finds and populates the edited_documents session state variable with information about edited neighborhoods.
    """
    # Connect to MongoDB
    client = MongoClient(config.mongo_connection)
    db = client[config.mongo_database]

    # Initialize session state variables as a list
    st.session_state.edited_documents = []

    # Get all collections
    all_collections = db.list_collection_names()

    # Iterate over collections
    for collection_name in all_collections:
        if collection_name.endswith('neighborhoods'):
            neighborhoods_collection = db[collection_name]

            # Search for neighborhoods with 'edited' True
            query = {'neighborhoods': {'$elemMatch': {'edited': True}}}
            edited_neighborhoods = neighborhoods_collection.find(query, {'_id': 1, 'neighborhoods': 1})

            # Iterate over documents with edited neighborhoods
            for doc in edited_neighborhoods:
                document_id = doc['_id']
                neighborhoods = doc.get('neighborhoods', [])

                # Iterate over neighborhoods
                for idx, neighborhood in enumerate(neighborhoods):
                    if neighborhood['edited']:
                        # Append information to the session state list
                        st.session_state.edited_documents.append({
                            'Document': document_id,
                            'Neighborhood index': idx,
                            'Collection name': collection_name
                        })
                        break  # Stop searching after finding the first edited neighborhood


def add_correction_entry_to_mongo(original_term, corrected_term):
    """
    Adds a new entry to the corrections collection in MongoDB.

    Parameters:
    - original_term (str): The original term to be corrected.
    - corrected_term (str): The corrected term.
    """
    client = MongoClient(mongo_connection)
    db = client[mongo_database]
    corrections_collection = db[corrections_collection_name]

    existing_entry = corrections_collection.find_one({"Original term": original_term})

    if existing_entry:
        st.warning(f"Entry for term '{original_term}' already exists.")
    elif len(original_term) == 0 or original_term.isspace():
        st.warning("You can't add an empty original term.")
    else:
        new_entry = {"Original term": original_term, "Correct term": corrected_term}
        corrections_collection.insert_one(new_entry)
        st.success("Entry added successfully!")

    client.close()


def delete_correction_entry_from_mongo(selected_entry):
    """
    Deletes a selected entry from the corrections collection in MongoDB.

    Parameters:
    - selected_entry (str): The original term of the entry to be deleted.
    """
    client = MongoClient(mongo_connection)
    db = client[mongo_database]
    corrections_collection = db[corrections_collection_name]

    if selected_entry:
        corrections_collection.delete_one({"Original term": selected_entry})
        st.success("Entry deleted successfully!")
    else:
        st.warning("Choose a valid entry from the dropdown.")

    client.close()


def get_corrections_from_mongo():
    """
    Retrieves corrections from the corrections collection in MongoDB.

    Returns:
    - pd.DataFrame: DataFrame containing corrections data.
    """
    client = MongoClient(mongo_connection)
    db = client[mongo_database]
    corrections_collection = db[corrections_collection_name]

    # Fetch corrections and convert to DataFrame
    corrections_data = list(corrections_collection.find())
    corrections_df = pd.DataFrame(corrections_data, columns=['Original term', 'Correct term'])

    client.close()

    return corrections_df


def apply_corrections_to_document(document, corrections_dict):
    """
    Applies corrections to the 'text' field of a document based on a corrections' dictionary.

    Parameters:
    - document (dict): The document to apply corrections to.
    - corrections_dict (dict): Dictionary mapping original terms to corrected terms.

    Returns:
    - dict or None: If corrections are applied, returns a dictionary with the updated document, else returns None.
    """
    if 'text' in document:
        # For the general collection
        tokenized_text = tokenize(document['text'])

        # Apply the corrections using set intersection
        corrected_tokens = [corrections_dict.get(token, token) for token in tokenized_text]

        # Save the updated text back to the JSON data
        corrected_document = ' '.join(corrected_tokens)
        if corrected_tokens != tokenized_text:
            corrected_doc = {'_id': document['_id'], 'text': corrected_document}
            return corrected_doc
    else:
        print(f"Unknown document structure for document {document}. Skipping corrections.")
        return None


def apply_corrections_all_collections_mongo_parallel(corrections_df):
    """
    Applies corrections from a DataFrame to all documents in the MongoDB collection in parallel.

    Parameters:
    - corrections_df (pandas.DataFrame): DataFrame containing 'Original term' and 'Correct term' columns.
    """
    client = MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    corrections_dict = dict(zip(corrections_df['Original term'], corrections_df['Correct term']))

    collection = db[config.mongo_collection]

    st.info(f"Applying corrections to collection {config.mongo_collection}. Please wait, this might take a while.")
    print(f"Applying corrections to collection {config.mongo_collection}. Please wait, this might take a while.")

    futures = []
    documents_ids = []

    executor = concurrent.futures.ProcessPoolExecutor()

    for document in collection.find():
        future = executor.submit(apply_corrections_to_document, document, corrections_dict)
        futures.append(future)

    for i, future in enumerate(concurrent.futures.as_completed(futures)):
        result = future.result()
        if result is not None:
            collection.update_one({'_id': result['_id']}, {'$set': result})
            documents_ids.append(result['_id'])

    print(f"Finished applying all corrections.")
    st.info(f"Corrections applied to collection {config.mongo_collection}.")

    st.success(f"Finished applying all corrections.")

    print(documents_ids)
    collect_neighborhoods_mongo_parallel(sequences_list=[], size=0, document_ids=documents_ids,
                                         all_collections=True, info=False)


def save_complete_text_to_mongo():
    """
    Saves the complete text of a document to MongoDB.
    """
    document_id = st.session_state.complete_file_to_display
    client = MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    documents_collection = db[config.mongo_collection]

    text_to_save = st.session_state.editor_content

    # Fetch the document from MongoDB
    document = documents_collection.find_one({"_id": document_id})

    if document:
        # Update the text field in the document
        documents_collection.update_one(
            {"_id": document_id},
            {"$set": {"text": text_to_save}}
        )
        with st.session_state.col8:
            st.success(f"Text successfully saved for document {document_id}.")
    else:
        with st.session_state.col8:
            st.error(f"Document {document_id} not found in collection {config.mongo_collection}.")

    # Recollect and insert the neighborhoods of the saved document
    with st.session_state.col8:
        st.info('Recollecting neighborhoods from edited documents.')
        collect_neighborhoods_mongo_parallel(sequences_list=[], size=0, document_ids=[document_id], all_collections=True)
        st.success('Finished recollecting neighborhoods successfully.')


def get_neighborhood_collections():
    """
    Retrieves neighborhood collections from MongoDB.

    Returns:
    - list: A list of neighborhood collection names.
    """
    client = MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    collection_names = db.list_collection_names()
    neighborhood_collections = [name for name in collection_names if name.endswith("_neighborhoods")]
    return neighborhood_collections


def get_documents_from_collection(collection_name):
    """
    Retrieves documents from a specified MongoDB collection.

    Parameters:
    - collection_name (str): The name of the MongoDB collection.

    Returns:
    - dict: A dictionary where keys are document IDs, and values are the corresponding document content.
    """
    client = MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    collection = db[collection_name]
    documents_content = list(collection.find({}))
    documents_dict = {str(doc['_id']): doc for doc in documents_content}
    return documents_dict


def get_corrections_from_collection():
    """
    Retrieves corrections from the corrections MongoDB collection.

    Returns:
    - pymongo.collection.Collection: The corrections MongoDB collection.
    """
    client = MongoClient(config.mongo_connection)
    database = client[config.mongo_database]
    corrections_collection = database[corrections_collection_name]
    return corrections_collection


def get_complete_text_from_document(document_id):
    """
    Retrieves the complete text of a document from MongoDB.

    Parameters:
    - document_id (str): The unique identifier of the document.

    Returns:
    - dict: The document content, including the complete text.
    """
    client = MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    documents_collection = db[config.mongo_collection]
    # Fetch the document from MongoDB
    document = documents_collection.find_one({"_id": document_id})
    return document
