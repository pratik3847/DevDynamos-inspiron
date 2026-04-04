from datetime import datetime

def create_session(userId: str, fileName: str, edi_text: str, parsed, errors, fixes) -> dict:
    """
    Returns a structured dictionary representing an EDI session,
    prepared for MongoDB insertion.
    """
    now = datetime.utcnow()
    
    return {
        "userId": userId,
        "fileName": fileName,
        "status": "Requires Attention" if errors else "Clean",
        "rawEdi": edi_text,
        "correctedEdi": None,
        "parsedJson": parsed,
        "modifiedJson": parsed,
        # validationErrors is the *current* issue set (will change after applying fixes)
        "validationErrors": errors,
        # originalValidationErrors is the *uploaded-file* issue set (never changes)
        "originalValidationErrors": errors,
        "fixes": fixes,
        "chatHistory": [],
        "changesLog": [],
        "createdAt": now,
        "updatedAt": now,
    }
