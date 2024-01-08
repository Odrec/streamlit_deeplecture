import json
from pathlib import Path
from config import JSON_DIR, CSV_DIR, mongo_connection, mongo_database
import utils
import gzip
from pymongo import MongoClient
import csv
import pandas as pd
import data_utils


def add_num_pages(name_file_no_num_pages, name_file_num_pages):
    file_no_num_pages_path = Path('../json/', name_file_no_num_pages)
    file_num_pages_path = Path('../json/', name_file_num_pages)
    no_num_pages_data = utils.open_json_data_gzipped(file_no_num_pages_path)
    num_pages_data = utils.open_json_data_gzipped(file_num_pages_path)

    for key, content in num_pages_data.items():
        no_num_pages_data[key] = {'text': no_num_pages_data[key], 'num_pages': content['num_pages']}

    utils.save_json_data_gzipped(file_no_num_pages_path, no_num_pages_data)


def zip_data(json_file_name):
    file_path = Path('../json/', json_file_name)
    data = utils.open_json_data_file(file_path)

    # Save the JSON content to a gzipped file
    gzipped_file_path = file_path.parent / Path(str(file_path.name) + ".gz")
    with gzip.open(gzipped_file_path, "wt", encoding="utf-8") as gzipped_file:
        json.dump(data, gzipped_file)

    return gzipped_file_path


def add_quality_info(metadata_dict, quality_file_path):
    with open(quality_file_path, 'r') as quality_file:
        quality_reader = csv.DictReader(quality_file)
        for row in quality_reader:
            key = row['document']  # Assuming 'Document' is the key matching 'codigo'
            quality = row['quality_all']
            metadata_dict[key]['quality'] = quality
    return metadata_dict


def add_whole_corpus_to_mongo_db(gzipped_file_path, metadata_file_name, collection, quality_file_name=None):
    # Read the gzipped file
    with gzip.open(gzipped_file_path, "rt", encoding="utf-8") as gzipped_file:
        json_content = json.load(gzipped_file)

    # Read CSV data
    metadata_dict = {}
    with open(Path('../csv/', metadata_file_name), 'r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        for row in csv_reader:
            key = row['codigo']
            metadata_dict[key] = {k: v for k, v in row.items() if k.lower() != 'codigo' and k.lower() != 'unnamed: 0'}
            metadata_dict[key]['num_pages'] = json_content[key]['num_pages']

    if quality_file_name:
        quality_file_path = Path('../csv/', quality_file_name)
        metadata_dict = add_quality_info(metadata_dict, quality_file_path)

    client = MongoClient(mongo_connection)
    db = client[mongo_database]
    collection = db[collection]

    for key, text_content in json_content.items():
        document = {
            '_id': key,
            'text': text_content['text'],
            'metadata':
                metadata_dict.get(key, {})
        }
        collection.insert_one(document)


def search_term(search_term="taturaleza"):
    client = MongoClient(mongo_connection)
    db = client[mongo_database]
    collection = db["neighborhoods_naturaleza"]

    # Construct a query using $elemMatch to search in all neighborhoods of all documents
    query = {
        "neighborhoods.neighborhood": {"$regex": search_term, "$options": "i"}
    }

    # Find documents matching the query
    matching_documents = collection.find(query)

    # Iterate over matching documents
    for document in matching_documents:
        print("Matching Document:")
        print(document['_id'])  # Assuming '_id' is the document name field

        # Loop through neighborhoods in the matching document
        for neighborhood in document['neighborhoods']:
            if "neighborhood" in neighborhood and \
                    search_term.lower() in neighborhood["neighborhood"].lower():
                print("Found in neighborhood:")
                print(neighborhood["neighborhood"])
                print("Text of the neighborhood:")
                print(neighborhood.get("text", "No text available"))
                print("\n")


def add_corrections_to_mongo(corrections_file_name):
    corrections_file_path = data_utils.keep_corrections_csv_clean(corrections_file_name)

    corrections_file_name = corrections_file_path.name

    # Read CSV file into a DataFrame
    df = pd.read_csv(Path('../csv/', corrections_file_name), names=['Original term', 'Correct term'])

    # Connect to MongoDB
    client = MongoClient(mongo_connection)  # Replace 'your_mongodb_uri' with your MongoDB connection URI
    db = client[mongo_database]  # Specify the database

    # Create or get the corrections collection
    corrections_collection = db['corrections']

    # Convert DataFrame to a list of dictionaries (each row as a dictionary)
    corrections_data = df.to_dict(orient='records')

    # Insert the data into the MongoDB collection
    corrections_collection.insert_many(corrections_data)


files_names = ["all_extracted_text_2023_corrected_all.json", "all_extracted_text_2023.json"]
gzipped_files_names = ["all_extracted_text_2023_corrected_all.json.gz", "all_extracted_text_2023.json.gz"]
corrections_file_name = "corrections.csv"
#gzipped_file_path = zip_data(files_names[0])
#add_num_pages(gzipped_files_names[0], gzipped_files_names[1])
collections = ['corrected_all_text_data', 'ocr_raw_text_data']
metadata_file_name = 'metadata_quality.csv'
quality_file_name = ['quality_comparison.csv', None]
#add_corrections_to_mongo(corrections_file_name)
# search_term()
add_whole_corpus_to_mongo_db(Path('../json/', gzipped_files_names[0]), metadata_file_name, collections[0], quality_file_name=quality_file_name[0])
