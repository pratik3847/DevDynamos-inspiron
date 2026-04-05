"""
835 Parser API Routes
Healthcare Payment Remittance Processing Endpoints
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from typing import Dict, List, Any, Optional
import uuid
import asyncio
import logging
from datetime import datetime

from ...services.parser_835.parser_835 import Parser835
from ...services.rag.rag_client import RAGClient
from ...utils.auth import get_current_user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/parser", tags=["835 Parser"])

# In-memory storage for demo (in production, use database)
file_storage = {}

@router.post("/upload-835", summary="Upload 835 Remittance File")
async def upload_835_file(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Upload and store 835 EDI remittance file for processing
    
    - **file**: 835 EDI file (text format)
    - Returns: file_id for subsequent processing
    """
    try:
        # Validate file type
        if not file.filename.endswith(('.txt', '.edi', '.835')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Please upload .txt, .edi, or .835 files"
            )
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Basic 835 validation
        if not content_str.strip().startswith('ISA'):
            raise HTTPException(
                status_code=400,
                detail="Invalid 835 file format. File must start with ISA segment"
            )
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Store file data
        file_storage[file_id] = {
            'filename': file.filename,
            'content': content_str,
            'uploaded_at': datetime.utcnow().isoformat(),
            'uploaded_by': current_user.get('username', 'unknown'),
            'status': 'uploaded',
            'parsed_data': None
        }
        
        logger.info(f"835 file uploaded: {file.filename} (ID: {file_id})")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "size_bytes": len(content),
            "status": "uploaded",
            "message": "File uploaded successfully. Use /parse/{file_id} to process."
        }
        
    except Exception as e:
        logger.error(f"Error uploading 835 file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/parse/{file_id}", summary="Parse 835 File")
async def parse_835_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """
    Parse uploaded 835 file into structured JSON
    
    - **file_id**: ID from upload-835 endpoint
    - Returns: Complete parsed 835 structure with claims and adjustments
    """
    try:
        # Check if file exists
        if file_id not in file_storage:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_data = file_storage[file_id]
        
        # Check if already parsed
        if file_data.get('parsed_data'):
            return {
                "file_id": file_id,
                "status": "already_parsed",
                "parsed_data": file_data['parsed_data']
            }
        
        # Initialize parser
        parser = Parser835()
        
        # Parse the file
        logger.info(f"Starting 835 parse for file: {file_id}")
        parsed_data = parser.parse_file(file_data['content'])
        
        # Store parsed data
        file_data['parsed_data'] = parsed_data
        file_data['status'] = 'parsed'
        file_data['parsed_at'] = datetime.utcnow().isoformat()
        
        logger.info(f"835 file parsed successfully: {file_id}")
        
        return {
            "file_id": file_id,
            "status": "parsed",
            "parsed_data": parsed_data
        }
        
    except Exception as e:
        logger.error(f"Error parsing 835 file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

@router.get("/payment-summary/{file_id}", summary="Get Payment Summary")
async def get_payment_summary(file_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get aggregated payment summary for 835 file
    
    - **file_id**: Parsed 835 file ID
    - Returns: Summary statistics and totals
    """
    try:
        if file_id not in file_storage:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_data = file_storage[file_id]
        parsed_data = file_data.get('parsed_data')
        
        if not parsed_data:
            raise HTTPException(status_code=400, detail="File not parsed. Use /parse/{file_id} first")
        
        # Extract summary information
        summary = parsed_data.get('summary', {})
        payment_header = parsed_data.get('payment_header', {})
        entities = parsed_data.get('entities', {})
        
        return {
            "file_id": file_id,
            "filename": file_data['filename'],
            "summary": summary,
            "payment_info": {
                "payment_amount": payment_header.get('total_payment_amount', 0),
                "payment_method": payment_header.get('payment_method', 'Unknown'),
                "payment_date": payment_header.get('check_issue_date', 'Unknown')
            },
            "payer_info": entities.get('PR', {}),  # PR = Payer
            "payee_info": entities.get('PE', {})   # PE = Payee
        }
        
    except Exception as e:
        logger.error(f"Error getting payment summary {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/claim-details/{file_id}", summary="Get Detailed Claims")
async def get_claim_details(file_id: str, current_user: dict = Depends(get_current_user)):
    """
    Get detailed claim-by-claim breakdown
    
    - **file_id**: Parsed 835 file ID
    - Returns: All claims with adjustments and patient details
    """
    try:
        if file_id not in file_storage:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_data = file_storage[file_id]
        parsed_data = file_data.get('parsed_data')
        
        if not parsed_data:
            raise HTTPException(status_code=400, detail="File not parsed. Use /parse/{file_id} first")
        
        claims = parsed_data.get('claims', [])
        
        # Add status descriptions for each claim
        for claim in claims:
            status_code = claim.get('claim_status_code', '')
            claim['status_description'] = _get_status_description(status_code)
            
            # Add adjustment summaries
            adjustments = claim.get('adjustments', [])
            claim['adjustment_summary'] = {
                'total_adjustments': len(adjustments),
                'total_adjustment_amount': sum(adj.get('adjustment_amount', 0) for adj in adjustments),
                'unique_reason_codes': list(set(adj.get('reason_code', '') for adj in adjustments))
            }
        
        return {
            "file_id": file_id,
            "total_claims": len(claims),
            "claims": claims
        }
        
    except Exception as e:
        logger.error(f"Error getting claim details {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/explain-adjustment", summary="Explain CARC/RARC Codes")
async def explain_adjustment_codes(
    request_data: Dict[str, Any],
    current_user: dict = Depends(get_current_user)
):
    """
    Get plain-language explanations for adjustment codes using RAG
    
    - **reason_codes**: List of CARC/RARC codes to explain
    - **context**: Optional claim context for better explanations
    - Returns: Explanations with confidence scores and sources
    """
    try:
        reason_codes = request_data.get('reason_codes', [])
        context = request_data.get('context', '')
        
        if not reason_codes:
            raise HTTPException(status_code=400, detail="reason_codes list is required")
        
        # Initialize parser (for RAG access)
        parser = Parser835()
        
        # Get explanations from RAG system
        explanations = parser.explain_adjustment_codes(reason_codes)
        
        return {
            "request_codes": reason_codes,
            "context": context,
            "explanations": explanations,
            "rag_status": parser._get_rag_status()
        }
        
    except Exception as e:
        logger.error(f"Error explaining adjustment codes: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-patterns/{file_id}", summary="Analyze Payment Patterns")
async def analyze_payment_patterns(file_id: str, current_user: dict = Depends(get_current_user)):
    """
    Identify and explain common adjustment patterns in the remittance
    
    - **file_id**: Parsed 835 file ID
    - Returns: Pattern analysis with RAG-powered explanations
    """
    try:
        if file_id not in file_storage:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_data = file_storage[file_id]
        parsed_data = file_data.get('parsed_data')
        
        if not parsed_data:
            raise HTTPException(status_code=400, detail="File not parsed. Use /parse/{file_id} first")
        
        # Analyze patterns
        claims = parsed_data.get('claims', [])
        summary = parsed_data.get('summary', {})
        
        # Get top adjustment reasons
        top_adjustments = summary.get('top_adjustment_reasons', {})
        
        # Initialize RAG client
        rag_client = RAGClient()
        
        # Get explanations for top adjustment reasons
        patterns = []
        for reason_code, count in list(top_adjustments.items())[:5]:  # Top 5
            try:
                query = f"Explain CARC-{reason_code} common causes and resolution steps"
                rag_results = rag_client.query(
                    question=query,
                    doc_type="code_list",
                    top_k=2,
                    min_score=0.3
                )
                
                explanation = "No specific explanation found"
                confidence = 0
                
                if rag_results:
                    explanation = rag_results[0].get('text', explanation)
                    confidence = rag_results[0].get('score', 0)
                
                patterns.append({
                    'reason_code': reason_code,
                    'frequency': count,
                    'percentage': round((count / len(claims)) * 100, 1),
                    'explanation': explanation,
                    'confidence': confidence
                })
                
            except Exception as e:
                patterns.append({
                    'reason_code': reason_code,
                    'frequency': count,
                    'percentage': round((count / len(claims)) * 100, 1),
                    'explanation': f"Error getting explanation: {str(e)}",
                    'confidence': 0
                })
        
        return {
            "file_id": file_id,
            "total_claims": len(claims),
            "patterns_analyzed": len(patterns),
            "common_patterns": patterns
        }
        
    except Exception as e:
        logger.error(f"Error analyzing patterns {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ask-question/{file_id}", summary="Ask Questions About Remittance")
async def ask_question_about_file(
    file_id: str,
    request_data: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """
    Ask contextual questions about the remittance file using RAG
    
    - **file_id**: Parsed 835 file ID  
    - **question**: Natural language question about the remittance
    - Returns: AI-powered answer with sources
    """
    try:
        question = request_data.get('question', '')
        
        if not question:
            raise HTTPException(status_code=400, detail="question is required")
        
        if file_id not in file_storage:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_data = file_storage[file_id]
        parsed_data = file_data.get('parsed_data')
        
        if not parsed_data:
            raise HTTPException(status_code=400, detail="File not parsed. Use /parse/{file_id} first")
        
        # Get file context
        summary = parsed_data.get('summary', {})
        payment_amount = summary.get('payment_amount', 0)
        claim_count = summary.get('total_claims', 0)
        top_adjustments = list(summary.get('top_adjustment_reasons', {}).keys())[:3]
        
        # Enhance question with context
        contextual_question = f"""
        Question about 835 remittance file:
        - Payment amount: ${payment_amount:,.2f}
        - Number of claims: {claim_count}
        - Top adjustment codes: {', '.join(top_adjustments)}
        
        User question: {question}
        """
        
        # Query RAG system
        rag_client = RAGClient()
        rag_results = rag_client.query(
            question=contextual_question,
            top_k=5,
            min_score=0.2
        )
        
        # Format response
        if rag_results:
            main_answer = rag_results[0].get('text', 'No specific answer found')
            sources = [
                {
                    'document': result.get('source_doc', 'Unknown'),
                    'confidence': result.get('score', 0),
                    'excerpt': result.get('text', '')[:200] + '...'
                }
                for result in rag_results[:3]
            ]
        else:
            main_answer = "I couldn't find specific information to answer your question."
            sources = []
        
        return {
            "file_id": file_id,
            "question": question,
            "answer": main_answer,
            "file_context": {
                "payment_amount": payment_amount,
                "claim_count": claim_count,
                "top_adjustments": top_adjustments
            },
            "sources": sources
        }
        
    except Exception as e:
        logger.error(f"Error answering question for {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/files", summary="List Uploaded Files")
async def list_uploaded_files(current_user: dict = Depends(get_current_user)):
    """
    Get list of all uploaded 835 files for current user
    
    Returns: List of file metadata
    """
    try:
        user_files = []
        username = current_user.get('username', 'unknown')
        
        for file_id, file_data in file_storage.items():
            if file_data.get('uploaded_by') == username:
                user_files.append({
                    'file_id': file_id,
                    'filename': file_data.get('filename'),
                    'uploaded_at': file_data.get('uploaded_at'),
                    'status': file_data.get('status'),
                    'has_parsed_data': file_data.get('parsed_data') is not None
                })
        
        return {
            "total_files": len(user_files),
            "files": sorted(user_files, key=lambda x: x['uploaded_at'], reverse=True)
        }
        
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
def _get_status_description(status_code: str) -> str:
    """Convert claim status code to description"""
    status_map = {
        '1': 'Processed as Primary',
        '2': 'Processed as Secondary', 
        '3': 'Processed as Tertiary',
        '4': 'Denied',
        '19': 'Processed as Primary, Forwarded to Additional Payer(s)',
        '20': 'Processed as Secondary, Forwarded to Additional Payer(s)',
        '21': 'Processed as Tertiary, Forwarded to Additional Payer(s)',
        '22': 'Reversal of Previous Payment',
        '23': 'Not Our Claim, Forwarded to Additional Payer(s)'
    }
    
    return status_map.get(status_code, f'Unknown Status Code: {status_code}')