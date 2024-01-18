import os
import subprocess

import pandas as pd
import streamlit as st
from streamlit_quill import st_quill

from htmlTemplates import css

from src import config, editor_config, data_utils, control_widgets as cw


def next_hood():
    """
    Increments the index (hoods_count) of the currently displayed neighborhood.
    Wraps around to the first neighborhood if the end is reached.
    """
    st.session_state.hoods_count = (st.session_state.hoods_count + 1) % len(
        st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]]['neighborhoods'])


def previous_hood():
    """
    Decrements the index (hoods_count) of the currently displayed neighborhood.
    Wraps around to the last neighborhood if the beginning is reached.
    """
    st.session_state.hoods_count = (st.session_state.hoods_count - 1) % len(
        st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]]['neighborhoods'])


def next_doc():
    """
    Increments the index (docs_count) of the currently displayed document.
    Resets the neighborhood index (hoods_count) to zero.
    Resets the document selection box.
    """
    # Enable widgets related to neighborhoods' navigation and editing
    cw.enable_neighborhoods_widgets()

    st.session_state.docs_count = (st.session_state.docs_count + 1) % len(st.session_state.filtered_docs)
    st.session_state.hoods_count = 0
    st.session_state.doc_selectbox = None  # Reset the selectbox

    # Disable widgets related to full text editing if it is enabled
    if not cw.get_status_complete_text_save_widget():
        cw.disable_complete_text_widgets()


def previous_doc():
    """
    Decrements the index (docs_count) of the currently displayed document.
    Resets the neighborhood index (hoods_count) to zero.
    Resets the document selection box.
    """
    # Enable widgets related to neighborhoods' navigation and editing
    cw.enable_neighborhoods_widgets()

    st.session_state.docs_count = (st.session_state.docs_count - 1) % len(st.session_state.filtered_docs)
    st.session_state.hoods_count = 0
    st.session_state.doc_selectbox = None  # Reset the selectbox

    # Disable widgets related to full text editing if it is enabled
    if not cw.get_status_complete_text_save_widget():
        cw.disable_complete_text_widgets()


def clear_filters():
    """
    Clears all applied filters and resets the session variables related to document and neighborhood indices,
    selected filters, and filtered documents.
    """
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
        if st.session_state.disabled_neighborhoods:
            cw.enable_neighborhoods_widgets()


def clear_filters_on_collection_change():
    """
    Calls the 'clear_filters' function to reset filters when a collection change event occurs.
    """
    clear_filters()


def clear_filters_on_explicit_call():
    """
    Calls the 'clear_filters' function to reset filters when called explicitly.
    """
    clear_filters()
    st.rerun()


def open_pdf_button():
    """
    Attempts to open the PDF file associated with the currently displayed document.
    """
    # Retrieves the PDF file name based on the current document index.
    pdf_file_name = st.session_state.filtered_keys[st.session_state.docs_count]
    # Constructs the full path of the PDF
    pdf_file_path = os.path.join(config.PDF_DIR, f"{pdf_file_name}.pdf")

    if os.path.exists(pdf_file_path):  # Checks if pdf file exists
        # If the file exists, opens it using the default system application (xdg-open).
        with st.session_state.col9:
            subprocess.run(["xdg-open", pdf_file_path])
            st.success(f"Opening PDF: {pdf_file_name}.pdf")
    else:
        with col9:
            st.warning(f"PDF file not found: {pdf_file_path}")


def colorize_word(word, color):
    return f'<span style="color: {color}; font-weight: bold;">{word}</span>'


def count_and_color_text(text_to_display):
    # Tokenize the text
    tokenized_text = data_utils.tokenize(text_to_display)

    # Initialize a dictionary to store counts and colored text
    terms_counts = {}
    colored_text = text_to_display

    # Flag to control if term is a whole word
    ww_flag = False

    # Get neighborhoods terms and filter term, if any, together
    all_terms = st.session_state.hoods_term.copy()
    if st.session_state.filter_by_term != "":
        all_terms.append(st.session_state.filter_by_term)

    # Loop through each term in st.session_state.hoods_term
    for term in all_terms:
        count = 0

        # Check if the term is a whole word indicator
        if term == 'ww':
            ww_flag = True
            continue

        # Count the term
        for word in tokenized_text:
            if ww_flag:
                # Check if the term is a whole word and increment count
                if term.lower() == word.lower():
                    count += 1
            else:
                # Check if the term is a substring of the word and increment count
                if term.lower() in word.lower():
                    count += 1

        # Store the count in the terms_counts dictionary
        terms_counts[term] = count

        # Colorize the term. Different colors if the term is of the neighborhoods or a filter term
        if term == st.session_state.filter_by_term:
            color = 'blue'
        else:
            color = 'red'
        if ww_flag:
            # Colorize the entire word in the text
            colored_text = colored_text.replace(f" {term} ", f" {colorize_word(term, color)} ")
            colored_text = colored_text.replace(f" {term}.", f" {colorize_word(term, color)}.")
            colored_text = colored_text.replace(f" {term},", f" {colorize_word(term, color)},")
            colored_text = colored_text.replace(f" {term}!", f" {colorize_word(term, color)}!")
            colored_text = colored_text.replace(f" {term}?", f" {colorize_word(term, color)}?")
            colored_text = colored_text.replace(f" {term}:", f" {colorize_word(term, color)}:")
            colored_text = colored_text.replace(f" {term};", f" {colorize_word(term, color)};")
            colored_text = colored_text.replace(f" ¡{term} ", f" ¡{colorize_word(term, color)} ")
            colored_text = colored_text.replace(f" ¿{term} ", f" ¿{colorize_word(term, color)} ")
            colored_text = colored_text.replace(f" ({term} ", f" ¿{colorize_word(term, color)} ")
            colored_text = colored_text.replace(f" {term}) ", f" ¿{colorize_word(term, color)} ")
            ww_flag = False
        else:
            # Colorize the specific sequence within the text
            colored_text = colored_text.replace(term, colorize_word(term, color))

    return terms_counts, colored_text


def display_complete_text(text_area_container):
    """
    Displays the complete text of a specific document within a Streamlit text area.

    Parameters:
    - text_area_container (streamlit.container): The container to display the text area.
    """
    document_id = st.session_state.complete_file_to_display
    # Retrieves the complete text of the specified document using the 'data_utils' module.
    document = data_utils.get_complete_text_from_document(document_id)

    # Checks if the document exists.
    if document:
        # Extracts the text to be displayed
        text_to_display = document.get("text", "")

        # Displays the complete text within a Streamlit text area.
        with text_area_container:
            terms_counts, colored_text = count_and_color_text(text_to_display)
            summary_string = "Amount of terms found in the text: "
            for term, count in terms_counts.items():
                summary_string += f"{term} {count} "
            st.write(f"Complete text from document {document_id} on collection **{config.mongo_collection}**. "
                     f"{summary_string}.")
            st.session_state.editor_content = st_quill(colored_text, toolbar=editor_config.toolbar)
    else:
        # If the document does not exist, displays a message indicating that the document was not found.
        # This should never happen
        text_area_container.text(f"Document {document_id} not found "
                                 f"in collection {config.mongo_collection}.")


def display_collection_hoods(text_area_container, selected_collection):
    """
    Displays information about the current neighborhood within a Streamlit text area.

    Parameters:
    - text_area_container (streamlit.container): The container to display the text area.
    - selected_collection (str): The name of the selected collection.
    """

    # Checks if there is a chosen collection available before trying to display anything
    if 'filtered_keys' in st.session_state and st.session_state.filtered_keys:
        # Retrieve information about the current document and neighborhood
        current_document_id = st.session_state.filtered_keys[st.session_state.docs_count]
        current_document = st.session_state.filtered_docs[current_document_id]
        current_metadata = current_document['metadata']
        current_hood = current_document['neighborhoods'][st.session_state.hoods_count]

        # Extract relevant information for display
        quality_percentage = float(current_metadata['quality'])
        number_of_words = current_metadata['doc_total_words']
        num_pages = current_metadata['num_pages']
        text = current_hood['neighborhood']
        start_index = current_hood['start_index']
        end_index = current_hood['end_index']
        edited = current_hood['edited']

        # Process hoods terms to put them in the proper display format
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

        # Calculate average words per page and approximate page where the neighborhood is located
        average_words_per_page = int(number_of_words) / int(num_pages)
        aprox_page_hood = int(start_index / average_words_per_page)

        with text_area_container:
            st.write(f'Neighborhood {st.session_state.hoods_count} from '
                     f'{len(current_document['neighborhoods']) - 1}'
                     f' for **{hoods_terms_string}**'
                     f' in document **{current_document_id}** '
                     f'(SI: {start_index} EI: {end_index} Q%: {quality_percentage: .2g}'
                     f' #W: {int(number_of_words)} #Pags. {int(num_pages)}) '
                     f'on collection **{selected_collection}**. '
                     f'Manually edited (not yet updated in corpus): **{"Yes" if edited else "No"}**. '
                     f'Aprox. page # the neighborhood is at: **{aprox_page_hood + 1}**.')
            terms_counts, colored_text = count_and_color_text(text)
            st.session_state.editor_content = st_quill(colored_text, toolbar=editor_config.toolbar)
            # Display summary information
            st.write(f'Total documents: {len(st.session_state.filtered_keys)}. Total neighborhoods: '
                     f'{sum(len(value['neighborhoods']) if isinstance(value['neighborhoods'], list) else 0
                            for value in st.session_state.filtered_docs.values())}. '
                     f'Applied filters: {st.session_state.filters}')
    else:
        with text_area_container:
            st.write("No neighborhoods found.")
            # Display a message if no neighborhoods are found
            st_quill("", toolbar=editor_config.toolbar)

            # Display summary information when no neighborhoods are found
            st.write(f'Total documents: 0. Total neighborhoods: 0. Applied filters: {st.session_state.filters}')


def initialize_session_variables():
    """
    Initializes and manages various session variables used for controlling the interface widgets
     and tracking document and neighborhood indices.
    """
    # These session variables are all used to control disabling and enabling different interface widgets
    if 'disabled' not in st.session_state:
        st.session_state.disabled = False
    if 'disabled_collect' not in st.session_state:
        st.session_state.disabled_collect = False
    if 'disabled_neighborhoods' not in st.session_state:
        st.session_state.disabled_neighborhoods = False
    if 'disabled_complete_text_save' not in st.session_state:
        cw.disable_complete_text_widgets()

    # These session variables control which is the current (displayed) document and neighborhood of that document
    if 'docs_count' not in st.session_state:
        st.session_state.docs_count = 0
    if 'hoods_count' not in st.session_state:
        st.session_state.hoods_count = 0

    # This session variable holds the previous selected collection to control when a new collection is selected
    if 'previous_selectbox_value' not in st.session_state:
        st.session_state.previous_selectbox_value = None

    # This session variable stores the current selected collection from the selectbox
    if 'selected_collection' not in st.session_state:
        st.session_state.selected_collection = "No Neighborhoods"

    # This session variable stores the current complete file that will be or is displayed in the text area
    if 'complete_file_to_display' not in st.session_state:
        st.session_state.complete_file_to_display = None

    # Variable that holds the current editor content
    if 'editor_content' not in st.session_state:
        st.session_state.editor_content = ""

    # This session variable holds a list of the neighborhoods that have been manually edited
    if 'edited_documents' not in st.session_state:
        data_utils.find_edited_neighborhoods()

    # This session variable has a string describing the chosen filters if any, otherwise None if no filters are chosen
    if 'filters' not in st.session_state:
        st.session_state.filters = None


def populate_session_document_variables(selected_collection):
    """
        Populates session variables related to the documents and neighborhoods of the selected collection.

        Parameters:
        - selected_collection (str): The name of the selected collection.
    """
    # Retrieve documents from MongoDB for the selected collection
    st.session_state.hoods_docs = data_utils.get_documents_from_collection(selected_collection)

    # Sort the documents alphabetically by keys
    st.session_state.hoods_docs = dict(sorted(st.session_state.hoods_docs.items(), key=lambda x: x[0]))

    # Make a copy of the entire neighborhoods corpus because the filtered might change. We mostly use filtered
    # and only use hoods_docs for when we need to reset the filters.
    st.session_state.filtered_docs = st.session_state.hoods_docs.copy()

    # Extract the terms from the collection's name and create a list of filtered keys
    st.session_state.hoods_term = [term.strip() for term in selected_collection.split('_')[1:]]
    st.session_state.filtered_keys = list(st.session_state.filtered_docs.keys())

    # Enable all interface widgets in case they were disabled
    cw.enable_all_widgets()


def neighborhood_collections_interface_controls():
    """
    Manages the interface controls related to neighborhood collections.

    Returns:
    - selected_collection (str): The selected neighborhood collection.
    """
    st.write("**NEIGHBORHOOD COLLECTIONS:**")

    # Fetch neighborhood collections from MongoDB
    neighborhood_collections = data_utils.get_neighborhood_collections()

    # Check if there were neighborhood collections in the database
    if neighborhood_collections:
        # If the neighborhood widgets are not disabled
        if not st.session_state.disabled_neighborhoods:
            cw.enable_widgets_without_collect()
        # If there are no selected collection or the selected collection
        # is not from the database (ex. No Neighborhoods)
        if (st.session_state.selected_collection is None or st.session_state.selected_collection
                not in neighborhood_collections):
            st.session_state.selected_collection = neighborhood_collections[0]
    else:
        # If no neighborhood collections exist make a 1 element list with No Neighborhoods
        neighborhood_collections = ["No Neighborhoods"]

    # The selectbox for neighborhood collections
    selected_collection = st.selectbox("Select a collection to display the neighborhoods",
                                       neighborhood_collections,
                                       on_change=clear_filters_on_collection_change,
                                       index=neighborhood_collections.index(st.session_state.selected_collection),
                                       disabled=st.session_state.disabled,
                                       key='collections_selectbox')

    # Set session variable necessary for callback functions outside main
    st.session_state.selected_collection = selected_collection
    return selected_collection


def collect_neighborhoods_interface_controls(selected_collection):
    """
    Manages the interface controls for collecting new neighborhoods.

    Parameters:
    - selected_collection (str): The selected neighborhood collection.
    """
    st.write("**COLLECT NEIGHBORHOODS:**")

    # If there are no neighborhood collections then disable all widgets except those to collect neighborhoods
    if selected_collection == 'No Neighborhoods':
        cw.disable_widgets_without_collect()

    col3_sb, col4_sb = st.columns([1, 1])

    # Input fields for generating new neighborhoods
    create_hood_term = col3_sb.text_input("Enter term(s) to collect new neighborhoods (sep ,):",
                                          disabled=st.session_state.disabled_collect)
    # Make terms lowercase
    create_hood_term = create_hood_term.lower()

    create_hood_size = col4_sb.number_input(f"Enter the size of the new neighborhoods "
                                            f"(default {config.neighborhoods_size}):", value=config.neighborhoods_size,
                                            step=1, disabled=st.session_state.disabled_collect)
    # Generate New Neighborhoods Button
    collect_neighborhoods_button = st.button("Collect Neighborhoods", on_click=cw.disable_widgets_without_collect,
                                             disabled=st.session_state.disabled_collect)

    # If the Collect Neighborhoods button is pressed
    if collect_neighborhoods_button:
        # Check if there is a term specified and show warning message if it wasn't
        if create_hood_term == "":
            st.warning("Please specify a term to collect the neighborhoods.")
        else:
            # Check if the size of the neighborhoods was specified and if not set it to the default in configuration
            if create_hood_size == "":
                create_hood_size = config.neighborhoods_size

            # Get the string sequences to collect the neighborhoods
            sequences = create_hood_term.split(',')

            # Streamlit spinner while processing the collecting of neighborhoods
            with st.spinner(f'Collecting neighborhoods for terms "{create_hood_term}". '
                            f'This might take a while. Please wait...'):

                # Collects the neighborhoods based on the specified sequences
                # and returns the name of the created collection
                collection_name = data_utils.collect_neighborhoods_mongo_parallel(sequences_list=sequences,
                                                                                  size=create_hood_size)
                st.success("Neighborhoods collected successfully.")

                # Once we are sure we have at least a collection of neighborhoods,
                # enable the remaining widgets if they were disabled
                cw.enable_widgets_without_collect()

                # Reset docs_count and hoods_count to 0 to avoid index out of bounds errors
                st.session_state.docs_count = 0
                st.session_state.hoods_count = 0

                # Set the selected collection to the newly created one
                st.session_state.selected_collection = collection_name

                # Rerun to see changes in the interface
                st.rerun()


def filters_interface_controls(selected_collection):
    """
    Manages the interface controls for applying and clearing filters.

    Parameters:
    - selected_collection (str): The selected neighborhood collection.
    """
    st.write("**FILTERS:**")

    # Variables to store unique values for each metadata field
    unique_periodo_values = set()
    unique_nacionalidad_values = set()
    unique_entidad_territorial_values = set()

    # If there is a collection of documents and a collection has been selected
    if 'hoods_docs' not in st.session_state and selected_collection:
        # Retrieve documents from MongoDB
        st.session_state.hoods_docs = data_utils.get_documents_from_collection(selected_collection)

    # If selected collection exists
    if selected_collection:

        # Get the required metadata fields for each document from the collection and add them to the set variables
        for doc in st.session_state.hoods_docs.values():
            metadata = doc.get('metadata', {})
            unique_periodo_values.add(metadata.get('periodo', ''))
            unique_nacionalidad_values.add(metadata.get('nacionalidad', ''))
            unique_entidad_territorial_values.add(metadata.get('entidad territorial', ''))

    # Add multiselect filters using the set variables
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
    st.text_input("Filter by term:", disabled=st.session_state.disabled, key='filter_by_term')

    # Columns to organize filters buttons
    col1_sb, col2_sb = st.columns([1, 1])

    # Apply filters button
    if col1_sb.button("Apply Filters", disabled=st.session_state.disabled):
        data_utils.apply_filters_to_neighborhoods()

    # Clear Filters Button
    if col2_sb.button("Clear Filters", disabled=st.session_state.disabled):
        clear_filters_on_explicit_call()


def sidebar_interface_controls():
    """
    Manages the interface controls in the Streamlit sidebar.

    Returns:
    - selected_collection (str): The selected neighborhood collection.
    """
    with st.sidebar:
        selected_collection = neighborhood_collections_interface_controls()

        st.markdown("""---""")  # Horizontal Separator

        collect_neighborhoods_interface_controls(selected_collection)

        st.markdown("""---""")  # Horizontal Separator

        filters_interface_controls(selected_collection)

        return selected_collection


def neighborhoods_navigation_interface_controls():
    """
    Manages the interface controls for navigating through neighborhoods and documents.
    """
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
        # Only if there's a filtered_keys variable in the session there are documents to populate the selectbox
        if 'filtered_keys' in st.session_state and st.session_state.filtered_keys:
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


def general_corrections_interface_controls():
    """
    Manages the interface controls for adding and deleting entries in the corrections list.
    """
    st.subheader("Add/Delete entries")

    # Display label for the dataframe
    st.markdown("**Add entry to the corrections list**")

    # Input fields for original and corrected terms
    original_term = st.text_input("Original Term:", disabled=st.session_state.disabled)
    corrected_term = st.text_input("Correct Term:", disabled=st.session_state.disabled)

    # Button to add entry
    if st.button("Add Entry", disabled=st.session_state.disabled):
        data_utils.add_correction_entry_to_mongo(original_term, corrected_term)

    corrections_collection = data_utils.get_corrections_from_collection()

    # Dropdown to select the entry to delete
    selected_entry = st.selectbox("**Select entry to delete from the corrections list**",
                                  [entry["Original term"] for entry in corrections_collection.find({})],
                                  index=None,
                                  key="delete_dropdown",
                                  disabled=st.session_state.disabled)

    # Button to delete entry
    delete_entry_button = st.button("Delete Entry", disabled=st.session_state.disabled)
    if delete_entry_button:
        data_utils.delete_correction_entry_from_mongo(selected_entry)


def complete_text_interface_controls(text_area_container):
    """
    Manages the interface controls for displaying and saving the entire text of the current document.

    Parameters:
    - text_area_container (streamlit.container): The container to display the text area.
    """
    # Check if there are documents from a collection present
    if 'filtered_keys' in st.session_state and st.session_state.filtered_keys:
        # cw.enable_neighborhoods_widgets()
        # Button to display the entire text of the current document
        st.session_state.complete_file_to_display = st.session_state.filtered_keys[st.session_state.docs_count]
        display_complete_text_button = st.button(f"Display text from {st.session_state.complete_file_to_display}",
                                                 disabled=st.session_state.disabled)
        if display_complete_text_button or st.session_state.disabled_neighborhoods:
            display_complete_text(text_area_container)

            # Disabling, enabling of buttons and rerun should only be done
            # when the button for full text display is pressed
            if display_complete_text_button:
                # Disable widgets for control of neighborhoods
                cw.disable_neighborhoods_widgets()
                # Enable widgets that control the complete text
                cw.enable_complete_text_widgets()

        st.button(f"Save Text from {st.session_state.complete_file_to_display}",
                  disabled=st.session_state.disabled_complete_text_save,
                  on_click=data_utils.save_complete_text_to_mongo)

        # if save_complete_text_button:
        # Call the save function
        #    data_utils.save_complete_text_to_mongo(file_to_display)
    else:
        cw.disable_complete_text_widgets()
        cw.disable_neighborhoods_widgets()


def neighborhoods_editing_interface_controls(selected_collection):
    """
    Manages the interface controls for editing neighborhoods, saving changes, and updating the corpus.

    Parameters:
    - selected_collection (str): The name of the selected neighborhood collection.
    """
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

        if 'filtered_keys' in st.session_state and st.session_state.filtered_keys:
            if 'updated' in st.session_state:
                if st.session_state.updated:
                    st.success("Corpus updated successfully.")
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

    with st.session_state.col6:

        st.subheader("Corrections list")

        # Retrieve corrections from MongoDB
        corrections_df = data_utils.get_corrections_from_mongo()

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
                populate_session_document_variables(selected_collection)
                data_utils.apply_filters_to_neighborhoods()

                cw.enable_all_widgets()
                st.rerun()


def edition_interface(selected_collection):
    """
    Manages the interface controls for displaying neighborhoods, applying corrections, and editing neighborhoods.

    Parameters:
    - selected_collection (str): The name of the selected neighborhood collection.
    """
    neighborhoods_navigation_interface_controls()

    text_area_container = st.container()
    # If the textarea is not showing a complete text right now or there is a neighborhood collection chosen yet,
    # then show the neighborhoods in the textarea
    if not st.session_state.disabled_neighborhoods or 'filtered_keys' not in st.session_state:
        cw.enable_all_widgets()
        display_collection_hoods(text_area_container, selected_collection)
        cw.disable_complete_text_widgets()

    st.session_state.col6, col7, st.session_state.col8, st.session_state.col9 = st.columns([1, 1, 1, 1])

    with col7:
        general_corrections_interface_controls()

    with st.session_state.col8:
        complete_text_interface_controls(text_area_container)

    # Display and control the interface controls for the editing neighborhoods
    neighborhoods_editing_interface_controls(selected_collection)

    with st.session_state.col9:
        # Add a button to open the PDF
        if 'filtered_keys' in st.session_state and st.session_state.filtered_keys:
            st.button(f"Open PDF for file {st.session_state.filtered_keys[st.session_state.docs_count]}",
                      on_click=open_pdf_button, disabled=st.session_state.disabled)


def main():
    st.set_page_config(layout="wide", page_title='Explore And Manage Your Corpus', page_icon=':books:')
    st.write(css, unsafe_allow_html=True)
    st.header('Explore And Manage Your Corpus :books:')

    initialize_session_variables()

    selected_collection = sidebar_interface_controls()

    # Populate or repopulate the neighborhoods if there are no filtered options and there's a selected collection
    # TODO: this can be more efficient. If no filters, just re-copy hoods. If selection changes do the whole thing??
    if (not st.session_state.filters and selected_collection and selected_collection != 'No Neighborhoods'
            and not st.session_state.disabled_neighborhoods):
        populate_session_document_variables(selected_collection)

    tab1, tab2 = st.tabs(["Edition", "Coocurrences", ])

    with tab1:
        edition_interface(selected_collection)


if __name__ == '__main__':
    main()
