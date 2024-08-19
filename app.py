import streamlit as st
import os
import subprocess
import logging
from pathlib import Path
from io import StringIO


def set_permissions(path):
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            os.chmod(dir_path, 0o777)  # or 0o755
        for file in files:
            file_path = os.path.join(root, file)
            os.chmod(file_path, 0o666)  # or 0o644

set_permissions('./uploads')

# Create 'uploads' directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Clean the 'uploads' directory before starting
for file in UPLOAD_DIR.glob('*'):
    if file.is_file():
        file.unlink()
# Clean the subfolders in uploads before starting
for subdir in UPLOAD_DIR.glob('*'):
    if subdir.is_dir():
        for file in subdir.glob('*'):
            if file.is_file():
                file.unlink()

def run_marker(input_folder, output_folder):
    command = f"marker {input_folder} {output_folder} --workers 2"

    subprocess.run(command, shell=True, capture_output=True, text=True)

def read_markdown_files(folder):
    # Convert the folder string to a Path object
    folder_path = Path(folder)

    markdown_files = []
    for subdir in folder_path.iterdir(): # Use iterdir() on Path object
        if subdir.is_dir():
            for md_file in subdir.glob("*.md"):
                with open(md_file, 'r') as f:
                    content = f.read()
                    markdown_files.append((md_file.name, content))
    return markdown_files

st.title("PDF to Markdown Converter")

uploaded_files = st.file_uploader("Choose PDF files", accept_multiple_files=True, type="pdf")

if st.button("Convert PDFs"):
    if uploaded_files:
        with st.spinner("Converting PDFs..."):
            # Save uploaded files to 'uploads' directory
            for uploaded_file in uploaded_files:
                file_path = UPLOAD_DIR / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                logging.info(f"Saved file: {file_path}")

            # Run marker on the 'uploads' directory
            try:
                run_marker('./uploads', './uploads')

                # wait for 5 seconds
            except Exception as e:
                st.error(f"An error occurred during conversion: {str(e)}")
                logging.exception("Error during conversion")

            # Read the output markdown files
            markdown_files = read_markdown_files('./uploads')

            if markdown_files:
                    # Store results in session state
                st.session_state.conversion_results = markdown_files
                st.success("Conversion completed successfully!")
            else:
                st.warning("No markdown files were generated. Check the logs for details.")
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

# Display logs
# st.header("Logs")
# with st.expander("View Logs"):
#     st.text(log_stream.getvalue())

# Display contents of output directory
st.header("Output Directory Contents")
output_files = list(UPLOAD_DIR.glob('*'))
st.write(f"Files in output directory: {[f.name for f in output_files if f.is_file()]}")

st.write("Upload PDF files and click 'Convert PDFs' to convert them to Markdown.")
