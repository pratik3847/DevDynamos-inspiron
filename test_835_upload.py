"""
Test 835 file upload through the complete pipeline
"""
import requests
import json

# Test credentials (adjust if needed)
LOGIN_URL = "http://localhost:8000/auth/login"
UPLOAD_URL = "http://localhost:8000/files/upload"

# 1. Login to get token
print("=== Step 1: Login ===")
login_data = {
    "email": "test@example.com",
    "password": "password123"
}

try:
    response = requests.post(LOGIN_URL, json=login_data)
    if response.status_code == 200:
        token = response.json().get("access_token")
        print(f"✓ Login successful, token: {token[:20]}...")
    else:
        print(f"✗ Login failed: {response.status_code} {response.text}")
        exit(1)
except Exception as e:
    print(f"✗ Login error: {e}")
    exit(1)

# 2. Upload 835 file
print("\n=== Step 2: Upload 835 File ===")
headers = {
    "Authorization": f"Bearer {token}"
}

with open("test_835_comprehensive.txt", "rb") as f:
    files = {"file": ("test_835.txt", f, "text/plain")}
    
    try:
        response = requests.post(UPLOAD_URL, headers=headers, files=files)
        if response.status_code == 200:
            result = response.json()
            print(f"✓ Upload successful!")
            print(f"  Session ID: {result['data']['sessionId']}")
            print(f"  Status: {result['data']['status']}")
            session_id = result['data']['sessionId']
        else:
            print(f"✗ Upload failed: {response.status_code}")
            print(response.text)
            exit(1)
    except Exception as e:
        print(f"✗ Upload error: {e}")
        exit(1)

# 3. Fetch session to verify 835 parsing
print(f"\n=== Step 3: Fetch Session {session_id} ===")
SESSION_URL = f"http://localhost:8000/files/session/{session_id}"

try:
    response = requests.get(SESSION_URL, headers=headers)
    if response.status_code == 200:
        session = response.json()
        print(f"✓ Session fetched successfully!")
        
        # Check if 835 parsed data exists
        if "parsed_835" in session:
            print(f"\n✓ 835-specific parsing SUCCESSFUL!")
            parsed_835 = session["parsed_835"]
            
            # Display payment info
            payment_header = parsed_835.get("payment_header", {})
            print(f"\n  Payment Details:")
            print(f"    Total: ${payment_header.get('total_payment_amount', 0)}")
            print(f"    Method: {payment_header.get('payment_method', 'N/A')}")
            
            # Display entities
            entities = parsed_835.get("entities", {})
            payer = entities.get("PR", {})
            provider = entities.get("PE", {})
            print(f"\n  Payer: {payer.get('name', 'N/A')}")
            print(f"  Provider: {provider.get('name', 'N/A')}")
            
            # Display claims summary
            claims = parsed_835.get("claims", [])
            print(f"\n  Claims: {len(claims)} total")
            for i, claim in enumerate(claims[:3], 1):
                print(f"    {i}. {claim.get('claim_submitter_identifier')}: {claim.get('patient_name')} - ${claim.get('claim_payment_amount')}")
                if claim.get('adjustments'):
                    print(f"       Adjustments: {len(claim['adjustments'])}")
                    for adj in claim['adjustments'][:2]:
                        print(f"         - {adj.get('group_code')}-{adj.get('reason_code')}: ${adj.get('adjustment_amount')}")
            
            if len(claims) > 3:
                print(f"    ... and {len(claims) - 3} more claims")
        else:
            print(f"\n✗ No parsed_835 data found in session")
            print(f"  Available keys: {list(session.keys())}")
    else:
        print(f"✗ Session fetch failed: {response.status_code}")
        print(response.text)
except Exception as e:
    print(f"✗ Session fetch error: {e}")
    exit(1)

print("\n=== Test Complete! ===")
print(f"\nNext steps:")
print(f"1. Open frontend at http://localhost:5177")
print(f"2. Navigate to Upload section")
print(f"3. Select the uploaded session")
print(f"4. Go to Dashboard → 835 Dashboard")
print(f"5. Verify claims are displayed correctly")
