import requests
import sys
import json
from datetime import datetime

class CommissionTrackerAPITester:
    def __init__(self, base_url="https://driver-tracker-27.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.admin_token = None
        self.user_token = None
        self.helper_token = None
        self.test_user_id = None
        self.test_helper_id = None
        self.assigned_driver_token = None
        self.assigned_driver_id = None
        self.tests_run = 0
        self.tests_passed = 0
        
        # Expected truck rates
        self.truck_rates = {
            "BKO": 3.50,
            "PYW": 3.50,
            "NYC": 3.50,
            "GKY": 7.50,
            "GSD": 7.50,
            "AUA": 10.00
        }
        
        # Day assignments for drivers
        self.day_assignments = {
            "Davi": "Monday",
            "Ivaney": "Tuesday", 
            "Claudio": "Wednesday",
            "Valdiney": "Thursday"
        }
        
        # Expected checklist categories
        self.expected_categories = [
            "Motor", "Freio", "Direção", "Elétrico", 
            "Pneus", "Placas", "Obrigatório", "Habitáculo"
        ]

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_admin_login(self):
        """Test admin login with default credentials"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"username": "admin", "password": "admin123"}
        )
        if success and 'token' in response:
            self.admin_token = response['token']
            print(f"   Admin role: {response.get('user', {}).get('role')}")
            return True
        return False

    def test_user_registration(self):
        """Test user registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_user = {
            "username": f"testdriver_{timestamp}",
            "password": "TestPass123!",
            "name": f"Test Driver {timestamp}",
            "role": "driver"
        }
        
        success, response = self.run_test(
            "User Registration",
            "POST",
            "auth/register",
            200,
            data=test_user
        )
        if success and 'token' in response:
            self.user_token = response['token']
            self.test_user_id = response['user']['id']
            print(f"   Created user: {response['user']['name']} (ID: {self.test_user_id})")
            return True
        return False

    def test_user_login(self):
        """Test user login with registered credentials"""
        timestamp = datetime.now().strftime('%H%M%S')
        success, response = self.run_test(
            "User Login",
            "POST",
            "auth/login",
            200,
            data={"username": f"testdriver_{timestamp}", "password": "TestPass123!"}
        )
        return success

    def test_user_dashboard(self):
        """Test user dashboard endpoint"""
        if not self.user_token:
            print("❌ Skipping user dashboard test - no user token")
            return False
            
        success, response = self.run_test(
            "User Dashboard",
            "GET",
            "user/dashboard",
            200,
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        if success:
            # Verify dashboard structure
            required_fields = ['user', 'deliveries', 'total_deliveries', 'total_commission']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field in dashboard: {field}")
                    return False
            
            # Verify truck types in deliveries
            deliveries = response.get('deliveries', {})
            for truck in self.truck_rates.keys():
                if truck not in deliveries:
                    print(f"❌ Missing truck type in deliveries: {truck}")
                    return False
            
            print(f"   Total deliveries: {response.get('total_deliveries', 0)}")
            print(f"   Total commission: R$ {response.get('total_commission', 0)}")
            return True
        return False

    def test_admin_get_users(self):
        """Test admin get all users endpoint"""
        if not self.admin_token:
            print("❌ Skipping admin users test - no admin token")
            return False
            
        success, response = self.run_test(
            "Admin Get Users",
            "GET",
            "admin/users",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success:
            print(f"   Found {len(response)} users")
            if len(response) > 0:
                user = response[0]
                required_fields = ['user', 'total_deliveries', 'total_commission']
                for field in required_fields:
                    if field not in user:
                        print(f"❌ Missing field in user summary: {field}")
                        return False
            return True
        return False

    def test_admin_update_delivery(self):
        """Test admin update delivery endpoint"""
        if not self.admin_token or not self.test_user_id:
            print("❌ Skipping delivery update test - missing admin token or user ID")
            return False
            
        # Test updating delivery for BKO truck
        success, response = self.run_test(
            "Admin Update Delivery",
            "POST",
            "admin/delivery",
            200,
            data={
                "user_id": self.test_user_id,
                "truck_type": "BKO",
                "delivery_count": 5
            },
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success:
            print("   Successfully updated delivery count")
            return True
        return False

    def test_admin_get_user_deliveries(self):
        """Test admin get user deliveries endpoint"""
        if not self.admin_token or not self.test_user_id:
            print("❌ Skipping user deliveries test - missing admin token or user ID")
            return False
            
        success, response = self.run_test(
            "Admin Get User Deliveries",
            "GET",
            f"admin/user/{self.test_user_id}/deliveries",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success:
            print(f"   Found {len(response)} delivery records")
            # Verify all truck types are present
            truck_types_found = [d['truck_type'] for d in response]
            for truck in self.truck_rates.keys():
                if truck not in truck_types_found:
                    print(f"❌ Missing delivery record for truck: {truck}")
                    return False
            return True
        return False

    def test_commission_calculation(self):
        """Test commission calculation accuracy"""
        if not self.user_token:
            print("❌ Skipping commission calculation test - no user token")
            return False
            
        # Get current dashboard
        success, dashboard = self.run_test(
            "Commission Calculation Check",
            "GET",
            "user/dashboard",
            200,
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        if success:
            deliveries = dashboard.get('deliveries', {})
            calculated_commission = 0
            calculated_deliveries = 0
            
            for truck, count in deliveries.items():
                if truck in self.truck_rates:
                    calculated_commission += count * self.truck_rates[truck]
                    calculated_deliveries += count
            
            api_commission = dashboard.get('total_commission', 0)
            api_deliveries = dashboard.get('total_deliveries', 0)
            
            commission_match = abs(calculated_commission - api_commission) < 0.01
            deliveries_match = calculated_deliveries == api_deliveries
            
            if commission_match and deliveries_match:
                print(f"✅ Commission calculation correct: R$ {api_commission}")
                print(f"✅ Delivery count correct: {api_deliveries}")
                return True
            else:
                print(f"❌ Commission mismatch - Expected: {calculated_commission}, Got: {api_commission}")
                print(f"❌ Delivery mismatch - Expected: {calculated_deliveries}, Got: {api_deliveries}")
                return False
        return False

    def test_unauthorized_access(self):
        """Test unauthorized access to protected endpoints"""
        print("\n🔍 Testing Unauthorized Access...")
        
        # Test user dashboard without token
        success, _ = self.run_test(
            "User Dashboard (No Token)",
            "GET",
            "user/dashboard",
            401
        )
        
        # Test admin endpoints without token
        success2, _ = self.run_test(
            "Admin Users (No Token)",
            "GET",
            "admin/users",
            401
        )
        
        # Test admin endpoint with user token
        if self.user_token:
            success3, _ = self.run_test(
                "Admin Users (User Token)",
                "GET",
                "admin/users",
                403,
                headers={"Authorization": f"Bearer {self.user_token}"}
            )
        else:
            success3 = True  # Skip if no user token
            
        return success and success2 and success3

    def test_invalid_data(self):
        """Test API with invalid data"""
        print("\n🔍 Testing Invalid Data Handling...")
        
        # Test registration with invalid role
        success1, _ = self.run_test(
            "Registration (Invalid Role)",
            "POST",
            "auth/register",
            400,
            data={
                "username": "testinvalid",
                "password": "TestPass123!",
                "name": "Test Invalid",
                "role": "invalid_role"
            }
        )
        
        # Test login with wrong credentials
        success2, _ = self.run_test(
            "Login (Wrong Credentials)",
            "POST",
            "auth/login",
            401,
            data={"username": "nonexistent", "password": "wrongpass"}
        )
        
        # Test delivery update with invalid truck type
        if self.admin_token and self.test_user_id:
            success3, _ = self.run_test(
                "Update Delivery (Invalid Truck)",
                "POST",
                "admin/delivery",
                400,
                data={
                    "user_id": self.test_user_id,
                    "truck_type": "INVALID",
                    "delivery_count": 5
                },
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
        else:
            success3 = True
            
        return success1 and success2 and success3

    def test_assigned_driver_registration(self):
        """Test driver registration with assigned day names"""
        timestamp = datetime.now().strftime('%H%M%S')
        
        # Test driver with assigned day (Davi)
        success, response = self.run_test(
            "Assigned Driver Registration (Davi)",
            "POST",
            "auth/register",
            200,
            data={
                "username": f"davi_{timestamp}",
                "password": "TestPass123!",
                "name": "Davi",
                "role": "driver"
            }
        )
        
        if success and 'user' in response:
            user = response['user']
            if user.get('assigned_day') == 'Monday':
                print(f"✅ Davi correctly assigned to Monday")
                self.assigned_driver_token = response['token']
                self.assigned_driver_id = user['id']
                return True
            else:
                print(f"❌ Davi assigned to {user.get('assigned_day')}, expected Monday")
                return False
        return False

    def test_unassigned_driver_registration(self):
        """Test driver registration with non-assigned name"""
        timestamp = datetime.now().strftime('%H%M%S')
        
        success, response = self.run_test(
            "Unassigned Driver Registration",
            "POST",
            "auth/register",
            200,
            data={
                "username": f"random_{timestamp}",
                "password": "TestPass123!",
                "name": "Random Driver",
                "role": "driver"
            }
        )
        
        if success and 'user' in response:
            user = response['user']
            if user.get('assigned_day') is None:
                print(f"✅ Random driver correctly has no assigned day")
                return True
            else:
                print(f"❌ Random driver incorrectly assigned to {user.get('assigned_day')}")
                return False
        return False

    def test_helper_registration(self):
        """Test helper registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        
        success, response = self.run_test(
            "Helper Registration",
            "POST",
            "auth/register",
            200,
            data={
                "username": f"helper_{timestamp}",
                "password": "TestPass123!",
                "name": "Test Helper",
                "role": "helper"
            }
        )
        
        if success and 'user' in response:
            user = response['user']
            self.helper_token = response['token']
            self.test_helper_id = user['id']
            if user.get('assigned_day') is None and user.get('role') == 'helper':
                print(f"✅ Helper correctly has no assigned day")
                return True
            else:
                print(f"❌ Helper incorrectly assigned day or wrong role")
                return False
        return False

    def test_checklist_template(self):
        """Test checklist template endpoint"""
        if not self.assigned_driver_token:
            print("❌ Skipping checklist template test - no assigned driver token")
            return False
            
        success, response = self.run_test(
            "Checklist Template",
            "GET",
            "checklist/template",
            200,
            headers={"Authorization": f"Bearer {self.assigned_driver_token}"}
        )
        
        if success:
            # Verify structure
            if 'assigned_day' not in response or 'categories' not in response:
                print("❌ Missing required fields in checklist template")
                return False
                
            # Verify assigned day
            if response['assigned_day'] != 'Monday':
                print(f"❌ Wrong assigned day: {response['assigned_day']}")
                return False
                
            # Verify all categories are present
            categories = response['categories']
            for expected_cat in self.expected_categories:
                if expected_cat not in categories:
                    print(f"❌ Missing category: {expected_cat}")
                    return False
                    
            # Verify categories have items
            for cat, items in categories.items():
                if not isinstance(items, list) or len(items) == 0:
                    print(f"❌ Category {cat} has no items")
                    return False
                    
            print(f"✅ Checklist template has all {len(self.expected_categories)} categories")
            return True
        return False

    def test_checklist_template_helper_access(self):
        """Test that helpers cannot access checklist template"""
        if not self.helper_token:
            print("❌ Skipping helper checklist access test - no helper token")
            return False
            
        success, response = self.run_test(
            "Checklist Template (Helper Access)",
            "GET",
            "checklist/template",
            403,
            headers={"Authorization": f"Bearer {self.helper_token}"}
        )
        return success

    def test_checklist_current(self):
        """Test current checklist endpoint"""
        if not self.assigned_driver_token:
            print("❌ Skipping current checklist test - no assigned driver token")
            return False
            
        success, response = self.run_test(
            "Current Checklist",
            "GET",
            "checklist/current",
            200,
            headers={"Authorization": f"Bearer {self.assigned_driver_token}"}
        )
        
        if success:
            # Verify structure
            required_fields = ['user_id', 'user_name', 'week_start', 'completed', 'items']
            for field in required_fields:
                if field not in response:
                    print(f"❌ Missing field in current checklist: {field}")
                    return False
                    
            print(f"✅ Current checklist structure correct")
            return True
        return False

    def test_checklist_submit_incomplete(self):
        """Test checklist submission with incomplete data"""
        if not self.assigned_driver_token:
            print("❌ Skipping incomplete checklist test - no assigned driver token")
            return False
            
        # Submit incomplete checklist (missing items)
        success, response = self.run_test(
            "Checklist Submit (Incomplete)",
            "POST",
            "checklist/submit",
            400,
            data={"items": {"Motor": {"verificar óleo do motor": "OK"}}},
            headers={"Authorization": f"Bearer {self.assigned_driver_token}"}
        )
        return success

    def test_checklist_submit_complete(self):
        """Test complete checklist submission"""
        if not self.assigned_driver_token:
            print("❌ Skipping complete checklist test - no assigned driver token")
            return False
            
        # First get template to build complete submission
        template_success, template = self.run_test(
            "Get Template for Submission",
            "GET",
            "checklist/template",
            200,
            headers={"Authorization": f"Bearer {self.assigned_driver_token}"}
        )
        
        if not template_success:
            return False
            
        # Build complete checklist data
        complete_items = {}
        for category, items in template['categories'].items():
            complete_items[category] = {}
            for item in items:
                complete_items[category][item] = "OK - Verificado"
                
        success, response = self.run_test(
            "Checklist Submit (Complete)",
            "POST",
            "checklist/submit",
            200,
            data={"items": complete_items},
            headers={"Authorization": f"Bearer {self.assigned_driver_token}"}
        )
        
        if success and response.get('completed'):
            print("✅ Checklist submitted successfully")
            return True
        return False

    def test_dashboard_checklist_blocking(self):
        """Test that dashboard shows checklist completion status"""
        if not self.assigned_driver_token:
            print("❌ Skipping dashboard checklist test - no assigned driver token")
            return False
            
        success, response = self.run_test(
            "Dashboard Checklist Status",
            "GET",
            "user/dashboard",
            200,
            headers={"Authorization": f"Bearer {self.assigned_driver_token}"}
        )
        
        if success:
            # Verify checklist_completed field exists
            if 'checklist_completed' not in response:
                print("❌ Missing checklist_completed field in dashboard")
                return False
                
            # Should be True after completing checklist
            if response['checklist_completed']:
                print("✅ Dashboard shows checklist completed")
                return True
            else:
                print("❌ Dashboard shows checklist not completed")
                return False
        return False

    def test_helper_dashboard_no_checklist(self):
        """Test that helper dashboard doesn't require checklist"""
        if not self.helper_token:
            print("❌ Skipping helper dashboard test - no helper token")
            return False
            
        success, response = self.run_test(
            "Helper Dashboard (No Checklist)",
            "GET",
            "user/dashboard",
            200,
            headers={"Authorization": f"Bearer {self.helper_token}"}
        )
        
        if success:
            # Helper should always have checklist_completed as True
            if response.get('checklist_completed', False):
                print("✅ Helper dashboard doesn't require checklist")
                return True
            else:
                print("❌ Helper dashboard incorrectly requires checklist")
                return False
        return False

    def test_admin_checklists(self):
        """Test admin view all checklists"""
        if not self.admin_token:
            print("❌ Skipping admin checklists test - no admin token")
            return False
            
        success, response = self.run_test(
            "Admin View All Checklists",
            "GET",
            "admin/checklists",
            200,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        
        if success:
            print(f"✅ Admin can view {len(response)} checklists")
            # Verify structure if checklists exist
            if len(response) > 0:
                checklist = response[0]
                required_fields = ['user_id', 'user_name', 'week_start', 'completed']
                for field in required_fields:
                    if field not in checklist:
                        print(f"❌ Missing field in admin checklist: {field}")
                        return False
            return True
        return False

def main():
    print("🚛 Commission Tracker API Testing")
    print("=" * 50)
    
    tester = CommissionTrackerAPITester()
    
    # Test sequence
    tests = [
        ("Admin Login", tester.test_admin_login),
        ("User Registration", tester.test_user_registration),
        ("User Dashboard", tester.test_user_dashboard),
        ("Admin Get Users", tester.test_admin_get_users),
        ("Admin Update Delivery", tester.test_admin_update_delivery),
        ("Admin Get User Deliveries", tester.test_admin_get_user_deliveries),
        ("Commission Calculation", tester.test_commission_calculation),
        ("Unauthorized Access", tester.test_unauthorized_access),
        ("Invalid Data Handling", tester.test_invalid_data)
    ]
    
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if not test_func():
                failed_tests.append(test_name)
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            failed_tests.append(test_name)
    
    # Print results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if failed_tests:
        print(f"❌ Failed tests: {', '.join(failed_tests)}")
        return 1
    else:
        print("✅ All tests passed!")
        return 0

if __name__ == "__main__":
    sys.exit(main())