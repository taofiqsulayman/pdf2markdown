import streamlit as st
import os
import subprocess
import logging
from pathlib import Path
from io import StringIO
import tempfile

def run_marker(input_folder, output_folder):
    command = f"marker {input_folder} {output_folder} --workers 1"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Marker command failed: {result.stderr}")
    return result.stdout

def read_markdown_files(folder):
    markdown_files = []
    for subdir in folder.iterdir():
        if subdir.is_dir():
            for md_file in subdir.glob("*.md"):
                with open(md_file, 'r') as f:
                    content = f.read()
                    markdown_files.append((md_file.name, content))
    return markdown_files

st.title("PDF to Markdown Converter")

# Use session state to store uploaded files
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []

uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True, type="pdf")

if uploaded_files:
    st.session_state.uploaded_files = uploaded_files

if st.button("Convert PDFs"):
    if st.session_state.uploaded_files:
        with st.spinner("Converting PDFs..."):
            # Create temporary directories for input and output
            with tempfile.TemporaryDirectory() as input_dir, tempfile.TemporaryDirectory() as output_dir:
                input_path = Path(input_dir)
                output_path = Path(output_dir)

                # Save uploaded files to temporary input directory
                for uploaded_file in st.session_state.uploaded_files:
                    file_path = input_path / uploaded_file.name
                    with open(file_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                # Run marker on the temporary directories
                try:
                    marker_output = run_marker(input_dir, output_dir)
                    # st.text(f"Marker output: {marker_output}")
                except Exception as e:
                    st.error(f"An error occurred during conversion: {str(e)}")
                    st.stop()

                # Read the output markdown files
                markdown_files = read_markdown_files(output_path)

                if markdown_files:
                    # Store results in session state
                    st.session_state.conversion_results = markdown_files
                    st.success("Conversion completed successfully!")
                else:
                    st.warning("No markdown files were generated.")

                # Display contents of output directory
                st.header("Output Directory Contents")
                output_files = list(output_path.glob('*'))
                st.write(f"Files in output directory: {[f.name for f in output_files if f.is_file()]}")

    else:
        st.warning("Please upload PDF files before converting.")

# Results section
st.header("Conversion Results")

if 'conversion_results' in st.session_state:
    for filename, content in st.session_state.conversion_results:
        with st.expander(f"Contents of {filename}"):
            st.text(f"Content length: {len(content)} characters")
            st.markdown(content)
else:
    st.info("No conversion results yet. Upload PDFs and click 'Convert PDFs' to see results here.")

st.write("Upload PDF files and click 'Convert PDFs' to convert them to Markdown.")
