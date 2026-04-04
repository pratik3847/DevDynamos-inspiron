import json
import uuid

import requests


def main() -> None:
    base = "http://127.0.0.1:8000"

    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    password = "Passw0rd!"
    name = "Test"

    r = requests.post(f"{base}/auth/signup", json={"name": name, "email": email, "password": password})
    print("signup", r.status_code)
    if not r.ok:
        print(r.text)
        r.raise_for_status()

    token = r.json().get("accessToken")
    if not token:
        raise RuntimeError("No accessToken returned from /auth/signup")

    headers = {"Authorization": f"Bearer {token}"}

    edi = (
        "ISA*00*          *00*          *ZZ*SENDERID      *ZZ*RECEIVERID    *240404*1200*^*00501*000000905*0*T*:~\n"
        "GS*HC*SENDER*RECEIVER*20240404*1200*1*X*005010X222A1~\n"
        "ST*837*0001~\n"
        "BHT*0019*00*0123*20240404*1200*CH~\n"
        "NM1*85*2*TEST*****XX*0000000000~\n"
        "SE*6*0001~\n"
        "GE*1*1~\n"
        "IEA*1*000000905~\n"
    )

    files = {"file": ("test.edi", edi.encode("utf-8"), "text/plain")}
    r = requests.post(f"{base}/files/upload", headers=headers, files=files)
    print("upload", r.status_code)
    if not r.ok:
        print(r.text)
        r.raise_for_status()

    session_id = r.json()["data"]["sessionId"]

    r = requests.get(f"{base}/files/session/{session_id}", headers=headers)
    print("get session", r.status_code)
    if not r.ok:
        print(r.text)
        r.raise_for_status()

    sess = r.json()
    fixes = sess.get("fixes") or []
    print("fixes", len(fixes))

    if not fixes:
        print("No fixes generated; cannot test apply")
        return

    fix = fixes[0]
    print(
        "first fix",
        {k: fix.get(k) for k in ["id", "segmentId", "elementId", "suggested", "original", "description", "status"]},
    )

    if not (fix.get("segmentId") and fix.get("elementId") and fix.get("suggested")):
        print("Fix missing required targeting fields; cannot apply")
        return

    payload = {
        "sessionId": session_id,
        "segmentId": fix["segmentId"],
        "elementId": fix["elementId"],
        "newValue": fix["suggested"],
        "fixId": fix.get("id"),
    }
    r = requests.post(
        f"{base}/fix/apply",
        headers={**headers, "Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    print("apply", r.status_code)
    if not r.ok:
        print(r.text)
        try:
            print("detail", r.json())
        except Exception:
            pass
        r.raise_for_status()

    r = requests.get(f"{base}/files/session/{session_id}", headers=headers)
    r.raise_for_status()
    updated = r.json()
    accepted = [x for x in (updated.get("fixes") or []) if x.get("status") == "accepted"]
    print("accepted fixes", len(accepted))
    print("correctedEdi present", bool(updated.get("correctedEdi")))
    print("fixReports", len(updated.get("fixReports") or []))


if __name__ == "__main__":
    main()
