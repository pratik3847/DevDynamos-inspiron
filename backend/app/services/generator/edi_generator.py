"""
EDI Generator Logic
Handles transformation of structural JSON formatting back to raw EDI formats.
"""

def generate_edi(parsed: dict) -> str:
    """
    Converts structured parsed JSON into a valid EDI string format.
    Safely ignores mutability, isolating extraction loops tightly.
    """
    if not isinstance(parsed, dict) or "segments" not in parsed:
        return ""

    edi = ""
    segments = parsed.get("segments", [])
    
    for seg in segments:
        # Secure extraction preventing KeyErrors
        segment_id = seg.get("segmentId", "")
        elements = [str(el.get("value", "")) for el in seg.get("elements", [])]
        
        # Concat logic
        if elements:
            line = segment_id + "*" + "*".join(elements) + "~"
        else:
            line = segment_id + "~"
            
        # Standardize presentation by appending cleanly 
        edi += line + "\n"

    return edi.strip()
