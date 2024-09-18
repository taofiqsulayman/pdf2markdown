import streamlit as st
import subprocess
from pathlib import Path
import tempfile
import pandas as pd
from spire.doc import Document
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import time
import os

def set_permissions(path):
    for root, dirs, files in os.walk(path):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            os.chmod(dir_path, 0o777)  # or 0o755
        for file in files:
            file_path = os.path.join(root, file)
            os.chmod(file_path, 0o666)  # or 0o644

set_permissions('./uploads')
set_permissions('./output')


def run_marker(input_folder, output_folder, min_length=10000, num_devices=4, num_workers=15, metadata_file=None):
    # Build the command with environment variables in the specified format
    env_vars = (
        f"MIN_LENGTH={min_length} "
        f"NUM_DEVICES={num_devices} "
        f"NUM_WORKERS={num_workers} "
    )

    # Add METADATA_FILE if provided
    if metadata_file:
        env_vars += f"METADATA_FILE={metadata_file} "

    command = f"{env_vars} marker_chunk_convert {input_folder} {output_folder}"
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Marker command failed: {result.stderr}")
    
    return result.stdout


def read_markdown_files(folder):
    markdown_files = []
    for subdir in folder.iterdir():
        if subdir.is_dir():
            for md_file in subdir.glob("*.md"):
                with open(md_file, "r") as f:
                    content = f.read()
                    markdown_files.append((md_file.name, content))
    return markdown_files


def process_csv(file):
    df = pd.read_csv(file)
    return df.to_markdown()


def process_excel(file):
    df = pd.read_excel(file)
    return df.to_markdown()


def process_word(file_path):
    document = Document()
    document.LoadFromFile(str(file_path))
    return document.GetText()


def image_to_pdf(image_path, pdf_path):
    img = Image.open(image_path)
    img_reader = ImageReader(image_path)
    can = canvas.Canvas(str(pdf_path), pagesize=img.size)
    can.drawImage(img_reader, 0, 0, width=img.width, height=img.height)
    can.save()


st.set_page_config(page_title="File Extractor and Viewer", page_icon="📂", layout="wide")
st.title("File Extractor and Viewer")

# Use session state to store uploaded files
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

uploaded_files = st.file_uploader(
    "Choose files",
    accept_multiple_files=True,
    type=["pdf", "csv", "xlsx", "docx", "jpg", "jpeg", "png"],
)

if uploaded_files:
    st.session_state.uploaded_files = uploaded_files

if st.button("Process Files"):
    if st.session_state.uploaded_files:
        with st.spinner("Processing files..."):
            start_time = time.time()
            results = []

            # Create temporary directory for input and output
            with tempfile.TemporaryDirectory() as temp_dir:
                input_dir = Path(temp_dir) / "input"
                output_dir = Path("./output")
                output_dir.mkdir(parents=True, exist_ok=True)
                                
                input_dir.mkdir()

                for uploaded_file in st.session_state.uploaded_files:
                    if uploaded_file.name.endswith((".pdf", ".jpg", ".jpeg", ".png")):
                        # Save file to temporary input directory
                        file_path = input_dir / uploaded_file.name
                        with open(file_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())

                        # Convert image to PDF if necessary
                        if file_path.suffix.lower() in (".jpg", ".jpeg", ".png"):
                            pdf_path = file_path.with_suffix(".pdf")
                            image_to_pdf(str(file_path), str(pdf_path))
                            file_path.unlink()  # Remove original image file

                    elif uploaded_file.name.endswith(".csv"):
                        results.append((uploaded_file.name, process_csv(uploaded_file)))
                    elif uploaded_file.name.endswith(".xlsx"):
                        results.append((uploaded_file.name, process_excel(uploaded_file)))
                    elif uploaded_file.name.endswith(".docx"):
                        results.append((uploaded_file.name, process_word(uploaded_file)))

                # Process PDFs (including converted images)
                if list(input_dir.glob("*.pdf")):
                    try:
                        # Call the marker processing function with multiple GPUs
                        marker_output = run_marker(
                            input_folder=str(input_dir),
                            output_folder=str(output_dir),
                            min_length=0,  # Minimum characters to consider
                            num_devices=4,     # Number of GPUs
                            num_workers=15,    # Number of workers per GPU
                            # metadata_file="../pdf_meta.json"  # Optional metadata file
                        )
                        st.text(f"Marker output: {marker_output}")

                        pdf_results = read_markdown_files(output_dir)
                        results.extend(pdf_results)
                    except Exception as e:
                        st.error(f"An error occurred during PDF conversion: {str(e)}")

            if results:
                # Store results in session state
                st.session_state.conversion_results = results
                end_time = time.time()
                st.success("Files processed successfully!")
                st.text(f"Total processing time: {end_time - start_time:.2f} seconds")
            else:
                st.warning("No files were processed.")
    else:
        st.warning("Please upload files before processing.")

st.header("Results")

if "conversion_results" in st.session_state:
    start_time_result = time.time()
    st.write('starting visualization ....')
    for filename, content in st.session_state.conversion_results:
        with st.expander(f"Contents of {filename}"):
            st.text(f"Content length: {len(content)} characters")
            st.markdown(content)
    end_time_result = time.time()
    st.text(f"Total result visualization time: {end_time_result - start_time_result:.2f} seconds")
else:
    st.info(
        "No processing results yet. Upload files and click 'Process Files' to see results here."
    )

st.write("Upload files and click 'Process Files' to convert or view them.")
