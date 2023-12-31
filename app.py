import pandas as pd
import streamlit as st
from htmlTemplates import css
from src import utils
from src import config
from src import data_utils
from pathlib import Path
import json
import os
import subprocess

st.session_state.complete_corpus_file_name = 'all_extracted_text_2023_corrected_all.json'


def next_hood():
    if st.session_state.hoods_count + 1 >= len(
            st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]]):
        st.session_state.hoods_count = 0
    else:
        st.session_state.hoods_count += 1


def previous_hood():
    if st.session_state.hoods_count > 0:
        st.session_state.hoods_count -= 1
    else:
        st.session_state.hoods_count = len(
            st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]]) - 1


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


def apply_filters(metadata_quality):
    # Apply metadata filters to the documents
    st.session_state.filtered_docs = {}
    for key, value in st.session_state.hoods_docs.items():
        metadata_row = metadata_quality[metadata_quality['codigo'] == key]
        if (not st.session_state.selected_nacionalidad or metadata_row['nacionalidad'].iloc[
            0] in st.session_state.selected_nacionalidad) and \
                (not st.session_state.selected_entidad_territorial or metadata_row['entidad territorial'].iloc[
                    0] in st.session_state.selected_entidad_territorial) and \
                (not st.session_state.selected_periodo or metadata_row['periodo'].iloc[
                    0] in st.session_state.selected_periodo):
            st.session_state.filtered_docs[key] = value

    st.session_state.filters = ""
    # Apply term filter do the documents
    if st.session_state.filter_by_term != "":
        filtered_by_term_dict = {}
        for key, value in st.session_state.filtered_docs.items():
            for hood in value:
                if st.session_state.filter_by_term in hood:
                    if key not in filtered_by_term_dict:
                        filtered_by_term_dict[key] = []
                    filtered_by_term_dict[key].append(hood)
        st.session_state.filtered_docs = filtered_by_term_dict
        st.session_state.filters += f"**Term** - {st.session_state.filter_by_term} "

    st.session_state.filtered_keys = list(st.session_state.filtered_docs.keys())
    st.session_state.docs_count = 0
    st.session_state.hoods_count = 0
    if 'selected_periodo' in st.session_state and st.session_state.selected_periodo:
        st.session_state.filters += f"**Periodos** - {' '.join(st.session_state.selected_periodo)} "
    if 'selected_entidad_territorial' in st.session_state and st.session_state.selected_entidad_territorial:
        st.session_state.filters += f"**Entidad Territorial** - {' '.join(st.session_state.selected_entidad_territorial)} "
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


def apply_corrections_all_files(corrections_df, json_file_list):
    corrections_dict = dict(zip(corrections_df['Original term'], corrections_df['Corrected term']))

    for json_file in json_file_list:
        st.info(f"Applying corrections to file {json_file}. Please wait, this might take a while.")
        print(f"Applying corrections to file {json_file}")

        file_data = utils.open_json_data_file(json_file)
        for key, neighborhoods in file_data.items():
            for i, neighborhood in enumerate(neighborhoods):
                tokenized_neighborhood = data_utils.tokenize(neighborhood['neighborhood'])

                # Apply the corrections using set intersection
                corrected_tokens = [corrections_dict.get(token, token) for token in tokenized_neighborhood]

                # Save the updated text back to the JSON data
                file_data[key][i]['neighborhood'] = ' '.join(corrected_tokens)

        # Save the updated JSON data back to the file
        utils.save_json_data_file(json_file, file_data)
        st.info(f"Corrections applied to file {json_file}.")
        print(f"Corrections applied to file {json_file}.")

    whole_corpus_file = Path(config.JSON_DIR, st.session_state.complete_corpus_file_name)
    whole_file_data = utils.open_json_data_file(whole_corpus_file)
    st.info(f"Applying corrections to file {whole_corpus_file}. Please wait, this might take a while.")
    print(f"Applying corrections to file {whole_corpus_file}")

    for key, content in whole_file_data.items():
        tokenized_text = data_utils.tokenize(content['text'])

        # Apply the corrections using set intersection
        corrected_tokens = [corrections_dict.get(token, token) for token in tokenized_text]

        # Save the updated text back to the JSON data
        whole_file_data[key]['text'] = ' '.join(corrected_tokens)

    # Save the updated JSON data back to the file
    utils.save_json_data_file(whole_corpus_file, whole_file_data)
    st.info(f"Corrections applied to file {whole_corpus_file}.")
    print(f"Corrections applied to file {whole_corpus_file}.")


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


def display_hood(text_area_container, quality_data):
    if 'filtered_keys' in st.session_state:
        current_document = st.session_state.filtered_keys[st.session_state.docs_count]
        quality_percentage = quality_data.loc[quality_data['document'] == current_document, 'quality_all'].values[0]
        number_of_words = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['doc_total_words']
        text = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['neighborhood']
        num_pages = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['num_pages']
        start_index = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['start_index']
        end_index = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['end_index']
        edited = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['edited']
        updated = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['updated']
        average_words_per_page = int(number_of_words) / int(num_pages)
        aprox_page_hood = int(start_index / average_words_per_page)
        text_area_container.text_area(f'Neighborhood {st.session_state.hoods_count} from '
                                      f'{len(st.session_state.filtered_docs
                                             [st.session_state.filtered_keys[st.session_state.docs_count]]) - 1}'
                                      f' for "**{st.session_state.hoods_term}**"'
                                      f' in document **{current_document}** '
                                      f'(SI: {start_index} EI: {end_index} Q%: {int(quality_percentage)}'
                                      f' #W: {int(number_of_words)} #Pags. {int(num_pages)}) '
                                      f'on file **{st.session_state.selected_hoods_file.name}**. '
                                      f'Manually edited: **{"Yes" if edited else "No"}**. '
                                      f'Updated in corpus **{"Yes" if updated else "No"}**. '
                                      f'Aprox. page # the neighborhood is at: **{aprox_page_hood + 1}**.',
                                      value=text, height=300, key="hood_text_area",
                                      disabled=st.session_state.disabled)
        st.write(f'Total documents: {len(st.session_state.filtered_keys)}. Total neighborhoods: '
                 f'{sum(len(value) if isinstance(value, list) else 0
                        for value in st.session_state.filtered_docs.values())}. Applied filters: {st.session_state.filters}')
    else:
        text_area_container.text_area(label="No neighborhoods found.",
                                      value="",
                                      height=300)
        st.write(f'Total documents: 0. Total neighborhoods: 0. Applied filters: {st.session_state.filters}')


def save_neighborhoods_file():
    original_text = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
        st.session_state.hoods_count]
    edited_text = st.session_state.hood_text_area
    if edited_text != original_text:
        original_index = st.session_state.hoods_docs[
            st.session_state.filtered_keys[st.session_state.docs_count]].index(original_text)
        st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            original_index]['neighborhood'] = edited_text
        st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            original_index]['edited'] = True
        st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            original_index]['updated'] = False
        st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['neighborhood'] = edited_text
        st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['edited'] = True
        st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
            st.session_state.hoods_count]['updated'] = False

        # Extract the directory path and file name without extension
        file_path = Path(st.session_state.selected_hoods_file)

        # Save the changes back to the neighborhoods file
        with open(file_path, 'w') as json_file:
            json.dump(st.session_state.hoods_docs, json_file, indent=2)

        # Control if neighbor was successfully saved to show message when rerun
        st.session_state.hood_saved = True
    else:
        st.warning("The original text and the text in the text area are the same.")


def disable_widgets():
    st.session_state.disabled = True


def main():
    st.set_page_config(layout="wide", page_title='Explore And Manage Your Corpus', page_icon=':books:')
    st.write(css, unsafe_allow_html=True)
    st.header('Explore And Manage Your Corpus :books:')

    metadata_quality = pd.read_csv(Path(config.CSV_DIR, 'metadata_quality.csv'))
    quality_data = pd.read_csv(Path(config.CSV_DIR, 'quality_comparison.csv'))

    if 'disabled' not in st.session_state:
        st.session_state.disabled = False

    if 'docs_count' not in st.session_state:
        st.session_state.docs_count = 0

    if 'previous_selectbox_value' not in st.session_state:
        st.session_state.previous_selectbox_value = None

    if 'selected_hoods_file_name' not in st.session_state:
        st.session_state.selected_hoods_file_name = "No Neighborhoods"

    with st.sidebar:
        st.write("**FILES:**")

        hoods_json_file_pattern = f"*.json"
        hoods_json_file_list = list(config.NEIGHBORHOODS_DIR.glob(hoods_json_file_pattern))
        if hoods_json_file_list:
            # Create a list of names for display
            hoods_json_file_names = [path.name for path in hoods_json_file_list]
            if st.session_state.selected_hoods_file_name == "No Neighborhoods":
                st.session_state.selected_hoods_file_name = hoods_json_file_names[0]
        else:
            # If it's empty
            hoods_json_file_names = ["No Neighborhoods"]
            hoods_json_file_list = ["No Neighborhoods"]

        if 'selected_hoods_file' not in st.session_state:
            st.session_state.selected_hoods_file = hoods_json_file_list[0]
            st.session_state.selected_hoods_file_name = hoods_json_file_names[0]

        selected_hoods_file = st.selectbox("Select an json file to display the neighborhoods",
                                           hoods_json_file_names,
                                           on_change=clear_filters_on_file_change,
                                           index=hoods_json_file_names.index(st.session_state.selected_hoods_file_name),
                                           disabled=st.session_state.disabled)

        # Get the corresponding full path based on the selected name
        st.session_state.selected_hoods_file = hoods_json_file_list[hoods_json_file_names.index(selected_hoods_file)]
        st.session_state.selected_hoods_file_name = selected_hoods_file

        if selected_hoods_file != st.session_state.selected_hoods_file_name:
            change_selectbox_value(hoods_json_file_list[hoods_json_file_names.index(selected_hoods_file)])

        if 'filters' not in st.session_state:
            st.session_state.filters = None
        st.write("**FILTERS:**")
        # Add multiselect filters
        st.session_state.selected_periodo = st.multiselect("Select Periodo",
                                                           sorted(metadata_quality['periodo'].unique()),
                                                           key="filter_periodo", disabled=st.session_state.disabled)
        # Replace NaN with "None" in the 'nacionalidad' column
        metadata_quality['nacionalidad'] = metadata_quality['nacionalidad'].fillna("Sin nacionalidad")
        st.session_state.selected_nacionalidad = st.multiselect("Select Nacionalidad",
                                                                sorted(metadata_quality['nacionalidad'].unique()),
                                                                disabled=st.session_state.disabled)
        st.session_state.selected_entidad_territorial = st.multiselect("Select Entidad Territorial",
                                                                       sorted(metadata_quality
                                                                              ['entidad territorial'].unique()),
                                                                       disabled=st.session_state.disabled)

        # Input fields for original and corrected terms
        st.session_state.filter_by_term = st.text_input("Filter by term:", disabled=st.session_state.disabled)

        col1_sb, col2_sb = st.columns([1, 1])

        if col1_sb.button("Apply Filters", disabled=st.session_state.disabled):
            apply_filters(metadata_quality)

        # Clear Filters Button
        if col2_sb.button("Clear Filters", disabled=st.session_state.disabled):
            clear_filters()

        if not st.session_state.filters and selected_hoods_file and selected_hoods_file != 'No Neighborhoods':
            st.session_state.hoods_docs = utils.open_json_data_file(st.session_state.selected_hoods_file)
            # Filter out keys with empty values
            st.session_state.hoods_docs = {key: value for key, value in st.session_state.hoods_docs.items() if value}
            st.session_state.hoods_docs = dict(sorted(st.session_state.hoods_docs.items()))
            st.session_state.filtered_docs = st.session_state.hoods_docs.copy()

            st.session_state.hoods_term = Path(st.session_state.selected_hoods_file).stem.split('_')[0]
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

    with st.sidebar:

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
                    data_utils.collect_neighborhoods(sequences_list=sequences, size=create_hood_size,
                                                     json_file=st.session_state.complete_corpus_file_name)
                    st.success("Neighborhoods collected successfully.")
                    st.session_state.disabled = False
                    # In case the same neighborhoods that are being displayed are regenerated
                    st.session_state.docs_count = 0
                    st.session_state.hoods_count = 0
                    st.rerun()

    text_area_container = st.empty()
    display_hood(text_area_container, quality_data)

    tab1, tab2 = st.tabs(["Edition", "Coocurrences",])

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
                                         on_click=save_neighborhoods_file)


            # Add a button to open the PDF
            if 'filtered_keys' in st.session_state:
                st.button(f"Open PDF for file {st.session_state.filtered_keys[st.session_state.docs_count]}",
                          on_click=open_pdf_button, disabled=st.session_state.disabled)

                not_updated_hoods_dict = {}

                for file, neighborhoods in st.session_state.hoods_docs.items():
                    for i, neighborhood in enumerate(neighborhoods):
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
                    st.write("**Edited files list (not updated in corpus)**")

                    not_updated_hoods_df = pd.DataFrame(not_updated_hoods_list)

                    # Display table
                    st.dataframe(not_updated_hoods_df, height=300)

                    update_files_in_corpus_button = st.button(f"Update edited files in corpus",
                                                              on_click=disable_widgets,
                                                              disabled=st.session_state.disabled)

                    if update_files_in_corpus_button:
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
                    apply_corrections_all_files(corrections_df, hoods_json_file_list)
                    st.success("Corrections applied successfully.")
                    st.session_state.disabled = False
                    st.rerun()


if __name__ == '__main__':
    main()
