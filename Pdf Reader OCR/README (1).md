# Email PDF to CSV Automation

This Python automation downloads PDF attachments from emails, processes them using OCR to extract table data, and exports the results to CSV format. Perfect for processing business documents like contact lists, invoices, reports, and other tabular data in PDF format.

## Installation

### Python Dependencies

Install the required Python dependencies:

```bash
pip install pandas pytesseract pdf2image pillow
```

Or install from requirements file:

```bash
pip install -r requirements.txt
```

### System Dependencies (for OCR support)

For processing scanned/image-based PDFs, you also need to install tesseract-ocr and poppler-utils:

**Ubuntu/Debian:**
```bash
sudo apt update && sudo apt install -y tesseract-ocr poppler-utils
```

**macOS:**
```bash
brew install tesseract poppler
```

**Windows:**
- Download and install tesseract from: https://github.com/UB-Mannheim/tesseract/wiki
- Download and install poppler from: https://blog.alivate.com.au/poppler-windows/

## Usage

### Email Automation

1. **Set up email credentials** (choose one method):

   **Option A: Environment Variables**
   ```bash
   export EMAIL_SERVER="imap.gmail.com"
   export EMAIL_USER="your_email@gmail.com"
   export EMAIL_PASSWORD="your_app_password"
   export EMAIL_PORT="993"
   ```

   **Option B: Modify email_config_example.py**
   ```python
   EMAIL_CONFIG = {
       'server': 'imap.gmail.com',
       'user': 'your_email@gmail.com',
       'password': 'your_app_password',
       'port': 993
   }
   ```

2. **Run the email automation**:
   ```bash
   python email_pdf_processor.py
   ```

3. **Demo with local PDF**:
   ```bash
   python email_pdf_processor.py demo
   ```

### Email Provider Setup

**Gmail:**
- Enable 2-factor authentication
- Generate an App Password: https://support.google.com/accounts/answer/185833
- Use the App Password instead of your regular password

**Outlook/Hotmail:**
- Server: `outlook.office365.com`
- Port: `993`
- Use your regular email password

**Yahoo:**
- Enable 2-factor authentication
- Generate an App Password
- Server: `imap.mail.yahoo.com`

### Testing

Test the complete automation system:

```bash
python test_email_automation.py
```

This will test:
- PDF processing with OCR
- CSV export functionality
- Complete workflow with example data

## Features

- **Email Integration**: Downloads PDF attachments from any IMAP-compatible email provider
- **OCR Processing**: Extracts table data from scanned/image-based PDFs using `pytesseract`
- **CSV Export**: Outputs clean, structured data in CSV format
- **Metadata Tracking**: Includes source file name and processing timestamp
- **Error Handling**: Robust error handling with detailed logging
- **Multiple Email Providers**: Works with Gmail, Outlook, Yahoo, and other IMAP servers

## File Structure

```
├── email_pdf_processor.py      # Main email automation script
├── test_email_automation.py    # Test suite for all functionality
├── email_config_example.py     # Example email configuration
├── requirements.txt            # Python dependencies
├── README.md                  # This documentation
├── email_pdfs/                # Example PDFs folder
│   ├── simple_contacts.pdf    # Example contact directory
│   ├── simple_invoices.pdf    # Example invoice report
│   ├── business_contacts.pdf  # Detailed contact list
│   └── invoice_summary.pdf    # Invoice summary report
├── downloaded_pdfs/           # Downloaded PDFs (created automatically)
└── extracted_pdf_data.csv     # Output CSV file (created automatically)
```

## How It Works

1. **Email Connection**: Connects to your email server using IMAP protocol
2. **PDF Discovery**: Searches for emails with PDF attachments
3. **PDF Download**: Downloads PDF attachments to local folder
4. **OCR Processing**: 
   - Converts PDF pages to images using `pdf2image`
   - Extracts text from images using `pytesseract` OCR
   - Parses the OCR text to identify table structure
5. **CSV Export**: Exports structured data to CSV with metadata

## CSV Output Format

The output CSV includes:
- All columns found in the PDF table
- `Source_File`: Name of the original PDF file
- `Date_Processed`: Timestamp when the PDF was processed
- Missing values filled with "N/A"

Example output for contact data:
```csv
Record_ID,Name_Client,Type_Department,Contact_Amount,Status_Location,Date_Info,Source_File,Date_Processed
C001,John,Smith,Sales,555-0123,john@company.com,simple_contacts.pdf,2024-07-12 15:30:00
C002,Sarah,Johnson,Marketing,555-0124,sarah@company.com,simple_contacts.pdf,2024-07-12 15:30:00
```

Example output for invoice data:
```csv
Record_ID,Name_Client,Type_Department,Contact_Amount,Status_Location,Date_Info,Source_File,Date_Processed
INV001,Tech,Corp,2500,Paid,2024-06-15,simple_invoices.pdf,2024-07-12 15:30:00
INV002,Design,LLC,4200,Pending,2024-07-20,simple_invoices.pdf,2024-07-12 15:30:00
```

## Advanced Configuration

### Search Criteria

You can customize email search criteria:

```python
# Search recent emails only
automation.run_automation(search_criteria='(SINCE "01-Jan-2024")')

# Search emails from specific sender
automation.run_automation(search_criteria='(FROM "lab@company.com")')

# Search emails with specific subject
automation.run_automation(search_criteria='(SUBJECT "test results")')
```

### Custom Processing

Extend the `PDFProcessor` class to customize OCR settings or table parsing logic.

## Troubleshooting

### Email Connection Issues
- **Gmail**: Make sure you're using an App Password, not your regular password
- **2FA Required**: Most email providers require 2-factor authentication for IMAP access
- **Firewall**: Ensure port 993 (IMAP SSL) is not blocked

### OCR Issues
- **Poor Quality PDFs**: Increase DPI in `convert_from_path(pdf_path, dpi=300)`
- **Complex Tables**: Adjust OCR config in `pytesseract.image_to_string(image, config='--psm 6')`
- **Missing Text**: Ensure tesseract-ocr is properly installed

### CSV Export Issues
- **File Permissions**: Ensure write permissions for the output directory
- **Large Files**: For very large datasets, consider processing in chunks

## Security Notes

- Never commit email credentials to version control
- Use environment variables or secure config files for credentials
- Consider using OAuth2 for production applications
- App Passwords are more secure than regular passwords for email automation

## Legacy PDF Watcher

The original folder-watching functionality is still available in `pdf_watcher.py` for local PDF processing with Excel output.
