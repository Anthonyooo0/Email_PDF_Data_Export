#!/usr/bin/env python3
"""
Email PDF Processor - Downloads PDFs from emails, processes with OCR, exports to CSV

Installation Requirements:
pip install pandas pytesseract pdf2image pillow
sudo apt install tesseract-ocr poppler-utils

Usage:
python email_pdf_processor.py

This script:
1. Downloads PDF attachments from emails using IMAP
2. Processes PDFs using OCR to extract table data
3. Exports extracted data to CSV format
"""

import os
import sys
import time
import pandas as pd
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
import imaplib
import email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import base64
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CSV_OUTPUT_FILE = "extracted_pdf_data.csv"
DOWNLOAD_FOLDER = "downloaded_pdfs"

class EmailPDFDownloader:
    """Downloads PDF attachments from emails using IMAP"""
    
    def __init__(self, email_server: str, email_user: str, email_password: str, port: int = 993):
        self.email_server = email_server
        self.email_user = email_user
        self.email_password = email_password
        self.port = port
        self.mail = None
        
    def connect(self):
        """Connect to email server"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.email_server, self.port)
            self.mail.login(self.email_user, self.email_password)
            logger.info(f"Successfully connected to {self.email_server}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to email server: {str(e)}")
            return False
    
    def disconnect(self):
        """Disconnect from email server"""
        if self.mail:
            self.mail.close()
            self.mail.logout()
            logger.info("Disconnected from email server")
    
    def search_emails_with_pdfs(self, mailbox: str = "INBOX", search_criteria: str = "ALL"):
        """Search for emails with PDF attachments"""
        try:
            self.mail.select(mailbox)
            
            status, messages = self.mail.search(None, search_criteria)
            if status != "OK":
                logger.error("Failed to search emails")
                return []
            
            email_ids = messages[0].split()
            pdf_emails = []
            
            for email_id in email_ids[-10:]:  # Process last 10 emails
                status, msg_data = self.mail.fetch(email_id, "(RFC822)")
                if status != "OK":
                    continue
                
                email_message = email.message_from_bytes(msg_data[0][1])
                
                if self.has_pdf_attachment(email_message):
                    pdf_emails.append((email_id, email_message))
                    logger.info(f"Found email with PDF: {email_message.get('Subject', 'No Subject')}")
            
            return pdf_emails
            
        except Exception as e:
            logger.error(f"Error searching emails: {str(e)}")
            return []
    
    def has_pdf_attachment(self, email_message):
        """Check if email has PDF attachments"""
        for part in email_message.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename and filename.lower().endswith('.pdf'):
                    return True
        return False
    
    def download_pdf_attachments(self, email_message, download_folder: str):
        """Download PDF attachments from an email"""
        downloaded_files = []
        
        Path(download_folder).mkdir(exist_ok=True)
        
        for part in email_message.walk():
            if part.get_content_disposition() == "attachment":
                filename = part.get_filename()
                if filename and filename.lower().endswith('.pdf'):
                    
                    safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    unique_filename = f"{timestamp}_{safe_filename}"
                    
                    filepath = Path(download_folder) / unique_filename
                    
                    with open(filepath, 'wb') as f:
                        f.write(part.get_payload(decode=True))
                    
                    downloaded_files.append(str(filepath))
                    logger.info(f"Downloaded PDF: {filepath}")
        
        return downloaded_files

class PDFProcessor:
    """Processes PDFs using OCR to extract table data"""
    
    def extract_table_from_pdf(self, pdf_path: str) -> Optional[pd.DataFrame]:
        """Extract table from PDF using OCR"""
        try:
            logger.info(f"Processing PDF with OCR: {pdf_path}")
            
            images = convert_from_path(pdf_path, dpi=300)
            
            for page_num, image in enumerate(images):
                logger.info(f"Processing page {page_num + 1} with OCR...")
                
                ocr_text = pytesseract.image_to_string(image, config='--psm 6')
                
                if not ocr_text.strip():
                    continue
                
                df = self.parse_table_from_ocr_text(ocr_text)
                
                if df is not None and not df.empty:
                    logger.info(f"Found table on page {page_num + 1} with {len(df)} rows and {len(df.columns)} columns")
                    return df
            
            logger.warning("No tables found with OCR")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting table with OCR: {str(e)}")
            return None
    
    def parse_table_from_ocr_text(self, ocr_text: str) -> Optional[pd.DataFrame]:
        """Parse table structure from OCR extracted text using improved logic"""
        try:
            lines = [line.strip() for line in ocr_text.split('\n') if line.strip()]
            
            if len(lines) < 2:
                logger.warning(f"Not enough lines for table parsing: {len(lines)}")
                return None
            
            logger.info(f"Analyzing {len(lines)} lines of OCR text")
            
            header_indicators = ['id', 'name', 'contact', 'phone', 'email', 'department', 'invoice', 'client', 'amount', 'status', 'date', 'service', 'location']
            header_line = None
            header_index = -1
            
            for i, line in enumerate(lines):
                if any(indicator in line.lower() for indicator in header_indicators):
                    words = line.split()
                    if len(words) >= 3:  # Header should have multiple column names
                        header_line = line
                        header_index = i
                        logger.info(f"Found header line at index {i}: {repr(header_line)}")
                        break
            
            if not header_line:
                logger.warning("No header line found")
                return None
            
            header_parts = header_line.split()
            logger.info(f"Header parts: {header_parts}")
            
            data_lines = []
            for i in range(header_index + 1, len(lines)):
                line = lines[i]
                
                if any(word in line.lower() for word in ['notes:', 'approved', 'director', 'standards', 'technician:']):
                    continue
                
                if re.match(r'^[A-Z]\d+', line) or len(re.findall(r'\d+', line)) >= 2:
                    data_lines.append(line)
                    logger.debug(f"Found data line: {repr(line)}")
            
            logger.info(f"Found {len(data_lines)} data lines")
            
            if not data_lines:
                logger.warning("No data lines found")
                return None
            
            data_rows = []
            for line in data_lines:
                parts = line.split()
                data_rows.append(parts)
                logger.debug(f"Data row parts: {parts}")
            
            if len(data_rows[0]) >= 6:
                headers = ['Record_ID', 'Name_Client', 'Type_Department', 'Contact_Amount', 'Status_Location', 'Date_Info', 'Additional_1', 'Additional_2']
                headers = headers[:len(data_rows[0])]
            elif len(data_rows[0]) >= 4:
                headers = ['Record_ID', 'Name_Client', 'Contact_Amount', 'Status_Date'][:len(data_rows[0])]
            else:
                headers = [f'Column_{i+1}' for i in range(len(data_rows[0]))]
            
            logger.info(f"Using headers: {headers}")
            
            max_cols = len(headers)
            normalized_data = []
            for row in data_rows:
                if len(row) < max_cols:
                    row.extend(['N/A'] * (max_cols - len(row)))
                elif len(row) > max_cols:
                    row = row[:max_cols]
                normalized_data.append(row)
            
            if not normalized_data:
                logger.warning("No normalized data after processing")
                return None
            
            df = pd.DataFrame(normalized_data, columns=headers)
            
            df = df.fillna("N/A")
            df = df.replace("", "N/A")
            
            logger.info(f"Successfully parsed table with {len(df)} rows and {len(df.columns)} columns")
            logger.info(f"Final headers: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error parsing table from OCR text: {str(e)}")
            return None

class CSVExporter:
    """Exports extracted data to CSV format"""
    
    def __init__(self, csv_file: str):
        self.csv_file = csv_file
    
    def append_to_csv(self, df: pd.DataFrame, source_file: str = ""):
        """Append DataFrame to CSV file"""
        try:
            df_with_metadata = df.copy()
            df_with_metadata['Source_File'] = source_file
            df_with_metadata['Date_Processed'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            if os.path.exists(self.csv_file):
                existing_df = pd.read_csv(self.csv_file)
                combined_df = pd.concat([existing_df, df_with_metadata], ignore_index=True)
                combined_df.to_csv(self.csv_file, index=False)
                logger.info(f"Appended {len(df)} rows to existing CSV: {self.csv_file}")
            else:
                df_with_metadata.to_csv(self.csv_file, index=False)
                logger.info(f"Created new CSV file: {self.csv_file}")
                
        except Exception as e:
            logger.error(f"Error writing to CSV file: {str(e)}")

class EmailPDFAutomation:
    """Main automation class that orchestrates the email-to-CSV workflow"""
    
    def __init__(self, email_config: Dict[str, str]):
        self.email_downloader = EmailPDFDownloader(
            email_config['server'],
            email_config['user'],
            email_config['password'],
            email_config.get('port', 993)
        )
        self.pdf_processor = PDFProcessor()
        self.csv_exporter = CSVExporter(CSV_OUTPUT_FILE)
    
    def run_automation(self, mailbox: str = "INBOX", search_criteria: str = "ALL"):
        """Run the complete email-to-CSV automation"""
        logger.info("Starting Email PDF to CSV Automation...")
        
        if not self.email_downloader.connect():
            logger.error("Failed to connect to email server")
            return False
        
        try:
            pdf_emails = self.email_downloader.search_emails_with_pdfs(mailbox, search_criteria)
            
            if not pdf_emails:
                logger.info("No emails with PDF attachments found")
                return True
            
            total_processed = 0
            
            for email_id, email_message in pdf_emails:
                logger.info(f"Processing email: {email_message.get('Subject', 'No Subject')}")
                
                downloaded_files = self.email_downloader.download_pdf_attachments(
                    email_message, DOWNLOAD_FOLDER
                )
                
                for pdf_file in downloaded_files:
                    df = self.pdf_processor.extract_table_from_pdf(pdf_file)
                    
                    if df is not None and not df.empty:
                        self.csv_exporter.append_to_csv(df, os.path.basename(pdf_file))
                        total_processed += len(df)
                        logger.info(f"Successfully processed {pdf_file} - {len(df)} rows extracted")
                    else:
                        logger.warning(f"No data extracted from {pdf_file}")
            
            logger.info(f"Automation completed. Total rows processed: {total_processed}")
            return True
            
        except Exception as e:
            logger.error(f"Error during automation: {str(e)}")
            return False
        
        finally:
            self.email_downloader.disconnect()

def demo_with_local_pdf():
    """Demo function using the local example PDF"""
    logger.info("Running demo with local example PDF...")
    
    processor = PDFProcessor()
    exporter = CSVExporter(CSV_OUTPUT_FILE)
    
    pdf_path = "email_pdfs/simple_contacts.pdf"
    
    if not os.path.exists(pdf_path):
        logger.error(f"Example PDF not found: {pdf_path}")
        return False
    
    df = processor.extract_table_from_pdf(pdf_path)
    
    if df is not None and not df.empty:
        exporter.append_to_csv(df, os.path.basename(pdf_path))
        logger.info(f"Demo completed successfully - {len(df)} rows exported to CSV")
        
        print("\nExtracted Data:")
        print(df.to_string())
        
        print(f"\nCSV file created: {CSV_OUTPUT_FILE}")
        return True
    else:
        logger.error("No data extracted from example PDF")
        return False

def main():
    """Main function"""
    print("Email PDF to CSV Automation")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        demo_with_local_pdf()
        return
    
    email_config = {
        'server': os.getenv('EMAIL_SERVER', 'imap.gmail.com'),
        'user': os.getenv('EMAIL_USER', ''),
        'password': os.getenv('EMAIL_PASSWORD', ''),
        'port': int(os.getenv('EMAIL_PORT', '993'))
    }
    
    if not email_config['user'] or not email_config['password']:
        logger.error("Email credentials not provided. Set EMAIL_USER and EMAIL_PASSWORD environment variables.")
        logger.info("Or run 'python email_pdf_processor.py demo' to test with local PDF")
        return
    
    automation = EmailPDFAutomation(email_config)
    automation.run_automation()

if __name__ == "__main__":
    main()
