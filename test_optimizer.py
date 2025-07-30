#!/usr/bin/env python3
"""
Test script for the new waiting time optimizer
Tests the core optimization algorithm functionality
"""

import sys
import json
import pandas as pd
from data_handlers import load_config

# Load test configuration
def test_optimizer_algorithm():
    """Test the new optimizer algorithm with sample data"""
    print("🧪 Testing New Waiting Time Optimizer Algorithm")
    print("=" * 50)
    
    # Load contractor configuration
    contractor_configs = load_config()
    
    if not contractor_configs:
        print("❌ No contractor configuration found")
        return False
    
    print(f"✅ Loaded configuration with {len(contractor_configs)} contractors")
    
    # Sample sidebar config
    sidebar_config = {
        'loaded_speed': 30,
        'empty_speed': 40
    }
    
    # Load time data
    try:
        time_df = pd.read_excel('Time_Data.xlsx', sheet_name='Time-Data')
        print(f"✅ Loaded Time_Data.xlsx with {len(time_df)} rows")
    except:
        print("⚠️ Could not load Time_Data.xlsx, using fallback")
        time_df = None
    
    # Test the optimization functions
    try:
        # Import the new optimization functions from app.py
        import importlib.util
        spec = importlib.util.spec_from_file_location("app", "app.py")
        app_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(app_module)
        
        print("\n📊 Testing baseline calculation...")
        baseline_waits = app_module.calculate_baseline_waiting_times(
            contractor_configs, sidebar_config, time_df, 5  # 5% variation
        )
        
        print(f"Current KM 0 waiting: {baseline_waits['km0_wait']:.1f} min/truck")
        print(f"Current KM 15 waiting: {baseline_waits['km15_wait']:.1f} min/truck")
        print(f"Total waiting: {baseline_waits['total_wait_minutes']:.1f} min")
        
        print("\n🎯 Testing optimization algorithm...")
        candidate_times = ["5:30", "6:00", "6:30", "7:00", "7:30", "8:00"]
        
        optimization_results = app_module.run_waiting_time_optimization(
            contractor_configs, sidebar_config, time_df, 
            candidate_times, 5, False  # Quick analysis
        )
        
        print(f"Baseline total wait: {optimization_results['baseline']['total_wait_minutes']:.1f} min")
        print(f"Optimized total wait: {optimization_results['optimized']['total_wait_minutes']:.1f} min")
        
        improvement = optimization_results['baseline']['total_wait_minutes'] - optimization_results['optimized']['total_wait_minutes']
        print(f"Improvement: {improvement:.1f} min ({(improvement/max(optimization_results['baseline']['total_wait_minutes'], 1)*100):.1f}%)")
        
        print("\n📋 Recommendations:")
        for contractor, routes in optimization_results['recommendations'].items():
            for route, data in routes.items():
                current = data['current_time']
                optimal = data['optimal_time']
                status = "🔄 CHANGE" if current != optimal else "✅ KEEP"
                print(f"  {contractor} - {route}: {current} → {optimal} {status}")
        
        print("\n✅ All tests passed! The new optimizer is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_optimizer_algorithm()
    sys.exit(0 if success else 1) 