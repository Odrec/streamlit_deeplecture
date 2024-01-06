import pandas as pd
import streamlit as st
from htmlTemplates import css
from src import config
from src import data_utils
import os
import subprocess
import pymongo
from src import control_widgets as cw


def initialize_session_document_variables(selected_collection):
    # Retrieve documents from MongoDB
    st.session_state.hoods_docs = get_documents_from_collection(selected_collection)

    # Filter out keys with empty values
    st.session_state.hoods_docs = dict(sorted(st.session_state.hoods_docs.items(), key=lambda x: x[0]))
    st.session_state.filtered_docs = st.session_state.hoods_docs.copy()

    st.session_state.hoods_term = [term.strip() for term in selected_collection.split('_')[1:]]

    st.session_state.filtered_keys = list(st.session_state.filtered_docs.keys())
    cw.enable_all_widgets()  # In case they were disabled for any reason


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
    cw.enable_neighborhoods_widgets()
    if st.session_state.docs_count + 1 >= len(st.session_state.filtered_docs):
        st.session_state.docs_count = 0
    else:
        st.session_state.docs_count += 1
    st.session_state.hoods_count = 0
    st.session_state.doc_selectbox = None  # Reset the selectbox


def previous_doc():
    cw.enable_neighborhoods_widgets()
    st.session_state.complete_text = False
    if st.session_state.docs_count > 0:
        st.session_state.docs_count -= 1
    else:
        st.session_state.docs_count = len(st.session_state.filtered_docs) - 1
    st.session_state.hoods_count = 0
    st.session_state.doc_selectbox = None  # Reset the selectbox


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
    # enable_complete_text_widgets()
    st.session_state.selected_hoods_file = new_file
    # st.rerun()


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
        text_to_display = document.get("text", "")

        # Define a unique key for the text_area widget
        widget_key = f"text_area_{document_id}"

        text_area_container.text_area(
            f"Complete text from document {document_id} on collection **{config.mongo_collection}**.",
            value=text_to_display,
            height=300,
            key=widget_key,
            disabled=st.session_state.disabled
        )
    else:
        text_area_container.text(f"Document {document_id} not found in collection {config.mongo_collection}.")


def display_collection_hoods(text_area_container, selected_collection):
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

        hoods_terms = []
        skip_next = False
        for i, term in enumerate(st.session_state.hoods_term):
            if skip_next:
                skip_next = False
                continue

            if term == 'ww':
                if i + 1 < len(st.session_state.hoods_term):
                    hoods_terms.append(st.session_state.hoods_term[i + 1] + " (ww)")
                    skip_next = True
            else:
                hoods_terms.append(term)
        hoods_terms_string = ','.join(hoods_terms)

        average_words_per_page = int(number_of_words) / int(num_pages)
        aprox_page_hood = int(start_index / average_words_per_page)
        text_area_container.text_area(f'Neighborhood {st.session_state.hoods_count} from '
                                      f'{len(current_document['neighborhoods']) - 1}'
                                      f' for **{hoods_terms_string}**'
                                      f' in document **{current_document_id}** '
                                      f'(SI: {start_index} EI: {end_index} Q%: {quality_percentage: .2g}'
                                      f' #W: {int(number_of_words)} #Pags. {int(num_pages)}) '
                                      f'on collection **{selected_collection}**. '
                                      f'Manually edited (not yet updated in corpus): **{"Yes" if edited else "No"}**. '
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


def initialize_session_variables():
    if 'disabled' not in st.session_state:
        st.session_state.disabled = False

    if 'disabled_collect' not in st.session_state:
        st.session_state.disabled_collect = False

    if 'disabled_neighborhoods' not in st.session_state:
        st.session_state.disabled_neighborhoods = False

    if 'disabled_complete_text_save' not in st.session_state:
        cw.disable_complete_text_save_widget()

    if 'docs_count' not in st.session_state:
        st.session_state.docs_count = 0

    if 'previous_selectbox_value' not in st.session_state:
        st.session_state.previous_selectbox_value = None

    if 'selected_collection' not in st.session_state:
        st.session_state.selected_collection = "No Neighborhoods"

    if 'edited_documents' not in st.session_state:
        data_utils.find_edited_neighborhoods()


def main():
    st.set_page_config(layout="wide", page_title='Explore And Manage Your Corpus', page_icon=':books:')
    st.write(css, unsafe_allow_html=True)
    st.header('Explore And Manage Your Corpus :books:')

    initialize_session_variables()

    with st.sidebar:
        st.write("**NEIGHBORHOOD COLLECTIONS:**")

        # Fetch neighborhood collections from MongoDB
        neighborhood_collections = get_neighborhood_collections()

        if neighborhood_collections:
            if not st.session_state.disabled_neighborhoods:
                cw.enable_widgets_without_collect()
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

        # Necessary for callback functions outside main
        st.session_state.selected_collection = selected_collection

        if selected_collection == 'No Neighborhoods':
            cw.disable_widgets_without_collect()

        st.markdown("""---""")  # Horizontal Separator

        st.write("**COLLECT NEIGHBORHOODS:**")

        col3_sb, col4_sb = st.columns([1, 1])

        # Input fields for generating new neighborhoods
        create_hood_term = col3_sb.text_input("Enter term(s) to collect new neighborhoods (sep ,):",
                                              disabled=st.session_state.disabled_collect)
        create_hood_size = col4_sb.number_input("Enter the size of the new neighborhoods (default 100):", value=100,
                                                step=1, disabled=st.session_state.disabled_collect)
        # Generate New Neighborhoods Button
        collect_neighborhoods_button = st.button("Collect Neighborhoods", on_click=cw.disable_widgets_without_collect,
                                                 disabled=st.session_state.disabled_collect)
        if collect_neighborhoods_button:
            if create_hood_term == "":
                st.warning("Please specify a term to collect the neighborhoods.")
            else:
                if create_hood_size == "":
                    create_hood_size = 100
                sequences = create_hood_term.split(',')
                with st.spinner(f'Collecting neighborhoods for terms "{create_hood_term}". '
                                f'This might take a while. Please wait...'):
                    collection_name = data_utils.collect_neighborhoods_mongo_parallel(sequences_list=sequences,
                                                                                      size=create_hood_size)
                    st.success("Neighborhoods collected successfully.")
                    cw.enable_widgets_without_collect()
                    # In case the same neighborhoods that are being displayed are regenerated
                    st.session_state.docs_count = 0
                    st.session_state.hoods_count = 0
                    st.session_state.selected_collection = collection_name
                    st.rerun()

        st.markdown("""---""")  # Horizontal Separator

        if 'filters' not in st.session_state:
            st.session_state.filters = None
        st.write("**FILTERS:**")

        # Extract unique values for each metadata field
        unique_periodo_values = set()
        unique_nacionalidad_values = set()
        unique_entidad_territorial_values = set()

        if 'hoods_docs' not in st.session_state and selected_collection:
            # Retrieve documents from MongoDB
            st.session_state.hoods_docs = get_documents_from_collection(selected_collection)
        if selected_collection:
            for doc in st.session_state.hoods_docs.values():
                metadata = doc.get('metadata', {})
                unique_periodo_values.add(metadata.get('periodo', ''))
                unique_nacionalidad_values.add(metadata.get('nacionalidad', ''))
                unique_entidad_territorial_values.add(metadata.get('entidad territorial', ''))

        # Add multiselect filters
        st.session_state.selected_periodo = st.multiselect("Select Periodo",
                                                           sorted(unique_periodo_values),
                                                           key="filter_periodo", disabled=st.session_state.disabled)
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
            data_utils.apply_filters_to_neighborhoods()
        # Clear Filters Button
        if col2_sb.button("Clear Filters", disabled=st.session_state.disabled):
            clear_filters()

        if not st.session_state.filters and selected_collection and selected_collection != 'No Neighborhoods' and not st.session_state.disabled_neighborhoods:
            initialize_session_document_variables(selected_collection)

        if 'hoods_count' not in st.session_state:
            st.session_state.hoods_count = 0

    tab1, tab2 = st.tabs(["Edition", "Coocurrences", ])

    with tab1:

        col1, col2, col3, col4, col5, col6 = st.columns([1, 1, 1, 1, 1, 1])

        with col1:
            if st.button("⏮️ Previous Neighborhood", on_click=previous_hood,
                         disabled=st.session_state.disabled_neighborhoods):
                pass

        with col2:
            if st.button("Next Neighborhood ⏭️", on_click=next_hood, disabled=st.session_state.disabled_neighborhoods):
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
                cw.enable_neighborhoods_widgets()
                st.session_state.docs_count = st.session_state.filtered_keys.index(selectbox_doc)
                st.session_state.hoods_count = 0
                # Save the value to control when value changes in the condition
                st.session_state.previous_selectbox_value = selectbox_doc
                st.rerun()

        # If the textarea is not showing a complete text right now or there are no neighborhood collection chosen yet
        text_area_container = st.empty()
        if not st.session_state.disabled_neighborhoods or 'filtered_keys' not in st.session_state:
            cw.enable_all_widgets()
            display_collection_hoods(text_area_container, selected_collection)
            cw.disable_complete_text_save_widget()

        col6, col7, col8, st.session_state.col9 = st.columns([1, 1, 1, 1])

        with col7:

            st.subheader("Add/Delete entries")

            # Display label for the dataframe
            st.markdown("**Add entry to the corrections list**")

            # Input fields for original and corrected terms
            original_term = st.text_input("Original Term:", disabled=st.session_state.disabled)
            corrected_term = st.text_input("Correct Term:", disabled=st.session_state.disabled)

            corrections_collection_name = 'corrections'
            # Button to add entry
            if st.button("Add Entry", disabled=st.session_state.disabled):
                data_utils.add_correction_entry_to_mongo(original_term, corrected_term, corrections_collection_name)

            client = pymongo.MongoClient(config.mongo_connection)
            database = client[config.mongo_database]
            corrections_collection = database[corrections_collection_name]

            # Dropdown to select the entry to delete
            selected_entry = st.selectbox("**Select entry to delete from the corrections list**",
                                          [entry["Original term"] for entry in corrections_collection.find({})],
                                          index=None,
                                          key="delete_dropdown",
                                          disabled=st.session_state.disabled)

            # Button to delete entry
            delete_entry_button = st.button("Delete Entry", disabled=st.session_state.disabled)
            if delete_entry_button:
                data_utils.delete_correction_entry_from_mongo(selected_entry, corrections_collection_name)

        with col8:

            if 'filtered_keys' in st.session_state:
                # Button to display the entire text of the current document
                file_to_display = st.session_state.filtered_keys[st.session_state.docs_count]
                display_complete_text_button = st.button(f"Display text from {file_to_display}",
                                                         disabled=st.session_state.disabled)
                if display_complete_text_button or st.session_state.disabled_neighborhoods:
                    display_complete_text(text_area_container, file_to_display)
                    cw.disable_neighborhoods_widgets()
                    cw.enable_complete_text_save_widget()
                    if display_complete_text_button:
                        st.rerun()

                if st.button(f"Save Text from {file_to_display}",
                             disabled=st.session_state.disabled_complete_text_save):
                    # Call the save function
                    data_utils.save_complete_text_to_mongo(file_to_display)

        with st.session_state.col9:

            # Show success message if neighborhood was saved successfully
            if 'hood_saved' in st.session_state:
                if st.session_state.hood_saved is True:
                    st.success(f"Neighborhood {st.session_state.hoods_count} from file "
                               f"{st.session_state.filtered_keys[st.session_state.docs_count]} saved successfully.")
                elif isinstance(st.session_state.hood_saved, str):
                    st.warning(st.session_state.hood_saved)

            st.session_state.hood_saved = False

            # Check if "Save" button is clicked and save changes
            st.button("Save changes in neighborhood", disabled=st.session_state.disabled_neighborhoods,
                      on_click=data_utils.update_neighborhood_in_collection)

            # Add a button to open the PDF
            if 'filtered_keys' in st.session_state:
                st.button(f"Open PDF for file {st.session_state.filtered_keys[st.session_state.docs_count]}",
                          on_click=open_pdf_button, disabled=st.session_state.disabled)

                if 'updated' in st.session_state:
                    if st.session_state.updated:
                        st.success("Corpus updated successfully.")
                        st.info("Regenerate the neighborhoods to ensure consistency with the corpus indexes.")
                        st.session_state.updated = False
                else:
                    st.session_state.updated = False

                # Only display the not updated files if there have been editions saved
                if st.session_state.edited_documents:
                    st.write("**Edited neighborhoods list (not updated in corpus)**")

                    not_updated_hoods_df = pd.DataFrame(st.session_state.edited_documents)

                    # Display table
                    st.dataframe(not_updated_hoods_df, height=300)

                    update_neighborhoods_in_corpus_button = st.button(f"Update edited neighborhoods in corpus",
                                                                      on_click=cw.disable_all_widgets,
                                                                      disabled=st.session_state.disabled_neighborhoods)

                    if update_neighborhoods_in_corpus_button:
                        data_utils.save_edited_neighborhoods_to_corpus_mongo(st.session_state.selected_collection)
                        st.session_state.updated = True
                        cw.enable_all_widgets()
                        st.rerun()

        with col6:

            st.subheader("Corrections list")

            # Retrieve corrections from MongoDB
            corrections_df = data_utils.get_corrections_from_mongo(corrections_collection_name)

            # Display table below the textarea
            st.dataframe(corrections_df, height=300)

            apply_corrections_button = st.button("Apply corrections to the entire corpus and neighborhoods",
                                                 key="apply_corrections_button", on_click=cw.disable_all_widgets,
                                                 disabled=st.session_state.disabled)

            if apply_corrections_button:
                with st.spinner("Applying corrections. Please wait..."):
                    data_utils.apply_corrections_all_collections_mongo_parallel(corrections_df)
                    st.success("Corrections applied successfully.")

                    # Recollect all neighborhoods and apply filters
                    initialize_session_document_variables(selected_collection)
                    data_utils.apply_filters_to_neighborhoods()

                    cw.enable_all_widgets()
                    st.rerun()


if __name__ == '__main__':
    main()
