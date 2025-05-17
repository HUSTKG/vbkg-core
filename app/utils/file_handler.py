import logging
import mimetypes
import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import UploadFile

# Try importing libraries for different file types
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import docx
except ImportError:
    docx = None

try:
    import csv
except ImportError:
    csv = None

try:
    import json
except ImportError:
    json = None

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import openpyxl
    import xlrd
except ImportError:
    xlrd = None
    openpyxl = None

logger = logging.getLogger(__name__)

TEMP_UPLOAD_DIR = tempfile.gettempdir() + "/kg_uploads"


def ensure_temp_dir():
    """Ensure temporary upload directory exists."""
    os.makedirs(TEMP_UPLOAD_DIR, exist_ok=True)


async def save_upload_file(upload_file: UploadFile) -> str:
    """
    Save an uploaded file to a temporary location.

    Args:
        upload_file: The uploaded file

    Returns:
        Path to the saved file
    """
    ensure_temp_dir()

    # Generate a unique filename
    file_extension = os.path.splitext(upload_file.filename)[1]
    temp_filename = f"{next(tempfile._get_candidate_names())}{file_extension}"
    file_path = os.path.join(TEMP_UPLOAD_DIR, temp_filename)

    # Save the file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)

    return file_path


def get_file_type(
    filename: Optional[str] = None, content_type: Optional[str] = None
) -> str:
    """
    Determine file type from filename and content type.

    Args:
        filename: Name of the file
        content_type: MIME type of the file

    Returns:
        Simplified file type string
    """

    if filename is None and content_type is None:
        raise ValueError("Either filename or content_type must be provided")

    if filename:
        extension = os.path.splitext(filename)[1].lower()

        # Text-based files
        if extension in [".txt", ".md"]:
            return "text"

        # HTML files
        if extension in [".html", ".htm"]:
            return "html"

        # PDF files
        if extension == ".pdf":
            return "pdf"

        # Word documents
        if extension in [".doc", ".docx"]:
            return "docx"

        # CSV files
        if extension == ".csv":
            return "csv"

        # JSON files
        if extension == ".json":
            return "json"

        # Excel files
        if extension in [".xls", ".xlsx"]:
            return "excel"

        # XML files
        if extension == ".xml":
            return "xml"

    # Fall back to content_type
    if content_type:
        if "text/plain" in content_type:
            return "text"
        elif "text/html" in content_type:
            return "html"
        elif "application/pdf" in content_type:
            return "pdf"
        elif (
            "application/msword" in content_type
            or "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            in content_type
        ):
            return "docx"
        elif "text/csv" in content_type:
            return "csv"
        elif "application/json" in content_type:
            return "json"
        elif (
            "application/vnd.ms-excel" in content_type
            or "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            in content_type
        ):
            return "excel"
        elif "application/xml" in content_type:
            return "xml"

    # Default
    return "text"


async def parse_file_content(file_path: str, file_type: str) -> Optional[str]:
    """
    Parse file content based on file type.

    Args:
        file_path: Path to the file
        file_type: Type of the file

    Returns:
        Extracted text content or None on error
    """
    try:
        if file_type == "text":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        elif file_type == "html":
            if BeautifulSoup is None:
                logger.warning("BeautifulSoup is not installed. Cannot parse HTML.")
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()

            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                soup = BeautifulSoup(f, "html.parser")
                return soup.get_text(separator="\n")

        elif file_type == "pdf":
            if PyPDF2 is None:
                logger.warning("PyPDF2 is not installed. Cannot parse PDF.")
                return None

            text = []
            with open(file_path, "rb") as f:
                pdf_reader = PyPDF2.PdfReader(f)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text.append(page.extract_text())

            return "\n\n".join(text)

        elif file_type == "docx":
            if docx is None:
                logger.warning("python-docx is not installed. Cannot parse DOCX.")
                return None

            doc = docx.Document(file_path)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])

        elif file_type == "csv":
            if pd is None:
                logger.warning("pandas is not installed. Cannot parse CSV.")
                return None

            df = pd.read_csv(file_path)
            return df.to_string()

        elif file_type == "json":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            return json.dumps(data, indent=2)

        elif file_type == "excel":
            if pd is None:
                logger.warning("pandas is not installed. Cannot parse Excel.")
                return None

            df = pd.read_excel(file_path)
            return df.to_string()

        elif file_type == "xml":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read()

        else:
            logger.warning(f"Unsupported file type: {file_type}")
            return None

    except Exception as e:
        logger.error(f"Error parsing file {file_path}: {e}")
        return None


async def parse_structured_data(
    file_path: str, file_type: str
) -> Optional[Dict[str, Any]]:
    """
    Parse structured data from file.

    Args:
        file_path: Path to the file
        file_type: Type of the file

    Returns:
        Structured data or None on error
    """
    try:
        if file_type == "csv":
            if pd is None:
                logger.warning("pandas is not installed. Cannot parse CSV.")
                return None

            df = pd.read_csv(file_path)
            return {
                "columns": df.columns.tolist(),
                "data": df.to_dict(orient="records"),
                "shape": df.shape,
            }

        elif file_type == "json":
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
            return data

        elif file_type == "excel":
            if pd is None:
                logger.warning("pandas is not installed. Cannot parse Excel.")
                return None

            # Read all sheets
            excel_data = {}
            xlsx = pd.ExcelFile(file_path)
            for sheet_name in xlsx.sheet_names:
                df = pd.read_excel(xlsx, sheet_name=sheet_name)
                excel_data[sheet_name] = {
                    "columns": df.columns.tolist(),
                    "data": df.to_dict(orient="records"),
                    "shape": df.shape,
                }

            return excel_data

        else:
            logger.warning(f"File type {file_type} is not structured data format")
            return None

    except Exception as e:
        logger.error(f"Error parsing structured data from {file_path}: {e}")
        return None
