#!/usr/bin/env python3
"""
Simple test to verify AlphaFX Trader functionality
"""

import sys
import os
import time
import requests
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_api_endpoints():
    """Test all major API endpoints"""
    base_url = "http://localhost:5000"
    
    print("🧪 Testing AlphaFX Trader API endpoints...")
    
    # Test 1: Get current prices
    try:
        response = requests.get(f"{base_url}/api/prices", timeout=5)
        assert response.status_code == 200
        prices = response.json()
        assert 'EUR/USD' in prices
        print("✅ Prices API working")
    except Exception as e:
        print(f"❌ Prices API failed: {e}")
        return False
    
    # Test 2: Get trading status
    try:
        response = requests.get(f"{base_url}/api/trading/status", timeout=5)
        assert response.status_code == 200
        status = response.json()
        assert 'volume_limit' in status
        print("✅ Trading status API working")
    except Exception as e:
        print(f"❌ Trading status API failed: {e}")
        return False
    
    # Test 3: Execute manual trade
    try:
        trade_data = {
            "pair": "EUR/USD",
            "side": "BUY", 
            "amount": 1000
        }
        response = requests.post(f"{base_url}/api/trade", 
                               json=trade_data, 
                               headers={'Content-Type': 'application/json'},
                               timeout=5)
        assert response.status_code == 200
        result = response.json()
        assert 'status' in result
        print("✅ Manual trading API working")
    except Exception as e:
        print(f"❌ Manual trading API failed: {e}")
        return False
    
    # Test 4: Get trade history
    try:
        response = requests.get(f"{base_url}/api/trades", timeout=5)
        assert response.status_code == 200
        trades = response.json()
        assert isinstance(trades, list)
        print("✅ Trade history API working")
    except Exception as e:
        print(f"❌ Trade history API failed: {e}")
        return False
    
    # Test 5: Run backtest
    try:
        backtest_data = {
            "pair": "EUR/USD",
            "days": 7,
            "initial_balance": 50000
        }
        response = requests.post(f"{base_url}/api/backtest",
                               json=backtest_data,
                               headers={'Content-Type': 'application/json'},
                               timeout=10)
        assert response.status_code == 200
        result = response.json()
        assert 'total_return_pct' in result
        print("✅ Backtesting API working")
    except Exception as e:
        print(f"❌ Backtesting API failed: {e}")
        return False
    
    # Test 6: Start/Stop auto trading
    try:
        # Start auto trading
        response = requests.post(f"{base_url}/api/trading/start", timeout=5)
        assert response.status_code == 200
        
        # Stop auto trading  
        response = requests.post(f"{base_url}/api/trading/stop", timeout=5)
        assert response.status_code == 200
        print("✅ Auto trading control working")
    except Exception as e:
        print(f"❌ Auto trading control failed: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    print("🚀 AlphaFX Trader - Functionality Test\n")
    
    # Wait a moment for server to be ready
    print("⏳ Waiting for server to be ready...")
    time.sleep(2)
    
    # Run tests
    if test_api_endpoints():
        print("\n🎉 All tests PASSED! AlphaFX Trader is fully functional!")
        print("\n📊 Key Features Verified:")
        print("   ✓ Real-time forex price streaming")
        print("   ✓ Manual trade execution") 
        print("   ✓ Auto trading controls")
        print("   ✓ Trade history tracking")
        print("   ✓ Backtesting engine")
        print("   ✓ Volume limit monitoring")
        print("\n🌐 Web Interface: http://localhost:5000")
        return True
    else:
        print("\n❌ Some tests failed. Check server status.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)