import streamlit as st
from concurrent.futures import ProcessPoolExecutor
import subprocess
from pathlib import Path
import time
import tempfile
import os
import json

# Constants
BATCH_MULTIPLIER = 4  # Adjust based on your VRAM capacity
MAX_PAGES = None  # Set to None to process entire documents, or specify a number
WORKERS = 1  # Since we're leveraging GPU, we'll process one file at a time


def run_marker_on_file(input_file, output_dir):
    command = f"marker_single '{input_file}' '{output_dir}' --batch_multiplier {BATCH_MULTIPLIER}"
    if MAX_PAGES:
        command += f" --max_pages {MAX_PAGES}"

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Marker command failed for {input_file}: {result.stderr}")

    return result.stdout


def extract_all_files(input_dir, output_dir):
    """Runs the marker tool on all files in the input directory."""
    for file_path in input_dir.glob("*.pdf"):
        output_dir.mkdir(parents=True, exist_ok=True)
        run_marker_on_file(file_path, output_dir)


def read_markdown_files(folder):
    """Reads all markdown files from the specified folder and its subdirectories."""
    markdown_files = []
    for subdir in folder.iterdir():
        if subdir.is_dir():
            for md_file in subdir.glob("*.md"):
                with open(md_file, "r") as f:
                    content = f.read()
                markdown_files.append((md_file.name, content))
    return markdown_files


def process_files(uploaded_files):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded files to temporary directory
        for uploaded_file in uploaded_files:
            file_path = input_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        # Step 1: Run marker on all files
        extract_all_files(input_dir, output_dir)

        # Step 2: Read all markdown files from the output directory
        results = read_markdown_files(output_dir)

        return results


# Streamlit app setup and logic
st.set_page_config(
    page_title="File Extractor and Viewer", page_icon="📂", layout="wide"
)
st.title("File Extractor and Viewer")

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

uploaded_files = st.file_uploader(
    "Choose files", accept_multiple_files=True, type=["pdf"]
)

if uploaded_files:
    st.session_state.uploaded_files = uploaded_files

if st.button("Process Files"):
    if st.session_state.uploaded_files:
        with st.spinner("Processing files..."):
            start_time = time.time()
            results = process_files(st.session_state.uploaded_files)

            if results:
                st.session_state.conversion_results = results
                end_time = time.time()
                st.success("Files processed successfully!")
                st.text(f"Total processing time: {end_time - start_time:.2f} seconds")
            else:
                st.warning("No files were processed successfully.")
    else:
        st.warning("Please upload files before processing.")

st.header("Results")

if "conversion_results" in st.session_state:
    start_time_result = time.time()
    st.write("Starting visualization ....")
    for filename, content in st.session_state.conversion_results:
        with st.expander(f"Contents of {filename}"):
            st.text(f"Content length: {len(content)} characters")
            st.markdown(content)
    end_time_result = time.time()
    st.text(
        f"Total result visualization time: {end_time_result - start_time_result:.2f} seconds"
    )
else:
    st.info(
        "No processing results yet. Upload files and click 'Process Files' to see results here."
    )

st.write("Upload files and click 'Process Files' to convert or view them.")
