#!/usr/bin/env python3
"""
Test script for the email PDF automation system
"""

import os
import sys
from email_pdf_processor import EmailPDFAutomation, PDFProcessor, CSVExporter, demo_with_local_pdf
import pandas as pd

def test_pdf_processing():
    """Test PDF processing functionality"""
    print("Testing PDF Processing...")
    print("-" * 40)
    
    processor = PDFProcessor()
    pdf_path = "email_pdfs/sample_test_report.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ Example PDF not found: {pdf_path}")
        return False
    
    df = processor.extract_table_from_pdf(pdf_path)
    
    if df is not None and not df.empty:
        print(f"✅ Successfully extracted {len(df)} rows and {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
        print("\nExtracted data:")
        print(df.to_string())
        return True
    else:
        print("❌ No data extracted")
        return False

def test_csv_export():
    """Test CSV export functionality"""
    print("\nTesting CSV Export...")
    print("-" * 40)
    
    if os.path.exists("test_output.csv"):
        os.remove("test_output.csv")
    
    exporter = CSVExporter("test_output.csv")
    
    sample_data = {
        'Sample ID': ['S001', 'S002'],
        'Material Type': ['Rubber A', 'Rubber B'],
        'Tensile Strength (psi)': ['2850', '3100'],
        'Elongation (%)': ['450', '380']
    }
    
    df = pd.DataFrame(sample_data)
    exporter.append_to_csv(df, "test_sample.pdf")
    
    if os.path.exists("test_output.csv"):
        result_df = pd.read_csv("test_output.csv")
        print(f"✅ CSV export successful - {len(result_df)} rows written")
        print("\nCSV content:")
        print(result_df.to_string())
        return True
    else:
        print("❌ CSV export failed")
        return False

def test_complete_workflow():
    """Test the complete workflow with demo function"""
    print("\nTesting Complete Workflow...")
    print("-" * 40)
    
    if os.path.exists("extracted_pdf_data.csv"):
        os.remove("extracted_pdf_data.csv")
    
    success = demo_with_local_pdf()
    
    if success and os.path.exists("extracted_pdf_data.csv"):
        result_df = pd.read_csv("extracted_pdf_data.csv")
        print(f"✅ Complete workflow successful - {len(result_df)} rows in final CSV")
        return True
    else:
        print("❌ Complete workflow failed")
        return False

def main():
    """Run all tests"""
    print("Email PDF Automation Test Suite")
    print("=" * 50)
    
    tests = [
        ("PDF Processing", test_pdf_processing),
        ("CSV Export", test_csv_export),
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with error: {str(e)}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("Test Results Summary:")
    print("=" * 50)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
    
    all_passed = all(result for _, result in results)
    print(f"\nOverall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

if __name__ == "__main__":
    main()
