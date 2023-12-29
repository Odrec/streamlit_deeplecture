import pandas as pd
import streamlit as st
from htmlTemplates import css
from src import utils
from src import config
from pathlib import Path
import json


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


def display_hood(text_area_container, metadata_quality):
    if 'filtered_keys' in st.session_state:
        current_document = st.session_state.filtered_keys[st.session_state.docs_count]
        quality_percentage = metadata_quality.loc[metadata_quality['codigo'] ==
                                                  current_document, 'OCR WB Quality %'].values[0]
        number_of_words = metadata_quality.loc[metadata_quality['codigo'] ==
                                               current_document, '# Words'].values[0]
        text = st.session_state.filtered_docs[st.session_state.filtered_keys
        [st.session_state.docs_count]][st.session_state.hoods_count]
        text_area_container.text_area(f'Neighborhood {st.session_state.hoods_count} from '
                                      f'{len(st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]]) - 1}'
                                      f' for "**{st.session_state.hoods_term}**"'
                                      f' in document **{current_document}** (Q%: {int(quality_percentage)}'
                                      f' #W: {int(number_of_words)}) '
                                      f'on file **{st.session_state.selected_hoods_file.name}**: ',
                                      value=text, height=300, key="hood_text_area")
        st.write(f'Total documents: {len(st.session_state.filtered_keys)}. Total neighborhoods: '
                 f'{sum(len(value) if isinstance(value, list) else 0
                        for value in st.session_state.filtered_docs.values())}. Applied filters: {st.session_state.filters}')
    else:
        text_area_container.text_area(label="No neighborhoods found.",
                                      value="",
                                      height=300)
        st.write(f'Total documents: 0. Total neighborhoods: 0. Applied filters: {st.session_state.filters}')


def save_neighborhoods_file(filtered_docs, selected_hoods_file):
    # Extract the directory path and file name without extension
    file_path = Path(selected_hoods_file)
    directory_path = file_path.parent
    file_name_without_extension = file_path.stem

    # Create the edited file name with preserved path
    if not 'edited' in file_name_without_extension:
        edited_file = directory_path / f"{file_name_without_extension}_edited.json"
    else:
        edited_file = file_path

    # Save the changes back to the neighborhoods file
    with open(edited_file, 'w') as json_file:
        json.dump(filtered_docs, json_file, indent=2)

    st.session_state.selected_hoods_file = edited_file
    st.session_state.selected_hoods_file_name = edited_file.name
    # Control if neighbor was successfully saved to show message when rerun
    st.session_state.hood_saved = True
    st.rerun()


def main():
    st.set_page_config(layout="wide", page_title='Explore And Manage Your Corpus', page_icon=':books:')
    st.write(css, unsafe_allow_html=True)
    st.header('Explore And Manage Your Corpus :books:')

    metadata_quality = pd.read_csv(Path(config.CSV_DIR, 'metadata_quality.csv'))

    if 'docs_count' not in st.session_state:
        st.session_state.docs_count = 0

    if 'previous_selectbox_value' not in st.session_state:
        st.session_state.previous_selectbox_value = None

    with st.sidebar:
        st.write("**FILES:**")

        hoods_json_file_pattern = f"*.json"
        hoods_json_file_list = list(config.NEIGHBORHOOD_DIR.glob(hoods_json_file_pattern))
        # Create a list of names for display
        hoods_json_file_names = [path.name for path in hoods_json_file_list]

        if 'selected_hoods_file' not in st.session_state:
            st.session_state.selected_hoods_file = hoods_json_file_list[0]
            st.session_state.selected_hoods_file_name = hoods_json_file_names[0]

        selected_hoods_file = st.selectbox("Select an json file to display the neighborhoods",
                                           hoods_json_file_names,
                                           on_change=clear_filters_on_file_change,
                                           index=hoods_json_file_names.index(st.session_state.selected_hoods_file_name))

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
                                                           key="filter_periodo")
        # Replace NaN with "None" in the 'nacionalidad' column
        metadata_quality['nacionalidad'] = metadata_quality['nacionalidad'].fillna("Sin nacionalidad")
        st.session_state.selected_nacionalidad = st.multiselect("Select Nacionalidad",
                                                                sorted(metadata_quality['nacionalidad'].unique()))
        st.session_state.selected_entidad_territorial = st.multiselect("Select Entidad Territorial",
                                                                       sorted(metadata_quality
                                                                              ['entidad territorial'].unique()))

        # Input fields for original and corrected terms
        st.session_state.filter_by_term = st.text_input("Filter by term:")

        col1_sb, col2_sb = st.columns([1, 1])

        if col1_sb.button("Apply Filters"):
            apply_filters(metadata_quality)

        # Clear Filters Button
        if col2_sb.button("Clear Filters"):
            clear_filters()

        if not st.session_state.filters and selected_hoods_file:
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
        if st.button("⏮️ Previous Neighborhood", on_click=previous_hood):
            pass

    with col2:
        if st.button("Next Neighborhood ⏭️", on_click=next_hood):
            pass

    with col3:
        if st.button("⏮️ Previous Document", on_click=previous_doc):
            pass

    with col4:
        if st.button("Next Document ⏭️", on_click=next_doc):
            pass

    with col5:
        if 'filtered_keys' in st.session_state:
            selectbox_doc = st.selectbox(label='Choose a document to navigate to',
                                         options=st.session_state.filtered_keys, key='doc_selectbox', index=None)
        else:
            selectbox_doc = st.selectbox(label='Choose a document to navigate to', key='doc_selectbox', options=[])

        if selectbox_doc and selectbox_doc != st.session_state.previous_selectbox_value:
            st.session_state.docs_count = st.session_state.filtered_keys.index(selectbox_doc)
            st.session_state.hoods_count = 0
            # Save the value to control when value changes in the condition
            st.session_state.previous_selectbox_value = selectbox_doc

    text_area_container = st.empty()
    display_hood(text_area_container, metadata_quality)

    col6, col7, col8, col9 = st.columns([1, 1, 1, 1])

    corrections_file_path = 'csv/corrections.csv'

    # Read CSV without column names
    df = pd.read_csv(corrections_file_path, header=None)

    # Add column names
    df.columns = ["Original term", "Corrected term"]

    with col7:
        st.subheader("Add/Delete entries")

        # Display label for the dataframe
        st.markdown("**Add entry to the corrections list**")

        # Input fields for original and corrected terms
        original_term = st.text_input("Original Term:")
        corrected_term = st.text_input("Corrected Term:")

        # Button to add entry
        if st.button("Add Entry"):
            if original_term in df["Original term"].values:
                st.warning(f"Entry for term '{original_term}' already exists.")
            elif len(original_term) == 0 or original_term.isspace():
                st.warning("You can't add an empty original term.")
            else:
                new_entry = {"Original term": original_term, "Corrected term": corrected_term}
                df = df._append(new_entry, ignore_index=True)
                # Save the updated DataFrame to CSV
                df.to_csv(corrections_file_path, index=False, header=False)
                st.success("Entry added successfully!")

        # with col6:
        # Dropdown to select the entry to delete
        selected_entry = st.selectbox("**Select entry to delete from the corrections list**",
                                      df["Original term"].tolist(), index=None,
                                      key="delete_dropdown")

        # Button to delete entry
        if st.button("Delete Entry"):
            if selected_entry:
                print(selected_entry)
                df = df[df["Original term"] != selected_entry]
                # Save the updated DataFrame to CSV
                df.to_csv(corrections_file_path, index=False, header=False)
                st.success("Entry deleted successfully!")
            else:
                st.warning("Choose a valid entry from the dropdown.")

    with col6:

        st.subheader("Corrections list")

        # Display table below the textarea
        st.dataframe(df, height=300)

    with col9:
        save_button = st.button("Save changes in neighborhood", key="save_button")

        # Show success message if neighborhood was saved successfully
        if 'hood_saved' in st.session_state:
            if st.session_state.hood_saved:
                st.success(f"Neighborhood {st.session_state.hoods_count} from file "
                           f"{st.session_state.filtered_keys[st.session_state.docs_count]} saved succesfully.")
                st.session_state.hood_saved = False
        else:
            st.session_state.hood_saved = False

        # Check if "Save" button is clicked and save changes
        if save_button:
            original_text = st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
                st.session_state.hoods_count]
            edited_text = st.session_state.hood_text_area
            if edited_text != original_text:
                original_index = st.session_state.hoods_docs[
                    st.session_state.filtered_keys[st.session_state.docs_count]].index(original_text)
                st.session_state.hoods_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
                    original_index] = edited_text
                st.session_state.filtered_docs[st.session_state.filtered_keys[st.session_state.docs_count]][
                    st.session_state.hoods_count] = edited_text

                # Save changes back to the neighborhoods file
                save_neighborhoods_file(st.session_state.hoods_docs, st.session_state.selected_hoods_file)
            else:
                st.warning("The original text and the text in the text area are the same.")


if __name__ == '__main__':
    main()
