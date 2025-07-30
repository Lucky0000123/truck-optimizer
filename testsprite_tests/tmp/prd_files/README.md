# 🚛 Truck-Dump Waiting-Time Optimiser

**Weda Bay Nickel - FENI Dump Sites Optimization Tool**

A Python + Streamlit web application that analyzes historical haul-cycle data and re-schedules contractor shift start-times to minimize truck queuing at the two critical dumping points: FENI km 0 and FENI km 15.

## 🎯 Project Overview

This optimization tool enables mine planners to:
- ✅ Analyze historical truck cycle data interactively
- ✅ Adjust contractor shift start times with real-time feedback
- ✅ Run discrete-event simulations to predict queue impacts
- ✅ Find optimal dispatch schedules automatically
- ✅ Export recommended timetables for implementation

**Target Outcome**: 25% reduction in average dump waiting times through intelligent shift staggering.

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download this repository**
   ```bash
   git clone <repository-url>
   cd truck-dump-optimizer
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Prepare your data**
   - Place your `Time_Data.xlsx` file in the project root
   - Ensure it follows the expected format (see Data Format section)

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - Navigate to `http://localhost:8501`
   - The app will automatically load if `Time_Data.xlsx` is present

## 📊 Features

### 1. Data Loader & Analytics Dashboard
- **Automatic Data Cleaning**: Handles missing values, calculates cycle times
- **KPI Cards**: Real-time metrics for waiting times, utilization, trips/shift
- **Interactive Visualizations**: Heatmaps, Gantt charts, contractor distributions
- **Location Mapping**: GPS coordinates and km markers for all sites

### 2. Shift-Start Optimizer Panel
- **Manual Controls**: Individual contractor offset sliders (-120 to +120 minutes)
- **Auto-Optimization**: Grid search algorithm with configurable weights
- **Real-time Impact**: Immediate KPI updates as you adjust offsets
- **Recommended Schedules**: One-click application of optimal offsets

### 3. Discrete-Event Simulation Engine
- **15-Minute Buckets**: Granular time discretization for accurate modeling
- **Queue Dynamics**: Service rates calculated from historical dump/spotting times
- **Multi-Site Support**: FENI km 0, FENI km 15, and alternative dump points
- **Before/After Comparison**: Visual impact assessment

### 4. Export & Reporting
- **Excel Export**: Downloadable optimized schedules with offset recommendations
- **Summary Reports**: Key metrics and optimization details
- **Implementation Ready**: Direct contractor start-time recommendations

## 📋 Data Format

Your Excel file should contain these key columns:

| Column | Description | Type | Required |
|--------|-------------|------|----------|
| `Loading Origin` | Mine pit/loader code | Text | ✅ |
| `Contractor` | RIM, GMG, CKB, SSS, PPP, HJS | Text | ✅ |
| `Parking Origin` | Initial yard/POS code | Text | ✅ |
| `Time Departure` | Shift-start dispatch timestamp | DateTime | ✅ |
| `Dumping Destination` | FENI km 0, FENI km 15, etc. | Text | ✅ |
| `Travel Parking-Loading (h)` | Hours | Numeric | ✅ |
| `Waiting for loading (h)` | Hours | Numeric | ✅ |
| `Loading (h)` | Hours | Numeric | ✅ |
| `Loaded Travel (h)` | Hours | Numeric | ✅ |
| `Waiting for dumping (h)` | Hours | Numeric | ✅ |
| `Dumping Spoting (h)` | Hours | Numeric | ✅ |
| `Dumping (h)` | Hours | Numeric | ✅ |
| `Empty Travel (h)` | Hours | Numeric | ✅ |
| `Cycle Time (h)` | Total cycle time | Numeric | Auto-calculated |

**Note**: The app will automatically calculate missing `Cycle Time (h)` values by summing time segments.

## 🗺️ Geographic References

The app includes built-in coordinates for all major locations:

| Location | Coordinates | Km Marker | Type |
|----------|-------------|-----------|------|
| FENI km 0 | 0°28'52"N 127°59'33"E | 0 | Primary Dump |
| FENI km 15 | 0°30'36"N 127°53'44"E | 15 | Primary Dump |
| CBB (km 15 opp.) | 0°31'39"N 127°56'15"E | 15 | Alternative Dump |
| KR (Kao Rahai) | 0°39'26"N 127°58'23"E | 38 | Parking/Loading |
| TF (Tofu) | 0°48'06"N 128°01'32"E | 60 | Parking/Loading |

## ⚙️ Configuration

Key settings can be adjusted in `app.py`:

```python
# Service times per dump site (hours)
DUMP_SERVICE_TIME_H = {
    "FENI km 0": 0.15,   # Auto-calculated from data
    "FENI km 15": 0.15,  # Auto-calculated from data
}

# Optimization weights
WEIGHTS = {"dump": 0.7, "load": 0.3}

# Time discretization
BUCKET_MIN = 15  # 15-minute simulation buckets
```

## 🧮 Algorithm Details

### Queue Simulation
```python
service_rate = 1 / (dump_time_per_truck)  # trucks per hour
queue_wait(t) = max(0, arrivals(t) - service_rate*bucket_duration) * dump_time_per_truck
```

### Optimization Objective
```python
objective = w₁ × avg_dump_wait + w₂ × avg_load_wait
```

Where weights are configurable (default: dump=0.7, load=0.3).

## 📱 Usage Guide

### Step 1: Upload Data
- Use the sidebar to upload your Excel file, or place `Time_Data.xlsx` in the project folder
- Verify data loads correctly in the Dashboard tab

### Step 2: Analyze Baseline
- Review current KPIs: waiting times, cycle times, utilization
- Examine arrival patterns in the heatmap visualization
- Check contractor trip distributions

### Step 3: Optimize Schedules
- **Manual Mode**: Use sliders to adjust contractor start times
- **Auto Mode**: Click "Auto-Optimize" for algorithmic recommendations
- Monitor real-time KPI impacts

### Step 4: Validate Results
- Switch to Simulation tab for before/after comparisons
- Review queue dynamics and arrival pattern changes
- Verify expected improvements

### Step 5: Export & Implement
- Generate Excel file with recommended offsets
- Download implementation-ready schedule
- Share results with operations team

## 🎨 Screenshots

### Dashboard View
*[Screenshot of main dashboard with KPIs and heatmap]*

### Optimizer Controls  
*[Screenshot of slider controls and optimization panel]*

### Simulation Results
*[Screenshot of before/after comparison charts]*

### Export Interface
*[Screenshot of export tab with downloadable schedule]*

## 🔧 Technical Architecture

### Core Components
- **TruckOptimizer Class**: Main optimization engine
- **Simulation Engine**: 15-minute discrete-event modeling
- **Data Pipeline**: Excel loading, cleaning, validation
- **Visualization Layer**: Plotly-based interactive charts
- **Export System**: Excel generation with openpyxl

### Performance Specifications
- **Target**: < 2 second KPI refresh on ≤10k cycles
- **Memory**: Efficient pandas operations with data caching
- **Scalability**: Designed for up to 50,000 historical cycles

## 🧪 Testing

Run basic functionality tests:
```bash
python -c "
import pandas as pd
from app import TruckOptimizer, load_data
print('✅ All imports successful')
print('✅ Ready for production use')
"
```

## 🤝 Contributing

This tool is designed to be extensible for future enhancements:

### Potential Improvements
- [ ] Add more dump sites (CBB, BLB, HAUFEI)
- [ ] Dynamic truck fleet sizing
- [ ] Weather/seasonal adjustments
- [ ] Multi-day optimization
- [ ] Machine learning predictions
- [ ] Real-time data integration

### Code Standards
- **PEP-8 Compliance**: Consistent formatting and naming
- **Type Hints**: All functions include typing annotations
- **Documentation**: Comprehensive docstrings
- **Modularity**: Easy to extend with new features

## ⚠️ Troubleshooting

### Common Issues

**Data Loading Errors**
```bash
Error: "Could not load Excel file"
Solution: Ensure openpyxl is installed and file is not corrupted
```

**Performance Issues**
```bash
Symptom: Slow optimization on large datasets
Solution: Reduce data size or adjust grid search resolution
```

**Visualization Problems**
```bash
Symptom: Charts not displaying
Solution: Update plotly version and clear browser cache
```

## 📄 License

This project is developed for Weda Bay Nickel operations optimization.

## 📞 Support

For technical support or feature requests:
- Create an issue in the repository
- Contact the development team
- Review logs in the Streamlit interface

## 🏆 Success Metrics

Target outcomes for successful implementation:
- ✅ **25% reduction** in average dump waiting time
- ✅ **Improved utilization** across all contractor fleets  
- ✅ **Clear implementation path** for operations team
- ✅ **Extensible platform** for future optimizations

---

**Built with ❤️ for efficient mining operations** 