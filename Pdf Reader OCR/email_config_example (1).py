#!/usr/bin/env python3
"""
Example configuration for email automation
Copy this file and update with your email settings
"""

EMAIL_CONFIG = {
    'gmail': {
        'server': 'imap.gmail.com',
        'port': 993,
        'user': 'your_email@gmail.com',
        'password': 'your_app_password'  # Use App Password for Gmail
    },
    
    'outlook': {
        'server': 'outlook.office365.com',
        'port': 993,
        'user': 'your_email@outlook.com',
        'password': 'your_password'
    },
    
    'yahoo': {
        'server': 'imap.mail.yahoo.com',
        'port': 993,
        'user': 'your_email@yahoo.com',
        'password': 'your_app_password'  # Use App Password for Yahoo
    }
}

SEARCH_CRITERIA_EXAMPLES = {
    'all_emails': 'ALL',
    'unread_emails': 'UNSEEN',
    'emails_with_attachments': 'ALL',  # Will be filtered for PDFs
    'recent_emails': '(SINCE "01-Jan-2024")',
    'from_specific_sender': '(FROM "sender@example.com")',
    'subject_contains': '(SUBJECT "test results")'
}
