import streamlit as st
from concurrent.futures import ProcessPoolExecutor
import subprocess
from pathlib import Path
import time
from PyPDF2 import PdfReader, PdfWriter
import shutil
import os
import uuid
import tempfile

# Hardcoded params
CHUNK_SIZE = 5  # number of pages per chunk
MARKER_WORKERS = 4  # Adjust based on available RAM


# split PDF into chunks with metadata tracking
def split_pdf(input_pdf_path, temp_dir):
    input_pdf = PdfReader(str(input_pdf_path))
    file_name = input_pdf_path.name
    file_id = str(uuid.uuid4())  # Generate a unique ID for the file
    pdf_chunks = []

    for i in range(0, len(input_pdf.pages), CHUNK_SIZE):
        pdf_writer = PdfWriter()
        start_page = i + 1
        end_page = min(i + CHUNK_SIZE, len(input_pdf.pages))

        for j in range(i, end_page):
            pdf_writer.add_page(input_pdf.pages[j])

        chunk_file_name = f"{file_id}_chunk_{start_page}_{end_page}.pdf"
        chunk_path = temp_dir / chunk_file_name

        with open(chunk_path, "wb") as f:
            pdf_writer.write(f)

        pdf_chunks.append(
            {
                "file_id": file_id,
                "original_file": file_name,
                "chunk_file": chunk_path,
                "start_page": start_page,
                "end_page": end_page,
            }
        )

    return pdf_chunks


# run marker on all chunks in the input directory
def run_marker_on_chunks(input_dir, output_dir):
    command = f"marker {input_dir} {output_dir} --workers {MARKER_WORKERS}"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Marker command failed: {result.stderr}")
    return result.stdout


# merge results back together
def merge_results(chunks, output_dir):
    results = {}
    sorted_chunks = sorted(chunks, key=lambda x: (x["file_id"], x["start_page"]))

    for chunk in sorted_chunks:
        file_id = chunk["file_id"]
        chunk_folder = output_dir / chunk["chunk_file"].stem
        md_file = chunk_folder / f"{chunk['chunk_file'].stem}.md"

        if md_file.exists():
            with open(md_file, "r") as f:
                content = f.read()
                if file_id not in results:
                    results[file_id] = {
                        "original_file": chunk["original_file"],
                        "content": [],
                    }
                results[file_id]["content"].append(content)

            # Remove the chunk and its output after processing
            os.remove(chunk["chunk_file"])
            shutil.rmtree(chunk_folder)
        else:
            raise FileNotFoundError(f"Markdown file not found: {md_file}")

    final_results = []
    for file_id, data in results.items():
        final_results.append((data["original_file"], "\n".join(data["content"])))

    return final_results


# handle the parallel splitting of PDFs
def parallel_pdf_splitting(uploaded_files, temp_dir):
    with ProcessPoolExecutor() as executor:
        futures = []
        for uploaded_file in uploaded_files:
            if uploaded_file.name.endswith(".pdf"):
                file_path = temp_dir / uploaded_file.name
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                futures.append(executor.submit(split_pdf, file_path, temp_dir))

        chunk_metadata = []
        for future in futures:
            chunk_metadata.extend(future.result())

    return chunk_metadata


# Function to handle the entire processing workflow
def process_files(uploaded_files):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        output_dir = temp_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)

        chunk_metadata = parallel_pdf_splitting(uploaded_files, temp_dir)

        # Display chunked files in the Streamlit app
        st.write("### Chunked Files")
        for chunk in chunk_metadata:
            st.write(
                f"{chunk['original_file']} - Chunk {chunk['start_page']} to {chunk['end_page']}"
            )

        if chunk_metadata:
            try:
                # run_marker_on_chunks(temp_dir, output_dir)
                marker_output = run_marker_on_chunks(temp_dir, output_dir)
                st.text(f"Marker output: {marker_output}")

                # Merge and display the results
                file_results = merge_results(chunk_metadata, output_dir)
                st.write("### Processed Files")
                for filename, _ in file_results:
                    st.write(filename)

                return file_results
            except Exception as e:
                st.error(f"An error occurred during PDF processing: {str(e)}")
                return []


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
                st.warning("No files were processed.")
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
