#!/usr/bin/env python3
"""
Complete workflow example using Smart PDF Toolkit
Demonstrates a real-world document processing pipeline
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from smart_pdf_toolkit.core.pdf_processor import PDFProcessor
from smart_pdf_toolkit.core.batch_processor import BatchProcessor
from smart_pdf_toolkit.ai.services import AIServices

async def document_processing_workflow():
    """
    Demonstrate a complete document processing workflow:
    1. Batch process multiple PDFs
    2. Extract and analyze content
    3. Generate summaries and insights
    4. Create consolidated report
    """
    
    print("Smart PDF Toolkit - Complete Workflow Example")
    print("=" * 50)
    
    # Initialize processors
    pdf_processor = PDFProcessor()
    batch_processor = BatchProcessor()
    ai_services = AIServices()
    
    # Step 1: Prepare input files
    input_dir = Path("input_documents")
    output_dir = Path("workflow_output")
    output_dir.mkdir(exist_ok=True)
    
    if not input_dir.exists():
        print(f"Creating sample input directory: {input_dir}")
        input_dir.mkdir(exist_ok=True)
        print("Please add PDF files to the input_documents/ directory and run again")
        return
    
    pdf_files = list(input_dir.glob("*.pdf"))
    if not pdf_files:
        print("No PDF files found in input_documents/ directory")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process")
    
    # Step 2: Batch extract text from all PDFs
    print("\nStep 1: Extracting text from all PDFs...")
    extraction_results = []
    
    for pdf_file in pdf_files:
        try:
            result = await pdf_processor.extract_text(pdf_file)
            extraction_results.append({
                "file": pdf_file.name,
                "text": result.text,
                "pages": result.page_count,
                "success": True
            })
            print(f"✓ Extracted text from {pdf_file.name}")
        except Exception as e:
            extraction_results.append({
                "file": pdf_file.name,
                "error": str(e),
                "success": False
            })
            print(f"✗ Failed to extract text from {pdf_file.name}: {e}")
    
    # Step 3: AI-powered analysis
    print("\nStep 2: Analyzing documents with AI...")
    analysis_results = []
    
    for result in extraction_results:
        if not result["success"]:
            continue
            
        try:
            # Generate summary
            summary = await ai_services.summarize_text(result["text"])
            
            # Extract key topics
            topics = await ai_services.extract_topics(result["text"])
            
            # Classify document type
            doc_type = await ai_services.classify_document(result["text"])
            
            analysis_results.append({
                "file": result["file"],
                "summary": summary,
                "topics": topics,
                "document_type": doc_type,
                "word_count": len(result["text"].split())
            })
            
            print(f"✓ Analyzed {result['file']}")
            
        except Exception as e:
            print(f"✗ Failed to analyze {result['file']}: {e}")
    
    # Step 4: Generate consolidated report
    print("\nStep 3: Generating consolidated report...")
    
    report = {
        "workflow_summary": {
            "total_files": len(pdf_files),
            "successfully_processed": len([r for r in extraction_results if r["success"]]),
            "total_pages": sum(r.get("pages", 0) for r in extraction_results if r["success"]),
            "total_words": sum(r.get("word_count", 0) for r in analysis_results)
        },
        "document_analysis": analysis_results,
        "processing_errors": [r for r in extraction_results if not r["success"]]
    }
    
    # Save detailed report
    report_file = output_dir / "processing_report.json"
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Generate human-readable summary
    summary_file = output_dir / "executive_summary.txt"
    with open(summary_file, "w", encoding="utf-8") as f:
        f.write("DOCUMENT PROCESSING EXECUTIVE SUMMARY\n")
        f.write("=" * 40 + "\n\n")
        
        f.write(f"Processed {report['workflow_summary']['successfully_processed']} ")
        f.write(f"out of {report['workflow_summary']['total_files']} documents\n")
        f.write(f"Total pages processed: {report['workflow_summary']['total_pages']}\n")
        f.write(f"Total words analyzed: {report['workflow_summary']['total_words']}\n\n")
        
        f.write("DOCUMENT SUMMARIES:\n")
        f.write("-" * 20 + "\n")
        
        for analysis in analysis_results:
            f.write(f"\nFile: {analysis['file']}\n")
            f.write(f"Type: {analysis['document_type']}\n")
            f.write(f"Word Count: {analysis['word_count']}\n")
            f.write(f"Key Topics: {', '.join(analysis['topics'])}\n")
            f.write(f"Summary: {analysis['summary']}\n")
            f.write("-" * 40 + "\n")
    
    # Step 5: Create merged document with all extracted text
    print("\nStep 4: Creating merged text document...")
    
    merged_file = output_dir / "all_extracted_text.txt"
    with open(merged_file, "w", encoding="utf-8") as f:
        f.write("MERGED DOCUMENT TEXT\n")
        f.write("=" * 30 + "\n\n")
        
        for result in extraction_results:
            if result["success"]:
                f.write(f"=== {result['file']} ===\n")
                f.write(result["text"])
                f.write("\n\n" + "=" * 50 + "\n\n")
    
    print(f"\nWorkflow completed successfully!")
    print(f"Results saved to: {output_dir}")
    print(f"- Detailed report: {report_file}")
    print(f"- Executive summary: {summary_file}")
    print(f"- Merged text: {merged_file}")
    
    return report

def main():
    """Run the workflow example"""
    try:
        report = asyncio.run(document_processing_workflow())
        
        # Print summary to console
        print("\n" + "=" * 50)
        print("WORKFLOW SUMMARY")
        print("=" * 50)
        print(f"Files processed: {report['workflow_summary']['successfully_processed']}")
        print(f"Total pages: {report['workflow_summary']['total_pages']}")
        print(f"Total words: {report['workflow_summary']['total_words']}")
        
        if report['processing_errors']:
            print(f"Errors encountered: {len(report['processing_errors'])}")
        
    except KeyboardInterrupt:
        print("\nWorkflow interrupted by user")
    except Exception as e:
        print(f"Workflow failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()