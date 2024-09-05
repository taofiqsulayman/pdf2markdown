import streamlit as st
import subprocess
from pathlib import Path
import time
import tempfile
from PyPDF2 import PdfReader, PdfWriter
import uuid
import shutil
from spire.doc import Document
import csv
import base64

# Constants
BATCH_MULTIPLIER = 4
MAX_PAGES = None
WORKERS = 1
CHUNK_SIZE = 20

def split_pdf(input_pdf_path, output_dir, chunk_size=CHUNK_SIZE):
    input_pdf = PdfReader(str(input_pdf_path))
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

        pdf_chunks.append({
            "file_id": file_id,
            "original_file": input_pdf_path.name,
            "chunk_file": chunk_path,
            "start_page": start_page,
            "end_page": end_page,
        })

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

    final_results = []
    for file_id, data in results.items():
        sorted_content = sorted(data["content"], key=lambda x: x[0])
        merged_content = "\n".join([content for _, content in sorted_content])
        final_results.append((data["original_file"], merged_content))

    return final_results

def extract_text_from_pdf(pdf_reader):
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text() + "\n"
    return text

def process_pdf(file_path, output_dir):
    input_pdf = PdfReader(str(file_path))
    total_pages = len(input_pdf.pages)

    if total_pages <= CHUNK_SIZE:
        content = extract_text_from_pdf(input_pdf)
        return content
    else:
        chunks = split_pdf(file_path, output_dir)
        processed_chunks = []
        for chunk in chunks:
            processed_chunk = process_chunk(chunk, output_dir)
            processed_chunks.append(processed_chunk)
        
        merged_results = merge_chunk_results(processed_chunks, output_dir)
        if merged_results:
            return merged_results[0][1]
        else:
            return ""

def process_docx(file_path):
    document = Document()
    document.LoadFromFile(str(file_path))
    return document.GetText()

def process_csv(file_path):
    with open(file_path, 'r') as f:
        reader = csv.reader(f)
        return "\n".join([",".join(row) for row in reader])

def process_txt(file_path):
    with open(file_path, 'r') as f:
        return f.read()

def process_file(file_path, output_dir):
    file_extension = file_path.suffix.lower()
    if file_extension == '.pdf':
        return process_pdf(file_path, output_dir)
    elif file_extension == '.docx' or file_extension == '.doc':
        return process_docx(file_path)
    elif file_extension == '.csv':
        return process_csv(file_path)
    elif file_extension == '.txt':
        return process_txt(file_path)
    else:
        raise ValueError(f"Unsupported file type: {file_extension}")

def process_files(uploaded_files):
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir = Path(temp_dir)
        input_dir = temp_dir / "input"
        output_dir = temp_dir / "output"
        input_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        for uploaded_file in uploaded_files:
            file_path = input_dir / uploaded_file.name
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

        results = []
        for file_path in input_dir.glob("*"):
            # st.write(f"Processing: {file_path.name}")
            try:
                result = process_file(file_path, output_dir)
                results.append((file_path.name, result))
            except Exception as e:
                st.error(f"Error processing {file_path.name}: {str(e)}")

        # Clean up temporary files
        shutil.rmtree(input_dir)
        shutil.rmtree(output_dir)

        return results

def get_download_link(text, filename):
    b64 = base64.b64encode(text.encode()).decode()
    return f'<a href="data:text/plain;base64,{b64}" download="{filename}">Download {filename}</a>'

# Streamlit app setup and logic
st.set_page_config(page_title="File Extractor and Viewer", page_icon="📂", layout="wide")
st.title("File Extractor and Viewer")

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

uploaded_files = st.file_uploader(
    "Choose files", accept_multiple_files=True, type=["pdf", "docx", "csv", "txt", "doc"]
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
            st.markdown(get_download_link(content, f"extracted_{filename}.txt"), unsafe_allow_html=True)
    end_time_result = time.time()
    st.text(f"Total result visualization time: {end_time_result - start_time_result:.2f} seconds")
else:
    st.info("No processing results yet. Upload files and click 'Process Files' to see results here.")

st.write("Upload files and click 'Process Files' to convert or view them.")