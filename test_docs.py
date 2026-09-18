import urllib.request
import json
import os

BASE = "http://127.0.0.1:8000"
p_list = json.loads(urllib.request.urlopen(f"{BASE}/api/patients").read())
p_id = p_list[0]["patient_id"]
docs = json.loads(urllib.request.urlopen(f"{BASE}/api/patients/{p_id}/documents").read())

print(f"Checking {len(docs)} documents:")
for d in docs:
    doc_id = d["document_id"]
    filename = d["original_filename"]
    url = f"{BASE}/api/documents/{doc_id}/file"
    print(f"\nDocument: {filename} (ID: {doc_id})")
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req) as resp:
            content = resp.read()
            print(f"  Status: {resp.status}")
            print(f"  Content-Type: {resp.headers.get('Content-Type')}")
            print(f"  Content-Disposition: {resp.headers.get('Content-Disposition')}")
            print(f"  Bytes: {len(content)}")
    except urllib.error.HTTPError as e:
        print(f"  HTTPError {e.code}: {e.read().decode('utf-8')}")
    except Exception as e:
        print(f"  Error: {e}")
