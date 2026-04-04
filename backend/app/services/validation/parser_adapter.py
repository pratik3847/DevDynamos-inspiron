"""
Parser Adapter
Converts parser JSON output to validator-compatible format
"""
from typing import Dict, Any, List


class ParserAdapter:
    """Adapts parser output to validator input format"""
    
    @staticmethod
    def convert_to_validator_format(parser_output: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert parser JSON output to validator-compatible format
        
        Args:
            parser_output: JSON output from parser with segments and loops
        
        Returns:
            Dict with 'segments' list in validator format
        """
        validator_data = {
            "transaction_type": parser_output.get("transactionType", "834"),
            "segments": [],
            "loops": []
        }
        
        # Convert top-level segments
        if "segments" in parser_output:
            validator_data["segments"] = ParserAdapter._convert_segments(
                parser_output["segments"]
            )
        
        # Convert loops (flatten for easier validation)
        if "loops" in parser_output:
            loop_segments = ParserAdapter._extract_loop_segments(
                parser_output["loops"]
            )
            validator_data["segments"].extend(loop_segments)
            validator_data["loops"] = parser_output["loops"]
        
        return validator_data
    
    @staticmethod
    def _convert_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert segment list to validator format"""
        converted = []
        
        for segment in segments:
            converted_segment = {
                "id": segment.get("segmentId", ""),
                "name": segment.get("segmentName", ""),
                "raw": segment.get("rawText", "")
            }
            
            # Convert elements to field format (e.g., ISA01, ISA02, etc.)
            if "elements" in segment:
                for element in segment["elements"]:
                    position = element.get("position", "")
                    value = element.get("value", "")
                    segment_id = segment.get("segmentId", "")
                    
                    # Create field key like "ISA01", "GS02", etc.
                    if position:
                        field_key = f"{segment_id}{position}"
                        converted_segment[field_key] = value
            
            converted.append(converted_segment)
        
        return converted
    
    @staticmethod
    def _extract_loop_segments(loops: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Recursively extract all segments from loops"""
        all_segments = []
        
        for loop in loops:
            # Add segments from this loop
            if "segments" in loop:
                converted = ParserAdapter._convert_segments(loop["segments"])
                all_segments.extend(converted)
            
            # Recursively process nested loops
            if "loops" in loop and loop["loops"]:
                nested_segments = ParserAdapter._extract_loop_segments(loop["loops"])
                all_segments.extend(nested_segments)
        
        return all_segments
    
    @staticmethod
    def get_transaction_type(parser_output: Dict[str, Any]) -> str:
        """Extract transaction type from parser output"""
        trans_type = parser_output.get("transactionType", "")
        
        # Map to standard format
        if trans_type == "834":
            return "834"
        elif trans_type == "837":
            return "837P"
        elif trans_type == "835":
            return "835"
        
        return trans_type
    
    @staticmethod
    def extract_segment_value(
        segment: Dict[str, Any], 
        element_position: str
    ) -> str:
        """
        Extract element value from parser segment format
        
        Args:
            segment: Segment dict from parser
            element_position: Position like "01", "02", etc.
        
        Returns:
            Element value or empty string
        """
        if "elements" not in segment:
            return ""
        
        for element in segment["elements"]:
            if element.get("position") == element_position:
                return element.get("value", "")
        
        return ""
    
    @staticmethod
    def find_segments_by_id(
        parser_output: Dict[str, Any], 
        segment_id: str
    ) -> List[Dict[str, Any]]:
        """
        Find all segments with specific ID
        
        Args:
            parser_output: Parser JSON output
            segment_id: Segment ID to find (e.g., "NM1", "DMG")
        
        Returns:
            List of matching segments
        """
        matching = []
        
        # Search top-level segments
        if "segments" in parser_output:
            for segment in parser_output["segments"]:
                if segment.get("segmentId") == segment_id:
                    matching.append(segment)
        
        # Search loop segments
        if "loops" in parser_output:
            matching.extend(
                ParserAdapter._find_in_loops(parser_output["loops"], segment_id)
            )
        
        return matching
    
    @staticmethod
    def _find_in_loops(
        loops: List[Dict[str, Any]], 
        segment_id: str
    ) -> List[Dict[str, Any]]:
        """Recursively find segments in loops"""
        matching = []
        
        for loop in loops:
            if "segments" in loop:
                for segment in loop["segments"]:
                    if segment.get("segmentId") == segment_id:
                        matching.append(segment)
            
            if "loops" in loop and loop["loops"]:
                matching.extend(
                    ParserAdapter._find_in_loops(loop["loops"], segment_id)
                )
        
        return matching


class ValidationHelper:
    """Helper methods for validation with parser format"""
    
    @staticmethod
    def get_element_value(
        parser_output: Dict[str, Any],
        segment_id: str,
        element_position: str,
        occurrence: int = 0
    ) -> str:
        """
        Get element value from parser output
        
        Args:
            parser_output: Parser JSON output
            segment_id: Segment ID (e.g., "NM1")
            element_position: Element position (e.g., "09")
            occurrence: Which occurrence to get (0 = first)
        
        Returns:
            Element value or empty string
        """
        segments = ParserAdapter.find_segments_by_id(parser_output, segment_id)
        
        if occurrence < len(segments):
            return ParserAdapter.extract_segment_value(
                segments[occurrence], 
                element_position
            )
        
        return ""
    
    @staticmethod
    def get_all_element_values(
        parser_output: Dict[str, Any],
        segment_id: str,
        element_position: str
    ) -> List[str]:
        """
        Get all element values for a segment type
        
        Args:
            parser_output: Parser JSON output
            segment_id: Segment ID
            element_position: Element position
        
        Returns:
            List of values
        """
        segments = ParserAdapter.find_segments_by_id(parser_output, segment_id)
        values = []
        
        for segment in segments:
            value = ParserAdapter.extract_segment_value(segment, element_position)
            if value:
                values.append(value)
        
        return values
    
    @staticmethod
    def count_segments(parser_output: Dict[str, Any], segment_id: str) -> int:
        """Count occurrences of a segment"""
        return len(ParserAdapter.find_segments_by_id(parser_output, segment_id))
