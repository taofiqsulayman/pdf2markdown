import boto3
import subprocess
import tempfile
from pathlib import Path
import pandas as pd
from docx import Document
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
import json

# Initialize the S3 client
s3 = boto3.client('s3')

# Helper function to download files from S3
def download_file_from_s3(bucket, key, download_path):
    s3.download_file(bucket, key, download_path)

# Helper function to upload files to S3
def upload_file_to_s3(bucket, key, file_path):
    s3.upload_file(file_path, bucket, key)

# Convert images to PDFs
def image_to_pdf(image_path, pdf_path):
    img = Image.open(image_path)
    img_reader = ImageReader(image_path)
    can = canvas.Canvas(str(pdf_path), pagesize=img.size)
    can.drawImage(img_reader, 0, 0, width=img.width, height=img.height)
    can.save()

# Run marker command for PDFs
def run_marker(input_folder, output_folder):
    command = f"marker {input_folder} {output_folder} --workers 4"
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Marker command failed: {result.stderr}")
    return result.stdout

# Read Markdown files from output folder
def read_markdown_files(folder):
    markdown_files = []
    for subdir in folder.iterdir():
        if subdir.is_dir():
            for md_file in subdir.glob("*.md"):
                with open(md_file, "r") as f:
                    content = f.read()
                    markdown_files.append((md_file.name, content))
    return markdown_files

# CSV and Excel processors
def process_csv(file_path):
    df = pd.read_csv(file_path)
    return df.to_markdown()

def process_excel(file_path):
    df = pd.read_excel(file_path)
    return df.to_markdown()

# Word processor
def process_word(file_path):
    doc = Document(file_path)
    full_text = [para.text for para in doc.paragraphs]
    return "\n\n".join(full_text)

# Main function to process files from S3
def process_files(files):
    results = []
    with tempfile.TemporaryDirectory() as temp_dir:
        input_dir = Path(temp_dir) / "input"
        output_dir = Path(temp_dir) / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Loop over files and process based on file type
        for file_info in files:
            bucket = file_info['bucket']
            key = file_info['key']
            file_name = os.path.basename(key)
            local_file_path = input_dir / file_name

            # Download file from S3
            download_file_from_s3(bucket, key, str(local_file_path))

            # Process based on file type
            if file_name.endswith((".pdf", ".jpg", ".jpeg", ".png")):
                # Convert image to PDF if necessary
                if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
                    pdf_path = local_file_path.with_suffix(".pdf")
                    image_to_pdf(str(local_file_path), str(pdf_path))
                    local_file_path.unlink()  # Remove original image file
                    local_file_path = pdf_path

            elif file_name.endswith(".csv"):
                results.append((file_name, process_csv(str(local_file_path))))
                continue

            elif file_name.endswith(".xlsx"):
                results.append((file_name, process_excel(str(local_file_path))))
                continue

            elif file_name.endswith(".docx"):
                results.append((file_name, process_word(str(local_file_path))))
                continue

        # Process PDFs with Marker (including converted images)
        if list(input_dir.glob("*.pdf")):
            try:
                marker_output = run_marker(str(input_dir), str(output_dir))
                print(f"Marker output: {marker_output}")
                pdf_results = read_markdown_files(output_dir)
                results.extend(pdf_results)
            except Exception as e:
                print(f"An error occurred during PDF processing: {str(e)}")

    return results

# AWS Batch job entry point
def handler(event, context):
    # Extract file information from environment variables or event input
    files = json.loads(os.environ['FILES'])
    results_bucket = os.environ['RESULTS_BUCKET']

    # Process files
    results = process_files(files)

    # Upload the results back to S3
    for filename, content in results:
        result_key = f"results/{filename}.md"
        result_file_path = f"/tmp/{filename}.md"
        with open(result_file_path, "w") as f:
            f.write(content)
        upload_file_to_s3(results_bucket, result_key, result_file_path)

    return {"status": "Completed", "processed_files": len(files)}
