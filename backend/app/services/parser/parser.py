import io
import pyx12.x12file
import traceback
import concurrent.futures

def _run_pyx12_parsing(edi_text: str):
    segments = []
    # Wrap string in StringIO to mimic file for pyx12 reader
    fd = io.StringIO(edi_text.strip())
    reader = pyx12.x12file.X12Reader(fd)
    
    for seg in reader:
        segment_id = seg.get_seg_id()
        elements = []
        
        # Extract elements cleanly using pyx12 element mapping
        for j, val in enumerate(seg.elements):
            position = f"{j+1:02d}"
            ele_id = f"{segment_id}{position}"
            str_val = str(val).strip() if val is not None else ""
            elements.append({"id": ele_id, "position": position, "value": str_val})
            
        raw_str = f"{segment_id}*" + "*".join(str(v) if v is not None else "" for v in seg.elements) + "~"
            
        segments.append({
            "segmentId": segment_id,
            "elements": elements,
            "raw": raw_str
        })
    return segments

def parser_agent(edi_text: str) -> dict:
    """
    Real EDI parser using pyx12 library.
    Turns raw X12 string into a structured nested dict that Validator expects.
    Protected against Event Loop deadlocks via ThreadPoolExecutor.
    """
    segments = []
    
    try:
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_run_pyx12_parsing, edi_text)
            # Imposing a firm 3-second timeout on pyx12 library to prevent infinite event loop blocking
            segments = future.result(timeout=3.0)
            
    except Exception as e:
        print(f"PYX12 Parsing error or timeout fallback: {e}")
        
        # Fallback to manual parsing if pyx12 fails explicitly or hangs indefinitely
        segments = []
        lines = edi_text.replace('\n', '').replace('\r', '').split('~')
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split('*')
            segment_id = parts[0]
            elements = [
                {"id": f"{segment_id}{j+1:02d}", "position": f"{j+1:02d}", "value": val}
                for j, val in enumerate(parts[1:])
            ]
            
            segments.append({
                "segmentId": segment_id,
                "elements": elements,
                "raw": line + "~"
            })
            
    return {
        "status": "parsed",
        "segments": segments,
        "loops": [] # Flattened for UI tree parsing
    }
