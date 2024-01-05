import streamlit as st


def disable_all_widgets():
    st.session_state.disabled = True
    st.session_state.disabled_collect = True
    st.session_state.disabled_neighborhoods = True


def enable_all_widgets():
    st.session_state.disabled = False
    st.session_state.disabled_collect = False
    st.session_state.disabled_neighborhoods = False


def disable_widgets_without_collect():
    st.session_state.disabled = True
    st.session_state.disabled_neighborhoods = True


def enable_widgets_without_collect():
    st.session_state.disabled = False
    st.session_state.disabled_neighborhoods = False


def disable_neighborhoods_widgets():
    st.session_state.disabled_neighborhoods = True


def enable_neighborhoods_widgets():
    st.session_state.disabled_neighborhoods = False


def disable_complete_text_save_widget():
    st.session_state.disabled_complete_text_save = True


def enable_complete_text_save_widget():
    st.session_state.disabled_complete_text_save = False
