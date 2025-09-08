# PHAROS Laser Virtual Clone

## Introduction

The PHAROS laser system is controlled via a local REST API that runs on port 20020. During development of automation applications, developers need access to a laser system for testing, which is often not available or practical due to:

- **Limited hardware access**: Physical laser systems are expensive and may not be available during development
- **Safety concerns**: Testing on real laser hardware can be dangerous during early development phases  
- **Development efficiency**: Need for rapid iteration without hardware dependencies
- **Parallel development**: Multiple developers working on different features simultaneously

This project provides a **virtual clone** of the PHAROS laser REST API using FastAPI that duplicates the behavior depicted in the official API reference. The clone provides:

- **1:1 API compatibility** with the original PHAROS REST API
- **Three-tier endpoint structure**: `/Basic`, `/Advanced`, and `/Raw` endpoints
- **Realistic state simulation** without complex physics modeling
- **Identical response formats** and data types as the original
- **Development-focused** design for testing automation applications

## 🏗️ API Structure

The PHAROS API is split into three main sections:

### `/v1/Basic` - Casual, often-used features
- Power and frequency control (`ActualOutputPower`, `ActualOutputFrequency`)
- State management (`ActualStateName`, `GeneralStatus`)
- Output control (`EnableOutput`, `CloseOutput`, `TurnOn`, `TurnOff`)
- Preset management (`SelectedPresetIndex`, `ApplySelectedPreset`)
- Attenuator control (`TargetAttenuatorPercentage`, `ActualAttenuatorPercentage`)

### `/v1/Advanced` - More complex functionality  
- Detailed state information (`ActualStateId`)
- Hardware configuration (`IsShutterUsedToControlOutput`)
- Advanced preset management with detailed parameters
- Pulse picker and burst mode controls

### `/v1/Raw` - Low-level functionality (advanced users only)
- Direct wrapper function execution
- Low-level hardware access simulation

## 📦 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- FastAPI and dependencies (see requirements.txt)

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd PHAROS-Clone

# Install dependencies
pip install -r requirements.txt
```

## 🚀 Usage

### Starting the Virtual Laser
```bash
# Start on default port 20020 (same as real PHAROS)
python pharos.py

# Start on custom port
python pharos.py 8080

# Example: Start on port 3000
python pharos.py 3000
```

### Accessing Documentation
Once the server is running, you can access:
- **Interactive API documentation**: `http://localhost:20020/` 
- **Complete endpoint reference** with examples and state machine documentation
- **Searchable interface** for quick endpoint lookup

### Basic API Usage
Once running, the virtual laser will be available at:
```
http://localhost:<port>/v1/
```

**Documentation Access:**
- **PHAROS API Reference**: http://localhost:20020/ (original documentation)
- **Interactive API Docs**: http://localhost:20020/docs (FastAPI Swagger UI)
- **API Information**: http://localhost:20020/info (JSON endpoint info)

**Examples:**
```bash
# Get all basic properties
curl http://localhost:20020/v1/Basic

# Get actual output power
curl http://localhost:20020/v1/Basic/ActualOutputPower

# Set attenuator percentage
curl -X PUT http://localhost:20020/v1/Basic/TargetAttenuatorPercentage \
  -H "Content-Type: application/json" \
  -d "75.5"

# Turn on the laser
curl -X POST http://localhost:20020/v1/Basic/TurnOn

# Enable output
curl -X POST http://localhost:20020/v1/Basic/EnableOutput
```

## 🔧 Development Features

### State Machine Simulation
The virtual laser maintains realistic state transitions:
- `StateDisconnected` → `StateOff` → `StateStandingBy` → `StateOperational` → `StateEmissionOn`
- Proper state validation for operations (e.g., can't enable output when off)
- Realistic timing for state transitions

### Response Compatibility
- **Identical JSON structure** to real PHAROS API
- **Same data types** (numeric values as strings where specified)
- **Compatible error responses** and status codes
- **Matching endpoint paths** and HTTP methods

### Testing Support
- **Deterministic behavior** for repeatable tests
- **Immediate response** to state changes for fast iteration
- **Full endpoint coverage** matching the original API reference

## 🧪 Testing Your Application

This virtual clone is designed to be a drop-in replacement for testing applications that will interface with real PHAROS lasers:

1. **Develop against the clone** using `http://localhost:20020`
2. **Test all API interactions** without hardware dependencies  
3. **Validate state machine logic** with rapid iteration
4. **Switch to real hardware** by simply changing the base URL

## ⚠️ Important Notes

- **Development tool only**: Not intended for production use
- **No persistence**: State resets on restart
- **Single instance**: Designed for one virtual laser at a time
- **No real hardware control**: Pure simulation for development purposes

## 📚 API Reference

For complete API documentation, refer to the original PHAROS API documentation. This clone implements the same endpoints with identical behavior for development purposes.

## 🤝 Contributing

This project is designed as a development aid. Contributions should focus on:
- Maintaining exact API compatibility
- Improving state simulation accuracy
- Adding missing endpoint implementations
- Enhancing development experience

---

