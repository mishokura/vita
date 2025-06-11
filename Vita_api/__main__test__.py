import requests
from pprint import pprint

BASE_URL = "http://127.0.0.1:8000"
TEST_USER = "testuser"
TEST_PASSWORD = "testpass"
ADMIN_USER = "adminuser"
ADMIN_PASSWORD = "adminpass"

def print_test_header(title):
    print(f"\n{'='*50}")
    print(f"Testing: {title}")
    print(f"{'='*50}")

def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}

def test_user_registration():
    print_test_header("User Registration")
    
    # Register test user
    response = requests.post(
        f"{BASE_URL}/register",
        params={"username": TEST_USER, "password": TEST_PASSWORD}
    )
    print("Regular user registration:")
    pprint(response.json())
    
    # Register admin user
    response = requests.post(
        f"{BASE_URL}/register",
        params={"username": ADMIN_USER, "password": ADMIN_PASSWORD, "is_admin": True}
    )
    print("\nAdmin user registration:")
    pprint(response.json())

def test_authentication():
    print_test_header("Authentication")
    
    # Test successful login
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": TEST_USER, "password": TEST_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print("Successful login:")
    pprint(response.json())
    global TEST_TOKEN
    TEST_TOKEN = response.json()["access_token"]
    
    # Test admin login
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": ADMIN_USER, "password": ADMIN_PASSWORD},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print("\nAdmin login:")
    pprint(response.json())
    global ADMIN_TOKEN
    ADMIN_TOKEN = response.json()["access_token"]
    
    # Test failed login
    response = requests.post(
        f"{BASE_URL}/token",
        data={"username": "wronguser", "password": "wrongpass"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    print("\nFailed login:")
    print(f"Status Code: {response.status_code}")
    pprint(response.json())

def test_admin_endpoints():
    print_test_header("Admin Endpoints")
    
    # Add career path
    career_data = {"name": "Software Engineering"}
    response = requests.post(
        f"{BASE_URL}/admin/careers",
        json=career_data,
        headers=get_auth_header(ADMIN_TOKEN)
    )
    print("Add career path (admin):")
    pprint(response.json())
    
    # Add question
    question_data = {
        "text": "Do you enjoy solving complex problems?",
        "associations": {
            "Software Engineering": 90,
            "Law": 30,
            "Medicine": 60
        }
    }
    response = requests.post(
        f"{BASE_URL}/admin/questions",
        json=question_data,
        headers=get_auth_header(ADMIN_TOKEN)
    )
    print("\nAdd question (admin):")
    pprint(response.json())
    
    # Try as non-admin (should fail)
    response = requests.post(
        f"{BASE_URL}/admin/careers",
        json=career_data,
        headers=get_auth_header(TEST_TOKEN)
    )
    print("\nAdd career path (non-admin - should fail):")
    print(f"Status Code: {response.status_code}")
    pprint(response.json())

def test_question_endpoints():
    print_test_header("Question Endpoints")
    
    # Get all questions
    response = requests.get(f"{BASE_URL}/questions")
    print("Get all questions:")
    pprint(response.json())
    global QUESTIONS
    QUESTIONS = response.json()

def test_answer_submission():
    print_test_header("Answer Submission")
    
    if not QUESTIONS:
        print("No questions available to answer")
        return
    
    # Prepare answers
    answers = [
        {"question_id": QUESTIONS[0]["id"], "answer": 80}
    ]
    
    # Submit partial answers
    response = requests.post(
        f"{BASE_URL}/submit",
        json=answers
    )
    print("Partial submission (last=False):")
    pprint(response.json())
    
    # Submit final answers
    response = requests.post(
        f"{BASE_URL}/submit",
        json=answers,
        params={"last": True}
    )
    print("\nFinal submission (last=True):")
    pprint(response.json())

def run_all_tests():
    test_user_registration()
    test_authentication()
    test_admin_endpoints()
    test_question_endpoints()
    test_answer_submission()

if __name__ == "__main__":
    TEST_TOKEN = None
    ADMIN_TOKEN = None
    QUESTIONS = None
    
    print("Starting Career Helper API Tests...")
    run_all_tests()
    print("\nAll tests completed!")