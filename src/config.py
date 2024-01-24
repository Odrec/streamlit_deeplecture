from pathlib import Path

NEIGHBORHOODS_DIR = Path("json/neighborhoods")
JSON_DIR = Path("json/")
CSV_DIR = Path("csv/")
PDF_DIR = Path("/home/odrec/Documents/Korpus PDFs/")

mongo_connection = 'mongodb://localhost:27017/'
mongo_database = 'deeplecture'
mongo_collection = 'corrected_all_text_data'
corrections_collection_name = 'corrections'

neighborhoods_size = 100
co_occurrence_neighborhood_size = 11


