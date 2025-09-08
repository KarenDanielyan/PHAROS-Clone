# Project Structure

```
PHAROS-Clone/
├── README.md                       # Complete project documentation
├── requirements.txt                # Python dependencies
├── pharos.py                       # Main FastAPI application
├── test_pharos.py                  # Comprehensive test suite
├── verify_installation.py          # Quick verification script
├── virtual_laser_api_docs.html     # Custom OpenAPI-style documentation
├── PHAROS_API.html                 # Original API reference (for development)
├── PROJECT_STRUCTURE.md            # This file
└── LICENSE                         # Project license
```

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start the virtual laser:**
   ```bash
   python pharos.py 20020
   ```

3. **Verify installation:**
   ```bash
   python verify_installation.py 20020
   ```

4. **Run full test suite:**
   ```bash
   python -m pytest test_pharos.py -v
   ```

## API Endpoints Implemented

### Basic API (/v1/Basic)
- ✅ GET `/Basic` - Batch properties
- ✅ GET `/Basic/ActualOutputPower` - Current power output
- ✅ GET `/Basic/ActualStateName` - Current state
- ✅ GET `/Basic/GeneralStatus` - General status
- ✅ GET `/Basic/IsOutputEnabled` - Output status
- ✅ POST `/Basic/TurnOn` - Turn on laser
- ✅ POST `/Basic/TurnOff` - Turn off laser
- ✅ POST `/Basic/EnableOutput` - Enable output
- ✅ POST `/Basic/CloseOutput` - Disable output
- ✅ PUT `/Basic/TargetAttenuatorPercentage` - Set attenuator
- ✅ PUT `/Basic/TargetPpDivider` - Set PP divider

### Advanced API (/v1/Advanced)
- ✅ GET `/Advanced` - Batch advanced properties
- ✅ GET `/Advanced/ActualStateId` - Numerical state ID
- ✅ GET `/Advanced/Presets` - Available presets
- ✅ PUT `/Advanced/IsShutterUsedToControlOutput` - Shutter config

### Raw API (/v1/Raw)
- ✅ GET `/Raw` - Raw API information
- ✅ POST `/Raw/ExecuteWrapperFunction` - Execute functions

## Development Features

- 🚀 Instant startup and response
- 🔧 Realistic parameter validation
- 📊 Comprehensive error handling with proper HTTP status codes:
  - 400 (Bad Request) for invalid parameters
  - 403 (Forbidden) for state-based restrictions  
  - 404 (Not Found) for missing endpoints
- 🧪 Full test coverage (41 tests)
- 📚 Interactive API documentation
- 🎯 1:1 compatibility with PHAROS API
