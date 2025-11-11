import requests
import json
import os

BASE_URL = "http://localhost:8000"

VALID_TOKEN = "UlWGx9EYLK6AtJCZ1LVRTMwK5PCQuisBl3%2BxgTVowyoBQ3gJtMg0fVpsMgmb9XCixgp2446wvuWH%2FdtKiTn4%2Baj7Q7NpSuhDzOQGfQfzhesvwJF1YqBSq3UQM9nGB5w8KnekyHcgTnIb26wlAlJk6w5gQE%2FSxGArNmBrFbSGNEg%3D"

INVALID_TOKEN = "Yrw%2FAQeno0NUzw3x%2Fvs%2FgPMf%2BBeyg5embicTLOvPnvMyYRCzhxKenYw4p9MwWJeMTtrcxz3CpEzmurMbl904dCYRoQeWczdVA1najVXHIK%2BGvuRNHYvgFpuiYmzFtoFueTY%2F9alHOn2MVQ5%2B%2BEDbTvBD82JCXY28x4PWREjNHdU%3D"

TEST_PAYLOAD = {
    "userName": "テスター／ローカル／SMBC (Tester)／1234567890ABCDEF",
    "threadId": "test-thread-auth",
    "conversation": [
        {
            "question": {"content": "テスト資料を作成してください"},
            "answer": {"content": "# テストスライド\n\nこれは認証テスト用の資料です。"}
        }
    ]
}

os.environ["COREAUTH_ROOT_URL"] = "http://127.0.0.1:10001"
os.environ["COREAUTH_APP_ID"] = "3af3e1d7-d62a-40de-a556-a0d7a08f7292"
os.environ["COREAUTH_APP_SECRET"] = "e5faad05face941736ca76e1094c928d032cba9a7a1486b06b8052c9dc038221"


def test_with_valid_token():
    print("\n" + "="*80)
    print("TEST 1: Valid Token (validFor='ppt')")
    print("="*80)
    
    cookies = {"MarketSessionToken": VALID_TOKEN}
    response = requests.post(
        f"{BASE_URL}/api/v2/generate",
        json=TEST_PAYLOAD,
        cookies=cookies
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 202:
        print("✅ PASSED: Request accepted with valid token")
        return response.json().get("taskId")
    else:
        print("❌ FAILED: Should return 202 with valid token")
        return None


def test_with_invalid_token():
    print("\n" + "="*80)
    print("TEST 2: Invalid Token (validFor='')")
    print("="*80)
    
    cookies = {"MarketSessionToken": INVALID_TOKEN}
    response = requests.post(
        f"{BASE_URL}/api/v2/generate",
        json=TEST_PAYLOAD,
        cookies=cookies
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 403:
        print("✅ PASSED: Correctly rejected token without 'ppt' in validFor")
    else:
        print("❌ FAILED: Should return 403 for invalid validFor")


def test_without_token():
    print("\n" + "="*80)
    print("TEST 3: No Token")
    print("="*80)
    
    response = requests.post(
        f"{BASE_URL}/api/v2/generate",
        json=TEST_PAYLOAD
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 401:
        print("✅ PASSED: Correctly rejected request without token")
    else:
        print("❌ FAILED: Should return 401 without token")


def test_status_endpoint(task_id):
    print("\n" + "="*80)
    print("TEST 4: Status Endpoint (Public, no auth required)")
    print("="*80)
    
    if not task_id:
        print("⏭️  SKIPPED: No task_id from previous test")
        return
    
    response = requests.get(f"{BASE_URL}/api/v2/status/{task_id}")
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print("✅ PASSED: Status endpoint accessible without auth")
    else:
        print("❌ FAILED: Status endpoint should be public")


def test_metadata_with_auth():
    print("\n" + "="*80)
    print("TEST 5: Metadata Endpoint with Auth")
    print("="*80)
    
    cookies = {"MarketSessionToken": VALID_TOKEN}
    params = {
        "userName": TEST_PAYLOAD["userName"],
        "threadId": TEST_PAYLOAD["threadId"]
    }
    
    response = requests.get(
        f"{BASE_URL}/api/v2/metadata",
        params=params,
        cookies=cookies
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        print("✅ PASSED: Metadata accessible with valid token")
    else:
        print("❌ FAILED: Should return 200 with valid token")


def test_metadata_without_auth():
    print("\n" + "="*80)
    print("TEST 6: Metadata Endpoint without Auth")
    print("="*80)
    
    params = {
        "userName": TEST_PAYLOAD["userName"],
        "threadId": TEST_PAYLOAD["threadId"]
    }
    
    response = requests.get(f"{BASE_URL}/api/v2/metadata", params=params)
    
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    
    if response.status_code == 401:
        print("✅ PASSED: Metadata correctly requires authentication")
    else:
        print("❌ FAILED: Should return 401 without token")


if __name__ == "__main__":
    print("="*80)
    print("PPT-Automate Authentication Tests")
    print("="*80)
    print(f"Base URL: {BASE_URL}")
    print(f"Valid Token (first 30 chars): {VALID_TOKEN[:30]}...")
    print(f"Invalid Token (first 30 chars): {INVALID_TOKEN[:30]}...")
    
    try:
        task_id = test_with_valid_token()
        test_with_invalid_token()
        test_without_token()
        test_status_endpoint(task_id)
        test_metadata_with_auth()
        test_metadata_without_auth()
        
        print("\n" + "="*80)
        print("All tests completed!")
        print("="*80)
        
    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server. Make sure PPT-Automate is running on port 8000")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

