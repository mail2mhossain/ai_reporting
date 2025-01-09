# streamlit run app.py

import time
import os
import io
import re
import json
import uuid 
import zipfile
import threading
from queue import Queue, LifoQueue
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from data_dictionary_generator_node import generate_data_dictionary
from nodes.file_manager_db import insert_db_info, get_all_file_info, if_db_exist
from reporting_graph_generator import get_reports
from connection_check import is_connection_ok, is_table_exist, get_random_rows
from dotenv import load_dotenv, set_key
from decouple import config
from decouple import AutoConfig

st.cache_data.clear()

load_dotenv()
config = AutoConfig()
data_directory = os.path.join(os.path.dirname(__file__), "data")

# database_url = "postgresql://postgres:postgres@localhost/ChinookDB"

# Initialize session states
if 'selected_db_name' not in st.session_state:
    st.session_state['selected_db_name'] = ""

if 'history' not in st.session_state:
    st.session_state['history'] = []
if 'last_report' not in st.session_state:
    st.session_state['last_report'] = None
if 'query' not in st.session_state:
    st.session_state['query'] = ''

if "selected_table_name" not in st.session_state:
    st.session_state["selected_table_name"] = None
if "selected_table" not in st.session_state:
    st.session_state["selected_table"] = None
if "data_loaded" not in st.session_state:
    st.session_state["data_loaded"] = False
if "data" not in st.session_state:
    st.session_state["data"] = None

if 'openai_api_key' not in st.session_state:
    st.session_state['openai_api_key'] = config("OPENAI_API_KEY", default="")
if 'gpt_model' not in st.session_state:
    st.session_state['gpt_model'] = config("GPT_MODEL", default="gpt-4o")


def get_temp_file(uploaded_file):
    erd_path = os.path.join("images", uploaded_file.name)
    os.makedirs("images", exist_ok=True)  
    with open(erd_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return erd_path

def update_env_variable(key, value):
    env_path = ".env"
    set_key(env_path, key, value)
    

def sanitize_filename(query):
    # Remove special characters and limit filename length
    sanitized = re.sub(r'[^a-zA-Z0-9_\- ]', '', query)  # Allow only alphanumeric, underscore, hyphen, and space
    sanitized = "_".join(sanitized.split())  # Replace spaces with underscores
    return sanitized[:50]  # Limit to 50 characters for readability

def download_png_files(png_paths):
    png_files = {}
    for path in png_paths:
        try:
            with open(path, 'rb') as f:
                png_files[Path(path).name] = f.read()
        except FileNotFoundError:
            st.warning(f"File {path} not found")
            
    return png_files

def download_reports(query, report):
    markdown_content = f"# Query: {query}\n\n{report}"
    markdown_file = io.StringIO(markdown_content)  # Use StringIO to create an in-memory file
    filename = sanitize_filename(query) + ".md"
    download_key = str(uuid.uuid4())
    st.download_button(
        label="Download Report",
        data=markdown_file.getvalue(),
        file_name=filename,
        mime="text/markdown",
        key=download_key
    )

def download_reports_with_png(query, report):
    # Extract PNG file paths from the markdown report
    pattern = r'!\[.*?\]\((.*?\.png)\)'
    png_paths = re.findall(pattern, report)
    
    # Download or collect PNG files
    png_files = download_png_files(png_paths)

    # Create a ZIP file in-memory
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
        # Add markdown report to the ZIP
        markdown_content = f"# Query: {query}\n\n{report}"
        markdown_filename = sanitize_filename(query) + ".md"
        zip_file.writestr(markdown_filename, markdown_content)

        # Add PNG files to the ZIP
        for file_name, content in png_files.items():
            zip_file.writestr(f"images/{file_name}", content)

    zip_buffer.seek(0)  # Move the buffer pointer to the start

    # Offer the ZIP file as a download
    zip_filename = sanitize_filename(query) + ".zip"
    download_key = str(uuid.uuid4())
    st.download_button(
        label="Download Report",
        data=zip_buffer,
        file_name=zip_filename,
        mime="application/zip",
        key=download_key
    )

def update_headings(text):
    # Replace headings in the order from largest to smallest to prevent conflicts
    text = re.sub(r'(?m)^###### ', '######## ', text)  # Handle heading 6, if any
    text = re.sub(r'(?m)^##### ', '####### ', text)
    text = re.sub(r'(?m)^#### ', '###### ', text)
    text = re.sub(r'(?m)^### ', '##### ', text)
    text = re.sub(r'(?m)^## ', '#### ', text)
    text = re.sub(r'(?m)^# ', '### ', text)
    return text

def display_reports(markdown_text):
    # Regex to find image references and capture captions and paths
    image_pattern = r'!\[(.*?)\]\((.*?)\)'

    # Split the markdown text into segments by images
    parts = re.split(image_pattern, markdown_text)

    # Find all image references to extract their captions and paths
    image_matches = re.findall(image_pattern, markdown_text)

    # Display the content and images alternately
    text_index = 0

    if len(image_matches) == 0:
        # No images found, display the full markdown text at once
        st.markdown(markdown_text)
    else:
        # Proceed with the original loop logic if there are images
        for i in range(len(parts)):
            if i % 3 == 0:
                st.markdown(parts[i])
            elif i % 3 == 1:
                if text_index < len(image_matches):
                    caption, path = image_matches[text_index]
                    if os.path.exists(path):
                        st.image(path.strip(), caption=caption)
                    text_index += 1

def submit_query():
    if st.session_state['last_report']:
        st.session_state['history'].append(st.session_state['last_report'])

    selected_name = st.session_state['selected_db_name']
    if selected_name:
        try:
            with st.spinner("Generating report..."):
                st.session_state['query'] = st.session_state['query_input']
                report = get_reports(selected_name, st.session_state['query'])
                report = update_headings(report)
                st.session_state['last_report'] = (st.session_state['query'], report)
        except Exception as e:
            st.error(f"Error occurred: {e}") 
    else:
        st.warning("Please select a dataset.")

    st.session_state['query'] = ''

# Title of the app
st.title("AI Reporting Tool")
    

def generate_reports():
    st.subheader("Select Database for Reporting")
    
    if not all([st.session_state['openai_api_key'], st.session_state['gpt_model']]):
        st.info("First Configure OpenAI API Key and Model Name in the 'Configuration' tab. After that, configure Dataset and upload data.")
    else:
        available_datasets = get_all_file_info()
        if available_datasets:
            dataset_choices = [dataset["db_name"] for dataset in available_datasets]
            # Ensure selected_db_name is valid or reset to None
            if 'selected_db_name' in st.session_state and st.session_state['selected_db_name'] not in dataset_choices:
                st.session_state['selected_db_name'] = None
            st.selectbox("Choose a DB:", dataset_choices, key="selected_db_name", index=None)
        else:
            st.info("No Database available. Please configure Dataset and upload data.")

    if st.session_state['selected_db_name']:
        with st.form(key='query_form'):
            query = st.text_input("Enter your query:", value=st.session_state['query'], key="query_input")
            submit_button = st.form_submit_button(label="Generate Report", on_click=submit_query)

        if st.session_state['last_report']:
            query, report = st.session_state['last_report']
            st.markdown(f"### Query: {query}")
            display_reports(report)
            download_reports_with_png(query, report)

        st.subheader("Chat History")
        total_history = len(st.session_state['history']) 
        for i, (query, report) in enumerate(reversed(st.session_state['history'])):
            st.markdown(f"### Query {total_history - i}: {query}")
            display_reports(report)
            download_reports_with_png(query, report)
    else:
        st.info("Please select a dataset for analysis.")



def configure_database():
    st.subheader("Data Dictionary Generator")
    # Input fields for database name and connection string
    db_name = st.text_input("Database Name", "")
    connection_string = st.text_input("Database Connection String", "")
   
    # Image uploader for ERD diagram
    st.subheader("Upload ERD Diagram")
    erd_image = st.file_uploader("Upload an ERD Image", type=["jpg", "jpeg", "png"])
    if erd_image:
        st.image(erd_image, caption="Uploaded ERD Diagram", use_container_width=True)
    
    # Button to generate data dictionary
    if st.button("Generate Data Dictionary"):
        if not db_name.strip():
            st.error("Database Name cannot be blank.")
        elif not connection_string.strip():
            st.error("Database Connection String cannot be blank.")
        elif not erd_image:
            st.error("ERD Image must be uploaded.")
        else:
            if if_db_exist(db_name.strip()):
                st.error("Database already exists. Please choose a different name.")
                return
            if is_connection_ok(connection_string.strip()):
                st.info("The connection string is valid.")
                erd_path = get_temp_file(erd_image)
                with st.spinner("Generating data dictionary..."):
                    data_dictionary =  generate_data_dictionary(erd_path)
                data_dictionary = data_dictionary.model_dump() 
                st.session_state["data"] = data_dictionary
                st.session_state["data"]["db_name"]= db_name.strip()
                st.session_state["data"]["connection_string"]= connection_string.strip()
                st.session_state["data"]["erd_path"]= erd_path
                st.session_state["data_loaded"] = True
            else:
                st.error("The connection string is invalid.")
        
    # Display database overview and tables if data is loaded
    if st.session_state["data_loaded"]:
        data = st.session_state["data"]

        # Display database overview
        st.subheader("Database Overview")
        
        st.session_state["database_overview"] = st.text_area("DatabaseOverview:", data["description"])

        # Table selection dropdown
        table_names = [table["name"].lower() for table in data["tables"]]
        selected_table_name = st.selectbox("Select a Table", table_names, key="table_selector")

        # Update session state only when the table selection changes
        if selected_table_name != st.session_state["selected_table_name"]:
            st.session_state["selected_table_name"] = selected_table_name
            st.session_state["selected_table"] = next(
                (table for table in data["tables"] if table["name"].lower() == selected_table_name), None
            )

        # Display the selected table details
        table = st.session_state["selected_table"]
        if table:
            if not is_table_exist(connection_string.strip(), table['name'].lower()):
                st.error(f"Table {table['name']} does not exist in Database.")
            else:
                table['name'] =table['name'].lower()
                st.subheader(f"Table: {table['name']}")
                
                # Editable table description
                table_description = st.text_area("Table Description:", table["description"])

                # Editable table columns using data_editor
                columns_df = pd.DataFrame(table["columns"])
                editable_df = st.data_editor(columns_df, num_rows="dynamic")
                if 'sample_data' in table:
                    df = pd.DataFrame(table["sample_data"])
                else:
                    df = get_random_rows(connection_string.strip(), table['name'])
                    table["sample_data"] = df.to_dict(orient="records")
                st.dataframe(df)

                # Use columns to align the "Save Changes" button below the table
                col1, col2, col3 = st.columns([4, 4, 3])  # Adjust ratios for spacing

                # Save Changes button
                with col3:  # Place the button in the rightmost column
                    if st.button("Save Changes"):
                        rows_with_all_null = editable_df[editable_df.isnull().all(axis=1)]

                        # If there are any such rows, show error with row indices
                        if not rows_with_all_null.empty:
                            row_indices = rows_with_all_null.index.tolist()
                            st.error(f"Validation failed: Rows with indices {row_indices} have all values missing.")

                        elif not table_description.strip():
                            st.error("Table description cannot be blank.")   
                        else:
                            # Update table description
                            table["description"] = table_description
                            
                            # Update table columns
                            table["columns"] = editable_df.to_dict(orient="records")
                            
                            # Update session state
                            st.session_state["data"]["tables"] = [
                                t if t["name"].lower() != table["name"] else table
                                for t in st.session_state["data"]["tables"]
                            ]
                            st.write("Updated Successfully.")
                

                # "Apply Changes" Button to Save JSON to Disk
                if st.button("Apply Changes"):
                    # Check for required fields
                    if not db_name.strip():
                        st.error("Database Name cannot be blank.")
                    elif not connection_string.strip():
                        st.error("Database Connection String cannot be blank.")
                    elif not erd_image:
                        st.error("ERD Image must be uploaded.")
                    elif not st.session_state["database_overview"].strip():
                        st.error("Database Overview cannot be blank.")
                    else:
                        apply_changes = True
                        tables = [table for table in st.session_state["data"]["tables"]]
                        for table in tables:
                            if 'sample_data' not in table:
                                apply_changes = False
                                st.error(f"Sample data not found for table {table['name']}.")

                        if (apply_changes):
                            insert_db_info(st.session_state["data"])
                            st.success(f"All changes applied and saved to DB!")
    


def configure_openai_api():
    st.subheader("Configuration")

    # Input fields for API key and model name
    api_key_input = st.text_input("OpenAI API Key", value=st.session_state['openai_api_key'], type="password")
    model_options = ["gpt-3.5-turbo", "gpt-4o", "gpt-4o-mini", "gpt-4"]
    model_name_input = st.selectbox("OpenAI Model Name", options=model_options, index=model_options.index(st.session_state['gpt_model']) if st.session_state['gpt_model'] in model_options else None)
    def save_configuration():
        # Update session state with the new configuration values
        st.session_state['openai_api_key'] = api_key_input
        st.session_state['gpt_model'] = model_name_input
        update_env_variable("OPENAI_API_KEY", api_key_input)
        st.session_state['openai_api_key'] = api_key_input
        update_env_variable("GPT_MODEL", model_name_input)
        st.session_state['gpt_model'] = model_name_input
        load_dotenv()
        st.success("Configuration saved successfully!")

    # Save configuration button with the callback function
    st.button("Save Configuration", on_click=save_configuration)


# Tab structure
tab1, tab2, tab3 = st.tabs(["Reporting", "Configure Database", "API Configuration"])

with tab1:
    generate_reports()
with tab2:
    configure_database()
with tab3:
    configure_openai_api()


    
