"""
Structure-aware document chunking for legal documents.
Preserves logical boundaries (sections, clauses) rather than arbitrary splits.
"""

from typing import List, Dict, Any
import re


def chunk_document(
    ocr_result: Dict[str, Any],
    document_type: str,
    max_chunk_size: int = 1500,
    overlap: int = 200
) -> List[Dict[str, Any]]:
    """
    Chunk a document using structure-aware chunking.
    
    For legal documents like Section 32:
    - Chunks by section headers
    - Preserves clause boundaries
    - Includes metadata for each chunk
    """
    
    pages = ocr_result.get("pages", [])
    
    # Choose chunking strategy based on document type
    if document_type in ["Section 32 Vendor Statement (VIC)", "Contract for Sale (NSW)"]:
        return chunk_legal_document(pages, max_chunk_size, overlap)
    elif document_type in ["Strata Report / OC Certificate", "Strata AGM Minutes"]:
        return chunk_strata_document(pages, max_chunk_size, overlap)
    else:
        return chunk_generic_document(pages, max_chunk_size, overlap)


def chunk_legal_document(
    pages: List[Dict[str, Any]],
    max_chunk_size: int,
    overlap: int
) -> List[Dict[str, Any]]:
    """
    Chunk legal documents by section headers.
    
    Looks for patterns like:
    - "1. Title" or "1.1 Easements"
    - "PART A" or "SCHEDULE 1"
    - "Special Condition 1"
    """
    
    chunks = []
    current_section = "Document Start"
    current_text = ""
    current_page = 1
    
    section_patterns = [
        r'^(\d+\.?\d*)\s+([A-Z][^\.]+)',  # "1. Title" or "1.1 Easements"
        r'^(PART\s+[A-Z])',                 # "PART A"
        r'^(SCHEDULE\s+\d+)',               # "SCHEDULE 1"
        r'^(Special Condition\s+\d+)',      # "Special Condition 1"
        r'^(ANNEXURE\s+[A-Z])',             # "ANNEXURE A"
    ]
    
    for page in pages:
        page_num = page.get("page_number", 1)
        text = page.get("text", "")
        
        # Split into lines and look for section headers
        lines = text.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this line is a section header
            is_header = False
            new_section = None
            
            for pattern in section_patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    is_header = True
                    new_section = line[:100]  # Limit section name length
                    break
            
            if is_header and current_text:
                # Save current chunk
                chunks.append({
                    "text": current_text.strip(),
                    "section": current_section,
                    "page_start": current_page,
                    "page_end": page_num,
                    "chunk_type": "legal_section"
                })
                
                # Start new chunk
                current_section = new_section
                current_text = line + "\n"
                current_page = page_num
            else:
                current_text += line + "\n"
                
                # Check if we need to split due to size
                if len(current_text) > max_chunk_size:
                    # Split at paragraph boundary
                    split_point = current_text.rfind("\n\n", 0, max_chunk_size)
                    if split_point == -1:
                        split_point = current_text.rfind("\n", 0, max_chunk_size)
                    if split_point == -1:
                        split_point = max_chunk_size
                    
                    chunks.append({
                        "text": current_text[:split_point].strip(),
                        "section": current_section,
                        "page_start": current_page,
                        "page_end": page_num,
                        "chunk_type": "legal_section_part"
                    })
                    
                    # Keep overlap
                    current_text = current_text[split_point - overlap:]
    
    # Add final chunk
    if current_text.strip():
        chunks.append({
            "text": current_text.strip(),
            "section": current_section,
            "page_start": current_page,
            "page_end": pages[-1].get("page_number", 1) if pages else 1,
            "chunk_type": "legal_section"
        })
    
    return chunks


def chunk_strata_document(
    pages: List[Dict[str, Any]],
    max_chunk_size: int,
    overlap: int
) -> List[Dict[str, Any]]:
    """
    Chunk strata documents looking for meeting minutes sections.
    """
    
    chunks = []
    current_section = "Strata Document"
    current_text = ""
    current_page = 1
    
    # Patterns for strata document sections
    section_patterns = [
        r'^(ANNUAL GENERAL MEETING)',
        r'^(EXTRAORDINARY GENERAL MEETING)',
        r'^(COMMITTEE MEETING)',
        r'^(AGENDA)',
        r'^(MINUTES)',
        r'^(FINANCIAL STATEMENTS?)',
        r'^(SINKING FUND|CAPITAL WORKS FUND)',
        r'^(INSURANCE)',
        r'^(BY-?LAWS?|RULES)',
        r'^(ITEM\s+\d+)',
        r'^(MOTION\s+\d+)',
        r'^(RESOLUTION\s+\d+)',
    ]
    
    for page in pages:
        page_num = page.get("page_number", 1)
        text = page.get("text", "")
        lines = text.split("\n")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            is_header = False
            new_section = None
            
            for pattern in section_patterns:
                if re.match(pattern, line, re.IGNORECASE):
                    is_header = True
                    new_section = line[:100]
                    break
            
            if is_header and current_text:
                chunks.append({
                    "text": current_text.strip(),
                    "section": current_section,
                    "page_start": current_page,
                    "page_end": page_num,
                    "chunk_type": "strata_section"
                })
                
                current_section = new_section
                current_text = line + "\n"
                current_page = page_num
            else:
                current_text += line + "\n"
    
    if current_text.strip():
        chunks.append({
            "text": current_text.strip(),
            "section": current_section,
            "page_start": current_page,
            "page_end": pages[-1].get("page_number", 1) if pages else 1,
            "chunk_type": "strata_section"
        })
    
    return chunks


def chunk_generic_document(
    pages: List[Dict[str, Any]],
    max_chunk_size: int,
    overlap: int
) -> List[Dict[str, Any]]:
    """
    Generic chunking for documents without clear structure.
    Chunks by page with overlap.
    """
    
    chunks = []
    
    for page in pages:
        page_num = page.get("page_number", 1)
        text = page.get("text", "").strip()
        
        if not text:
            continue
        
        # If page fits in one chunk
        if len(text) <= max_chunk_size:
            chunks.append({
                "text": text,
                "section": f"Page {page_num}",
                "page_start": page_num,
                "page_end": page_num,
                "chunk_type": "page"
            })
        else:
            # Split page into multiple chunks
            start = 0
            part = 1
            while start < len(text):
                end = min(start + max_chunk_size, len(text))
                
                # Try to end at paragraph boundary
                if end < len(text):
                    boundary = text.rfind("\n\n", start, end)
                    if boundary > start:
                        end = boundary
                
                chunks.append({
                    "text": text[start:end].strip(),
                    "section": f"Page {page_num} (Part {part})",
                    "page_start": page_num,
                    "page_end": page_num,
                    "chunk_type": "page_part"
                })
                
                start = end - overlap
                part += 1
    
    return chunks







