

# File Converter and Viewer

## Table of Contents
1. [Description](#description)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Use Cases](#use-cases)
7. [Troubleshooting](#troubleshooting)
8. [Contact](#contact)

## Description

The File Converter and Viewer is a powerful Streamlit application that allows users to upload, process, and view various file types including PDFs, images, CSV, Excel, and Word documents. It leverages the marker-pdf library to convert PDFs and images into markdown format, providing a unified viewing experience for all file types.

## Features

- Upload multiple files of different types (PDF, JPG, PNG, CSV, XLSX, DOCX)
- Convert images to PDF for unified processing
- Process PDFs and images using the marker-pdf library
- Convert CSV and Excel files to markdown format
- Extract text from Word documents
- Display processed content in an interactive Streamlit interface

## Requirements

- Python 3.7+
- Streamlit
- pandas
- openpyxl
- python-docx
- Pillow
- reportlab
- marker-pdf
- PyTorch (CPU or GPU version)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/taofiqsulayman/pdf2markdown.git
   cd pdf2markdown
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

4. Install PyTorch and related packages:

   For CPU:
   ```
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
   ```

   For GPU (CUDA 11.8):
   ```
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

   ``` For specific PyTorch and related package based on your hardware, "visit: https://pytorch.org/get-started/locally/" ```

5. Install marker-pdf:
   ```
   pip install marker-pdf
   ```

   Note for Mac users:
   ```
   pip install pdftext==0.3.7 marker_pdf==0.2.6
   ```

## Usage

1. Ensure you're in the project directory and your virtual environment is activated.

2. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

3. Open your web browser and go to the URL provided by Streamlit (usually http://localhost:8501).

4. Use the file uploader to select one or more files of supported types.

5. Click the "Process Files" button to convert and view the files.

6. Explore the processed content in the expandable sections below.

## Use Cases

1. **Document Conversion**: Quickly convert PDFs and images to markdown format for easy viewing and sharing.
2. **Data Analysis**: Upload CSV or Excel files to view their contents in a formatted markdown table.
3. **Text Extraction**: Extract and view text content from Word documents.
4. **Batch Processing**: Process multiple files of different types in a single operation.
5. **Content Aggregation**: Combine content from various file types into a single, easy-to-navigate interface.

## Troubleshooting

- If you encounter issues with PDF processing, ensure that the `marker` command is properly installed and accessible in your system's PATH.
- For image processing problems, check that you have the necessary dependencies for image-to-PDF conversion (Pillow and reportlab).
- If you're using a GPU and experiencing CUDA errors, make sure you've installed the correct version of PyTorch for your CUDA version.
- For Mac users experiencing issues with pdftext or marker_pdf, try the specific versions mentioned in the installation notes.

## Contact

For any questions, issues, or suggestions, please open an issue on the GitHub repository or contact the maintainer at [sulaymantaofiq@gmail.com].

