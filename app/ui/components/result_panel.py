import streamlit as st


def result_panel(title: str, result) -> None:
    st.subheader(title)
    if isinstance(result, (dict, list)):
        st.json(result)
    else:
        st.text_area("结果", str(result), height=420)
