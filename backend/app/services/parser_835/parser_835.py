"""
835 Parser Service - Healthcare Payment Remittance Processor
Integrates with existing RAG system for CARC/RARC explanations
"""

from typing import Dict, List, Any, Optional, Union
import re
from decimal import Decimal
from datetime import datetime
from ..rag.rag_client import RAGClient

class Parser835:
    """
    Comprehensive 835 EDI Remittance Advice Parser
    Connects to existing RAG system for payment explanation context
    """
    
    def __init__(self):
        """Initialize with RAG integration"""
        self.rag_client = RAGClient()
        self.segment_delimiter = '~'
        self.element_delimiter = '*'
        self.sub_element_delimiter = ':'
        
    def parse_file(self, content: str) -> Dict[str, Any]:
        """
        Parse complete 835 remittance file
        
        Args:
            content: Raw 835 EDI content
            
        Returns:
            Complete parsed structure with payment details
        """
        try:
            # Clean and validate content
            content = self._clean_content(content)
            
            # Extract control segments
            segments = self._split_segments(content)
            
            # Parse envelope (ISA/GS/ST)
            envelope = self._parse_envelope(segments)
            
            # Parse payment header (BPR)
            payment_header = self._parse_payment_header(segments)
            
            # Parse payer/payee information (N1 loops)
            entities = self._parse_entities(segments)
            
            # Parse claims and adjustments (CLP/CAS loops)
            claims = self._parse_claims(segments)
            
            # Calculate summaries
            summary = self._calculate_summary(payment_header, claims)
            
            return {
                "file_metadata": {
                    "parsed_at": datetime.utcnow().isoformat(),
                    "total_segments": len(segments),
                    "parser_version": "1.0.0"
                },
                "envelope": envelope,
                "payment_header": payment_header,
                "entities": entities,
                "claims": claims,
                "summary": summary,
                "rag_integration": {
                    "enabled": True,
                    "embedding_count": self._get_rag_status()
                }
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "parse_failed",
                "rag_integration": {"enabled": False}
            }
    
    def _clean_content(self, content: str) -> str:
        """Clean EDI content and detect delimiters"""
        # Remove BOM and normalize line endings
        content = content.strip().replace('\r\n', '\n').replace('\r', '\n')
        
        # Auto-detect delimiters from ISA segment
        if content.startswith('ISA'):
            self.element_delimiter = content[3]  # Character after 'ISA'
            
            # Find the segment delimiter (usually ~) at the end of the ISA segment
            isa_end = content.find('~', 3)  # Start searching after ISA*
            if isa_end > 0:
                self.segment_delimiter = content[isa_end]
                # Sub-element delimiter is typically at position isa_end-1
                if isa_end > 1:
                    self.sub_element_delimiter = content[isa_end-1]
                else:
                    self.sub_element_delimiter = ':'  # Default
            else:
                # Fallback to defaults
                self.segment_delimiter = '~'
                self.sub_element_delimiter = ':'
        
        return content
    
    def _split_segments(self, content: str) -> List[str]:
        """Split content into segments"""
        segments = [seg.strip() for seg in content.split(self.segment_delimiter) if seg.strip()]
        return segments
    
    def _parse_envelope(self, segments: List[str]) -> Dict[str, Any]:
        """Parse ISA/GS/ST envelope segments"""
        envelope = {}
        
        for segment in segments:
            elements = segment.split(self.element_delimiter)
            
            if elements[0] == 'ISA':
                envelope['interchange'] = {
                    'sender_id': elements[6],
                    'receiver_id': elements[8], 
                    'date': elements[9],
                    'time': elements[10],
                    'control_number': elements[13]
                }
            elif elements[0] == 'GS':
                envelope['functional_group'] = {
                    'transaction_type': elements[1],  # Should be 'RA' for 835
                    'sender': elements[2],
                    'receiver': elements[3],
                    'date': elements[4],
                    'time': elements[5],
                    'control_number': elements[6]
                }
            elif elements[0] == 'ST':
                envelope['transaction_set'] = {
                    'transaction_type': elements[1],  # Should be '835' 
                    'control_number': elements[2]
                }
        
        return envelope
    
    def _parse_payment_header(self, segments: List[str]) -> Dict[str, Any]:
        """Parse BPR (Financial Information) segment"""
        for segment in segments:
            elements = segment.split(self.element_delimiter)
            
            if elements[0] == 'BPR':
                return {
                    'transaction_handling_code': elements[1],  # I=information only, C=payment
                    'total_payment_amount': float(elements[2]) if elements[2] else 0.0,
                    'credit_debit_flag': elements[3],  # C=credit, D=debit
                    'payment_method': elements[4],  # CHK, ACH, etc.
                    'payment_format': elements[5] if len(elements) > 5 else None,
                    'sender_bank_id': elements[6] if len(elements) > 6 else None,
                    'sender_bank_account': elements[7] if len(elements) > 7 else None,
                    'payer_identifier': elements[10] if len(elements) > 10 else None,
                    'check_issue_date': elements[16] if len(elements) > 16 else None
                }
        
        return {}
    
    def _parse_entities(self, segments: List[str]) -> Dict[str, Any]:
        """Parse N1 loops for payer and payee information"""
        entities = {}
        current_entity = None
        
        for i, segment in enumerate(segments):
            elements = segment.split(self.element_delimiter)
            
            if elements[0] == 'N1':
                entity_type = elements[1]
                entity_name = elements[2] if len(elements) > 2 else ''
                
                current_entity = {
                    'entity_type': entity_type,
                    'name': entity_name,
                    'identification_code_qualifier': elements[3] if len(elements) > 3 else None,
                    'identification_code': elements[4] if len(elements) > 4 else None
                }
                entities[entity_type] = current_entity
                
            elif elements[0] == 'N3' and current_entity:
                current_entity['address_line_1'] = elements[1] if len(elements) > 1 else ''
                current_entity['address_line_2'] = elements[2] if len(elements) > 2 else ''
                
            elif elements[0] == 'N4' and current_entity:
                current_entity['city'] = elements[1] if len(elements) > 1 else ''
                current_entity['state'] = elements[2] if len(elements) > 2 else ''
                current_entity['zip_code'] = elements[3] if len(elements) > 3 else ''
                
            elif elements[0] == 'REF' and current_entity:
                ref_qualifier = elements[1] if len(elements) > 1 else ''
                ref_value = elements[2] if len(elements) > 2 else ''
                
                if 'references' not in current_entity:
                    current_entity['references'] = {}
                current_entity['references'][ref_qualifier] = ref_value
        
        return entities
    
    def _parse_claims(self, segments: List[str]) -> List[Dict[str, Any]]:
        """Parse CLP (Claim Payment Information) and associated CAS segments"""
        claims = []
        current_claim = None
        
        for i, segment in enumerate(segments):
            elements = segment.split(self.element_delimiter)
            
            if elements[0] == 'CLP':
                # Save previous claim if exists
                if current_claim:
                    claims.append(current_claim)
                
                # Start new claim
                current_claim = {
                    'claim_submitter_identifier': elements[1] if len(elements) > 1 else '',
                    'claim_status_code': elements[2] if len(elements) > 2 else '',
                    'total_claim_charge_amount': float(elements[3]) if len(elements) > 3 and elements[3] else 0.0,
                    'claim_payment_amount': float(elements[4]) if len(elements) > 4 and elements[4] else 0.0,
                    'patient_responsibility_amount': float(elements[5]) if len(elements) > 5 and elements[5] else 0.0,
                    'claim_filing_indicator': elements[6] if len(elements) > 6 else '',
                    'payer_claim_control_number': elements[7] if len(elements) > 7 else '',
                    'facility_type_code': elements[8] if len(elements) > 8 else '',
                    'adjustments': [],
                    'service_lines': []
                }
                
            elif elements[0] == 'CAS' and current_claim:
                # Claim Adjustment Segment
                adjustment_group_code = elements[1] if len(elements) > 1 else ''
                
                # Parse adjustment reason codes and amounts (up to 6 pairs)
                adjustments = []
                for j in range(2, len(elements), 3):
                    if j < len(elements) and elements[j]:
                        reason_code = elements[j]
                        adjustment_amount = float(elements[j+1]) if j+1 < len(elements) and elements[j+1] else 0.0
                        quantity = float(elements[j+2]) if j+2 < len(elements) and elements[j+2] else 0.0
                        
                        adjustments.append({
                            'reason_code': reason_code,
                            'adjustment_amount': adjustment_amount,
                            'quantity': quantity,
                            'group_code': adjustment_group_code
                        })
                
                current_claim['adjustments'].extend(adjustments)
                
            elif elements[0] == 'NM1' and current_claim:
                # Patient name information
                if elements[1] == 'QC':  # Patient
                    current_claim['patient'] = {
                        'entity_type': elements[1],
                        'entity_type_qualifier': elements[2] if len(elements) > 2 else '',
                        'last_name': elements[3] if len(elements) > 3 else '',
                        'first_name': elements[4] if len(elements) > 4 else '',
                        'middle_name': elements[5] if len(elements) > 5 else '',
                        'identification_code_qualifier': elements[8] if len(elements) > 8 else '',
                        'identification_code': elements[9] if len(elements) > 9 else ''
                    }
                    
            elif elements[0] == 'DTM' and current_claim:
                # Date/Time Reference
                date_qualifier = elements[1] if len(elements) > 1 else ''
                date_value = elements[2] if len(elements) > 2 else ''
                
                if 'dates' not in current_claim:
                    current_claim['dates'] = {}
                current_claim['dates'][date_qualifier] = date_value
        
        # Add last claim
        if current_claim:
            claims.append(current_claim)
        
        return claims
    
    def _calculate_summary(self, payment_header: Dict, claims: List[Dict]) -> Dict[str, Any]:
        """Calculate payment summary statistics"""
        total_claims = len(claims)
        total_billed = sum(claim.get('total_claim_charge_amount', 0) for claim in claims)
        total_paid = sum(claim.get('claim_payment_amount', 0) for claim in claims)
        total_patient_responsibility = sum(claim.get('patient_responsibility_amount', 0) for claim in claims)
        
        # Count claims by status
        status_counts = {}
        for claim in claims:
            status = claim.get('claim_status_code', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Count adjustment reasons
        adjustment_counts = {}
        for claim in claims:
            for adj in claim.get('adjustments', []):
                reason = adj.get('reason_code', 'unknown')
                adjustment_counts[reason] = adjustment_counts.get(reason, 0) + 1
        
        return {
            'payment_amount': payment_header.get('total_payment_amount', 0),
            'total_claims': total_claims,
            'total_billed_amount': total_billed,
            'total_paid_amount': total_paid,
            'total_patient_responsibility': total_patient_responsibility,
            'claim_status_breakdown': status_counts,
            'top_adjustment_reasons': dict(sorted(adjustment_counts.items(), 
                                                key=lambda x: x[1], reverse=True)[:10])
        }
    
    def _get_rag_status(self) -> int:
        """Get RAG system status"""
        try:
            info = self.rag_client.get_collection_info()
            return info.get('vectors_count', 0)
        except:
            return 0
    
    def explain_adjustment_codes(self, reason_codes: List[str]) -> Dict[str, str]:
        """
        Get explanations for CARC/RARC codes from RAG system
        
        Args:
            reason_codes: List of adjustment reason codes
            
        Returns:
            Dictionary mapping codes to explanations
        """
        explanations = {}
        
        for code in reason_codes:
            try:
                # Query RAG system for code explanation
                query = f"What does CARC-{code} mean? Explain adjustment reason code {code}"
                rag_results = self.rag_client.query(
                    question=query,
                    doc_type="code_list",
                    top_k=3,
                    min_score=0.3
                )
                
                if rag_results:
                    # Use the best match
                    explanation = rag_results[0].get('text', 'No explanation found')
                    explanations[code] = {
                        'explanation': explanation,
                        'confidence': rag_results[0].get('score', 0),
                        'source': rag_results[0].get('source_doc', 'Unknown')
                    }
                else:
                    explanations[code] = {
                        'explanation': f'No explanation found for code {code}',
                        'confidence': 0,
                        'source': 'RAG System'
                    }
                    
            except Exception as e:
                explanations[code] = {
                    'explanation': f'Error retrieving explanation: {str(e)}',
                    'confidence': 0,
                    'source': 'Error'
                }
        
        return explanations