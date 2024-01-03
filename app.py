import pandas as pd
import streamlit as st
from htmlTemplates import css
from src import config
from src import data_utils
from pathlib import Path
import os
import subprocess
import pymongo


def next_hood():
    if st.session_state.hoods_count + 1 >= len(
            st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]]['neighborhoods']):
        st.session_state.hoods_count = 0
    else:
        st.session_state.hoods_count += 1


def previous_hood():
    if st.session_state.hoods_count > 0:
        st.session_state.hoods_count -= 1
    else:
        st.session_state.hoods_count = (len(
            st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]]['neighborhoods'])
                                        - 1)


def next_doc():
    if st.session_state.docs_count + 1 >= len(st.session_state.filtered_docs):
        st.session_state.docs_count = 0
    else:
        st.session_state.docs_count += 1
    st.session_state.hoods_count = 0
    st.session_state.doc_selectbox = None  # Reset the selectbox


def previous_doc():
    if st.session_state.docs_count > 0:
        st.session_state.docs_count -= 1
    else:
        st.session_state.docs_count = len(st.session_state.filtered_docs) - 1
    st.session_state.hoods_count = 0
    st.session_state.doc_selectbox = None  # Reset the selectbox


def apply_filters_to_neighborhoods():
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

    st.session_state.filters = ""
    # Apply term filter do the documents
    if st.session_state.filter_by_term != "":
        filtered_by_term_dict = {}
        for doc_id, doc in st.session_state.filtered_docs.items():
            for hood in doc.get('neighborhoods', []):
                if st.session_state.filter_by_term in hood['neighborhood']:
                    if doc_id not in filtered_by_term_dict:
                        filtered_by_term_dict[doc_id] = {'neighborhoods': []}
                    filtered_by_term_dict[doc_id]['neighborhoods'].append(hood)
        st.session_state.filtered_docs = filtered_by_term_dict
        st.session_state.filters += f"**Term** - {st.session_state.filter_by_term} "

    st.session_state.filtered_keys = list(st.session_state.filtered_docs.keys())
    st.session_state.docs_count = 0
    st.session_state.hoods_count = 0
    if 'selected_periodo' in st.session_state and st.session_state.selected_periodo:
        st.session_state.filters += f"**Periodos** - {' '.join(st.session_state.selected_periodo)} "
    if 'selected_entidad_territorial' in st.session_state and st.session_state.selected_entidad_territorial:
        st.session_state.filters += (f"**Entidad Territorial** - "
                                     f"{' '.join(st.session_state.selected_entidad_territorial)} ")
    if 'selected_nacionalidad' in st.session_state and st.session_state.selected_nacionalidad:
        st.session_state.filters += f"**Nacionalidad** - " + ' '.join(st.session_state.selected_nacionalidad)


def clear_filters():
    if 'hoods_docs' in st.session_state:
        st.session_state.docs_count = 0
        st.session_state.hoods_count = 0
        st.session_state.selected_nacionalidad = []
        st.session_state.selected_entidad_territorial = []
        st.session_state.selected_periodo = []
        st.session_state.filtered_docs = st.session_state.hoods_docs.copy()
        st.session_state.filtered_keys = list(st.session_state.filtered_docs.keys())
        st.session_state.filters = None
        st.session_state.filter_by_term = ""


def clear_filters_on_file_change():
    clear_filters()


def change_selectbox_value(new_file):
    st.session_state.selected_hoods_file = new_file
    st.session_state.selected_hoods_file_name = new_file.name
    st.rerun()


def open_pdf_button():
    pdf_file_name = st.session_state.filtered_keys[st.session_state.docs_count]
    pdf_file_path = os.path.join(config.PDF_DIR, f"{pdf_file_name}.pdf")

    if os.path.exists(pdf_file_path):
        with st.session_state.col9:
            st.success(f"Opening PDF: {pdf_file_name}.pdf")
            subprocess.run(["xdg-open", pdf_file_path])
    else:
        with st.session_state.col9:
            st.warning(f"PDF file not found: {pdf_file_path}")


def display_complete_text(text_area_container, document_id):
    client = pymongo.MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    documents_collection = db[config.mongo_collection]
    # Fetch the document from MongoDB
    document = documents_collection.find_one({"_id": document_id})

    if document:
        # Access the text field you want to display
        text_to_display = document.get("your_text_field_name", "")

        # Define a unique key for the text_area widget
        widget_key = f"hood_text_area_{document_id}"

        text_area_container.text_area(
            f"Complete text from document {document_id} on collection **{config.mongo_collection}**.",
            value=text_to_display,
            height=300,
            key=widget_key,
            disabled=st.session_state.disabled
        )
    else:
        text_area_container.text(f"Document {document_id} not found in collection {config.mongo_collection}.")


def display_collection_hoods(text_area_container):
    if 'filtered_keys' in st.session_state:
        current_document_id = st.session_state.filtered_keys[st.session_state.docs_count]
        current_document = st.session_state.filtered_docs[current_document_id]
        current_metadata = current_document['metadata']
        current_hood = current_document['neighborhoods'][st.session_state.hoods_count]

        quality_percentage = float(current_metadata['quality'])
        number_of_words = current_metadata['doc_total_words']
        num_pages = current_metadata['num_pages']
        text = current_hood['neighborhood']
        start_index = current_hood['start_index']
        end_index = current_hood['end_index']
        edited = current_hood['edited']
        updated = current_hood['updated']

        hoods_terms = ""
        for i, term in enumerate(st.session_state.hoods_term):
            if term == 'ww':
                hoods_terms += st.session_state.hoods_term[i + 1] + " (ww)"
                if i + 1 == len(st.session_state.hoods_term) - 1:
                    break
            else:
                hoods_terms += term
            if i != len(st.session_state.hoods_term) - 1:
                hoods_terms += ', '

        average_words_per_page = int(number_of_words) / int(num_pages)
        aprox_page_hood = int(start_index / average_words_per_page)
        text_area_container.text_area(f'Neighborhood {st.session_state.hoods_count} from '
                                      f'{len(current_document['neighborhoods']) - 1}'
                                      f' for **{hoods_terms}**'
                                      f' in document **{current_document_id}** '
                                      f'(SI: {start_index} EI: {end_index} Q%: {quality_percentage: .2g}'
                                      f' #W: {int(number_of_words)} #Pags. {int(num_pages)}) '
                                      f'on collection **{st.session_state.selected_collection}**. '
                                      f'Manually edited: **{"Yes" if edited else "No"}**. '
                                      f'Updated in corpus **{"Yes" if updated else "No"}**. '
                                      f'Aprox. page # the neighborhood is at: **{aprox_page_hood + 1}**.',
                                      value=text, height=300, key="hood_text_area",
                                      disabled=st.session_state.disabled)
        st.write(f'Total documents: {len(st.session_state.filtered_keys)}. Total neighborhoods: '
                 f'{sum(len(value['neighborhoods']) if isinstance(value['neighborhoods'], list) else 0
                        for value in st.session_state.filtered_docs.values())}. '
                 f'Applied filters: {st.session_state.filters}')
    else:
        text_area_container.text_area(label="No neighborhoods found.",
                                      value="",
                                      height=300)
        st.write(f'Total documents: 0. Total neighborhoods: 0. Applied filters: {st.session_state.filters}')


def disable_widgets():
    st.session_state.disabled = True


def get_neighborhood_collections():
    client = pymongo.MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    collection_names = db.list_collection_names()
    neighborhood_collections = [name for name in collection_names if name.startswith("neighborhoods_")]
    return neighborhood_collections


def get_documents_from_collection(collection_name):
    client = pymongo.MongoClient(config.mongo_connection)
    db = client[config.mongo_database]
    collection = db[collection_name]
    documents_content = list(collection.find({}))
    documents_dict = {str(doc['_id']): doc for doc in documents_content}
    return documents_dict


def main():
    st.set_page_config(layout="wide", page_title='Explore And Manage Your Corpus', page_icon=':books:')
    st.write(css, unsafe_allow_html=True)
    st.header('Explore And Manage Your Corpus :books:')

    metadata_quality = pd.read_csv(Path(config.CSV_DIR, 'metadata_quality.csv'))

    if 'disabled' not in st.session_state:
        st.session_state.disabled = False

    if 'docs_count' not in st.session_state:
        st.session_state.docs_count = 0

    if 'previous_selectbox_value' not in st.session_state:
        st.session_state.previous_selectbox_value = None

    if 'selected_collection' not in st.session_state:
        st.session_state.selected_collection = "No Neighborhoods"

    with (st.sidebar):
        st.write("**NEIGHBORHOOD COLLECTIONS:**")

        # Fetch neighborhood collections from MongoDB
        neighborhood_collections = get_neighborhood_collections()

        if neighborhood_collections:
            # Create a list of names for display
            if st.session_state.selected_collection is None or st.session_state.selected_collection not in neighborhood_collections:
                st.session_state.selected_collection = neighborhood_collections[0]
        else:
            # If no neighborhood collections exist
            neighborhood_collections = ["No Neighborhoods"]

        selected_collection = st.selectbox("Select a collection to display the neighborhoods",
                                           neighborhood_collections,
                                           on_change=clear_filters_on_file_change,
                                           index=neighborhood_collections.index(st.session_state.selected_collection),
                                           disabled=st.session_state.disabled)

        st.session_state.selected_collection = selected_collection

        # TODO: Is this necessary??
        if selected_collection != st.session_state.selected_collection:
            change_selectbox_value(selected_collection)

        st.markdown("""---""")  # Horizontal Separator

        st.write("**COLLECT NEIGHBORHOODS:**")

        col3_sb, col4_sb = st.columns([1, 1])

        # Input fields for generating new neighborhoods
        create_hood_term = col3_sb.text_input("Enter term(s) to collect new neighborhoods (sep ,):",
                                              disabled=st.session_state.disabled)
        create_hood_size = col4_sb.number_input("Enter the size of the new neighborhoods (default 100):", value=100,
                                                step=1, disabled=st.session_state.disabled)
        # Generate New Neighborhoods Button
        collect_neighborhoods_button = st.button("Collect Neighborhoods", on_click=disable_widgets,
                                                 disabled=st.session_state.disabled)
        if collect_neighborhoods_button:
            if create_hood_term == "":
                st.warning("Please specify a term to collect the neighborhoods.")
            else:
                if create_hood_size == "":
                    create_hood_size = 100
                sequences = create_hood_term.split(',')
                with st.spinner(f'Collecting neighborhoods for terms "{create_hood_term}". '
                                f'This might take a while. Please wait...'):
                    data_utils.collect_neighborhoods_mongo_parallel(sequences_list=sequences, size=create_hood_size)
                    st.success("Neighborhoods collected successfully.")
                    st.session_state.disabled = False
                    # In case the same neighborhoods that are being displayed are regenerated
                    st.session_state.docs_count = 0
                    st.session_state.hoods_count = 0
                    st.rerun()

        st.markdown("""---""")  # Horizontal Separator

        if 'filters' not in st.session_state:
            st.session_state.filters = None
        st.write("**FILTERS:**")

        # Extract unique values for each metadata field
        unique_periodo_values = set()
        unique_nacionalidad_values = set()
        unique_entidad_territorial_values = set()

        if 'hoods_docs' in st.session_state:
            for doc_id, doc in st.session_state.hoods_docs.items():
                metadata = doc.get('metadata', {})
                unique_periodo_values.update(metadata.get('periodo', []))
                unique_nacionalidad_values.update(metadata.get('nacionalidad', []))
                unique_entidad_territorial_values.update(metadata.get('entidad territorial', []))

        # Add multiselect filters
        st.session_state.selected_periodo = st.multiselect("Select Periodo",
                                                           sorted(unique_periodo_values),
                                                           key="filter_periodo", disabled=st.session_state.disabled)
        # Replace NaN with "None" in the 'nacionalidad' column
        metadata_quality['nacionalidad'] = metadata_quality['nacionalidad'].fillna("Sin nacionalidad")
        st.session_state.selected_nacionalidad = st.multiselect("Select Nacionalidad",
                                                                sorted(unique_nacionalidad_values),
                                                                disabled=st.session_state.disabled)
        st.session_state.selected_entidad_territorial = st.multiselect("Select Entidad Territorial",
                                                                       sorted(unique_entidad_territorial_values),
                                                                       disabled=st.session_state.disabled)

        # Input fields for original and corrected terms
        st.session_state.filter_by_term = st.text_input("Filter by term:", disabled=st.session_state.disabled)

        col1_sb, col2_sb = st.columns([1, 1])

        if col1_sb.button("Apply Filters", disabled=st.session_state.disabled):
            apply_filters_to_neighborhoods()
        # Clear Filters Button
        if col2_sb.button("Clear Filters", disabled=st.session_state.disabled):
            clear_filters()

        if not st.session_state.filters and selected_collection and selected_collection != 'No Neighborhoods':
            # Retrieve documents from MongoDB
            st.session_state.hoods_docs = get_documents_from_collection(selected_collection)

            # Filter out keys with empty values
            st.session_state.hoods_docs = dict(sorted(st.session_state.hoods_docs.items(), key=lambda x: x[0]))
            st.session_state.filtered_docs = st.session_state.hoods_docs.copy()

            st.session_state.hoods_term = [term.strip() for term in selected_collection.split('_')[1:]]

            st.session_state.filtered_keys = list(st.session_state.filtered_docs.keys())

        if 'hoods_count' not in st.session_state:
            st.session_state.hoods_count = 0

    col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])

    with col1:
        if st.button("⏮️ Previous Neighborhood", on_click=previous_hood, disabled=st.session_state.disabled):
            pass

    with col2:
        if st.button("Next Neighborhood ⏭️", on_click=next_hood, disabled=st.session_state.disabled):
            pass

    with col3:
        if st.button("⏮️ Previous Document", on_click=previous_doc, disabled=st.session_state.disabled):
            pass

    with col4:
        if st.button("Next Document ⏭️", on_click=next_doc, disabled=st.session_state.disabled):
            pass

    with col5:
        if 'filtered_keys' in st.session_state:
            selectbox_doc = st.selectbox(label='Choose a document to navigate to',
                                         options=st.session_state.filtered_keys, key='doc_selectbox', index=None,
                                         disabled=st.session_state.disabled)
        else:
            selectbox_doc = st.selectbox(label='Choose a document to navigate to', key='doc_selectbox', options=[],
                                         disabled=st.session_state.disabled)

        if selectbox_doc and selectbox_doc != st.session_state.previous_selectbox_value:
            # TODO: Check behavior of dropbox after applying corrections.
            st.session_state.docs_count = st.session_state.filtered_keys.index(selectbox_doc)
            st.session_state.hoods_count = 0
            # Save the value to control when value changes in the condition
            st.session_state.previous_selectbox_value = selectbox_doc

    text_area_container = st.empty()
    display_collection_hoods(text_area_container)

    tab1, tab2 = st.tabs(["Edition", "Coocurrences", ])

    with tab1:
        col6, col7, col8, st.session_state.col9 = st.columns([1, 1, 1, 1])

        corrections_file_name = 'corrections.csv'
        corrections_file_path = data_utils.keep_corrections_csv_clean(corrections_file_name)

        # Read CSV without column names
        corrections_df = pd.read_csv(corrections_file_path, header=None)

        # Add column names
        corrections_df.columns = ["Original term", "Corrected term"]

        with col7:
            st.subheader("Add/Delete entries")

            # Display label for the dataframe
            st.markdown("**Add entry to the corrections list**")

            # Input fields for original and corrected terms
            original_term = st.text_input("Original Term:", disabled=st.session_state.disabled)
            corrected_term = st.text_input("Corrected Term:", disabled=st.session_state.disabled)

            # Button to add entry
            if st.button("Add Entry", disabled=st.session_state.disabled):
                if original_term in corrections_df["Original term"].values:
                    st.warning(f"Entry for term '{original_term}' already exists.")
                elif len(original_term) == 0 or original_term.isspace():
                    st.warning("You can't add an empty original term.")
                else:
                    new_entry = {"Original term": original_term, "Corrected term": corrected_term}
                    corrections_df = corrections_df._append(new_entry, ignore_index=True)
                    # Save the updated DataFrame to CSV
                    corrections_df.to_csv(corrections_file_path, index=False, header=False)
                    st.success("Entry added successfully!")

            # Dropdown to select the entry to delete
            selected_entry = st.selectbox("**Select entry to delete from the corrections list**",
                                          corrections_df["Original term"].tolist(), index=None,
                                          key="delete_dropdown", disabled=st.session_state.disabled)

            # Button to delete entry
            delete_entry_button = st.button("Delete Entry", disabled=st.session_state.disabled)
            if delete_entry_button:
                if selected_entry:
                    corrections_df = corrections_df[corrections_df["Original term"] != selected_entry]
                    # Save the updated DataFrame to CSV
                    corrections_df.to_csv(corrections_file_path, index=False, header=False)
                    st.success("Entry deleted successfully!")
                else:
                    st.warning("Choose a valid entry from the dropdown.")

        with col8:
            # Button to display the entire text of the current document
            display_complete_text_button = st.button("Display complete text", disabled=st.session_state.disabled)
            if display_complete_text_button:
                display_complete_text(text_area_container, st.session_state.filtered_keys[st.session_state.docs_count])

        with st.session_state.col9:

            # Show success message if neighborhood was saved successfully
            if 'hood_saved' in st.session_state:
                if st.session_state.hood_saved:
                    st.success(f"Neighborhood {st.session_state.hoods_count} from file "
                               f"{st.session_state.filtered_keys[st.session_state.docs_count]} saved successfully.")
                    st.session_state.hood_saved = False
            else:
                st.session_state.hood_saved = False

            # Check if "Save" button is clicked and save changes
            st.button("Save changes in neighborhood", disabled=st.session_state.disabled,
                      on_click=data_utils.update_neighborhood_in_collection)

            # Add a button to open the PDF
            if 'filtered_keys' in st.session_state:
                st.button(f"Open PDF for file {st.session_state.filtered_keys[st.session_state.docs_count]}",
                          on_click=open_pdf_button, disabled=st.session_state.disabled)

                not_updated_hoods_dict = {}

                for file, neighborhoods in st.session_state.hoods_docs.items():
                    for i, neighborhood in enumerate(neighborhoods['neighborhoods']):
                        if neighborhood['edited'] and not neighborhood['updated']:
                            if file in not_updated_hoods_dict:
                                not_updated_hoods_dict[file]['Neighborhoods'] += f', {i}'
                            else:
                                not_updated_hoods_dict[file] = {'File': file, 'Neighborhoods': str(i)}

                # Convert the dictionary values to a list
                not_updated_hoods_list = list(not_updated_hoods_dict.values())

                if 'updated' in st.session_state:
                    if st.session_state.updated:
                        st.success("Corpus updated successfully.")
                        st.info("Regenerate the neighborhoods to ensure consistency with the corpus indexes.")
                        st.session_state.updated = False
                else:
                    st.session_state.updated = False

                # Only display the not updated files if there have been editions saved
                if not_updated_hoods_list:
                    st.write("**Edited neighborhoods list (not updated in corpus)**")

                    not_updated_hoods_df = pd.DataFrame(not_updated_hoods_list)

                    # Display table
                    st.dataframe(not_updated_hoods_df, height=300)

                    update_neighborhoods_in_corpus_button = st.button(f"Update edited neighborhoods in corpus",
                                                                      on_click=disable_widgets,
                                                                      disabled=st.session_state.disabled)

                    if update_neighborhoods_in_corpus_button:
                        data_utils.save_edited_neighborhoods_to_corpus(st.session_state.complete_corpus_file_name,
                                                                       st.session_state.selected_hoods_file_name)
                        st.session_state.updated = True
                        st.session_state.disabled = False
                        st.rerun()

        with col6:

            st.subheader("Corrections list")

            # Display table below the textarea
            st.dataframe(corrections_df, height=300)

            apply_corrections_button = st.button("Apply corrections to the entire corpus and neighborhoods",
                                                 key="apply_corrections_button", on_click=disable_widgets,
                                                 disabled=st.session_state.disabled)

            if apply_corrections_button:
                with st.spinner("Applying corrections. Please wait..."):
                    data_utils.apply_corrections_all_collections(corrections_df, neighborhood_collections)
                    st.success("Corrections applied successfully.")
                    st.session_state.disabled = False
                    st.rerun()


if __name__ == '__main__':
    main()
