import streamlit as st
from concurrent.futures import ProcessPoolExecutor
import subprocess
from pathlib import Path
import time
import tempfile
import os
import json
from PyPDF2 import PdfReader, PdfWriter
import uuid
import shutil

# Constants
BATCH_MULTIPLIER = 4  # Adjust based on your VRAM capacity
MAX_PAGES = None  # Set to None to process entire documents, or specify a number
WORKERS = 1  # Since we're leveraging GPU, we'll process one file at a time
CHUNK_SIZE = 20  # Number of pages per chunk


def split_pdf(input_pdf_path, output_dir, chunk_size=CHUNK_SIZE):
    input_pdf = PdfReader(str(input_pdf_path))
    file_name = input_pdf_path.stem
    file_id = str(uuid.uuid4())
    pdf_chunks = []

    for i in range(0, len(input_pdf.pages), chunk_size):
        pdf_writer = PdfWriter()
        start_page = i + 1
        end_page = min(i + chunk_size, len(input_pdf.pages))

        for j in range(i, end_page):
            pdf_writer.add_page(input_pdf.pages[j])

        chunk_file_name = f"{file_id}_chunk_{start_page}_{end_page}.pdf"
        chunk_path = output_dir / chunk_file_name

        with open(chunk_path, "wb") as f:
            pdf_writer.write(f)

        pdf_chunks.append(
            {
                "file_id": file_id,
                "original_file": input_pdf_path.name,
                "chunk_file": chunk_path,
                "start_page": start_page,
                "end_page": end_page,
            }
        )

    # Delete the original file after chunking
    os.remove(input_pdf_path)

    return pdf_chunks


def run_marker_on_file(input_file, output_dir):
    command = f"marker_single '{input_file}' '{output_dir}' --batch_multiplier {BATCH_MULTIPLIER}"
    if MAX_PAGES:
        command += f" --max_pages {MAX_PAGES}"

    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Marker command failed for {input_file}: {result.stderr}")

    return result.stdout


def process_chunk(chunk, output_dir):
    chunk_output_dir = output_dir / chunk["original_file"].rsplit(".", 1)[0]
    chunk_output_dir.mkdir(parents=True, exist_ok=True)
    run_marker_on_file(chunk["chunk_file"], chunk_output_dir)

    # Delete the chunk file after processing
    os.remove(chunk["chunk_file"])

    return chunk


def merge_chunk_results(chunks, output_dir):
    results = {}
    for chunk in chunks:
        file_id = chunk["file_id"]
        original_file = chunk["original_file"]
        chunk_folder = output_dir / original_file.rsplit(".", 1)[0] / chunk["chunk_file"].stem
        md_file = chunk_folder / f"{chunk['chunk_file'].stem}.md"

        if md_file.exists():
            with open(md_file, "r") as f:
                content = f.read()
                if file_id not in results:
                    results[file_id] = {"original_file": original_file, "content": []}
                results[file_id]["content"].append((chunk["start_page"], content))

            # Delete the chunk's markdown file after reading
            os.remove(md_file)

    final_results = []
    for file_id, data in results.items():
        sorted_content = sorted(data["content"], key=lambda x: x[0])
        merged_content = "\n".join([content for _, content in sorted_content])
        final_results.append((data["original_file"], merged_content))

        # Delete the output folder for this file
        shutil.rmtree(output_dir / data["original_file"].rsplit(".", 1)[0])

    return final_results


def process_files(uploaded_files):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        chunk_dir = temp_dir / "chunks"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)
        chunk_dir.mkdir(parents=True, exist_ok=True)

        # Save uploaded files to temporary directory
        for uploaded_file in uploaded_files:
            file_path = input_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        all_chunks = []
        for file_path in input_dir.glob("*.pdf"):
            chunks = split_pdf(file_path, chunk_dir)
            all_chunks.extend(chunks)

        # Process chunks
        processed_chunks = []
        for chunk in all_chunks:
            st.write(
                f"Processing: {chunk['original_file']} (Pages {chunk['start_page']}-{chunk['end_page']})"
            )
            processed_chunk = process_chunk(chunk, output_dir)
            processed_chunks.append(processed_chunk)

        # Merge results
        results = merge_chunk_results(processed_chunks, output_dir)

        return results


# Streamlit app setup and logic (unchanged)
# ... (rest of the Streamlit code remains the same)

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
