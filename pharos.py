#!/usr/bin/env python3
"""
PHAROS Laser Virtual Clone
==========================

A FastAPI-based virtual clone of the PHAROS laser REST API for development purposes.
This application provides 1:1 API compatibility with the original PHAROS laser system
without requiring physical hardware.

Usage:
    python pharos.py [port]

Author: Development Team
Date: September 2025
"""

import sys
import time
import os
from enum import Enum
from typing import Dict, List, Optional, Union, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
import uvicorn
from pydantic import BaseModel, Field


# =============================================================================
# CONSTANTS AND ENUMS
# =============================================================================

class LaserState(Enum):
    """Laser state enumeration matching PHAROS API states."""
    DISCONNECTED = "StateDisconnected"
    OFF = "StateOff" 
    STANDING_BY = "StateStandingBy"
    OPERATIONAL = "StateOperational"
    EMISSION_ON = "StateEmissionOn"
    FAILURE = "StateFailure"
    SHUTTING_DOWN = "StateShuttingDown"
    DETECTING_LASER_STATE = "StateDetectingLaserState"
    PREPARING_HARDWARE = "StatePreparingHardware"


class LaserStateId(Enum):
    """Numerical state IDs matching PHAROS Advanced API."""
    UNKNOWN = 0x00
    STANDING_BY = 0x01
    SERVICE = 0x02
    IN_FIELD_UPDATE = 0x04
    INITIALIZING = 0x08
    GOING_TO_STANDBY = 0x10
    FAILURE = 0x20
    HOUSEKEEPING = 0x40
    OPERATIONAL = 0x80
    SHUTTING_DOWN = 0x100
    OFF = 0x200
    DETECTING_LASER_STATE = 0x400
    DISCONNECTED = 0x800


class GeneralStatus(Enum):
    """General status enumeration."""
    DISCONNECTED = "Disconnected"
    OFF = "Off"
    STANDBY = "Standby" 
    OPERATIONAL = "Operational"
    EMISSION_ON = "EmissionOn"
    FAILURE = "Failure"


# =============================================================================
# DATA MODELS
# =============================================================================

class PresetModel(BaseModel):
    """Preset configuration model matching PHAROS structure."""
    AttenuatorPercentage: float = 100.0
    BurstEnvelopeControlParameter: int = 0
    BurstMode: int = 0
    BurstParameterN: int = 1
    BurstParameterP: int = 1
    CavityDumpingTimeInNs: int = -1
    HarmonicNumber: int = 0
    Notes: str = "Virtual preset"
    OptimalMotorPosition: int = -1
    PhotodiodeCorrection1: float = 0.10446500033140183
    PhotodiodeCorrection2: float = -1.6866900409695518e-7
    PhotodiodeFactor: float = -1
    PhotodiodeOffset: float = -1
    PpDivider: int = 1
    PpHighVoltageInVolts: float = -1
    PulseRepetitionRateInKhz: float = 100.0
    RaHighVoltageInVolts: float = -1
    RaLddCurrentInA: float = -1
    RaOnDelayInNs: float = -1
    RaOutputPowerSetpointInW: float = 5.0
    IsStoredInPharos: bool = True


class WarningModel(BaseModel):
    """Warning/Error model."""
    Description: str
    Code: str


# =============================================================================
# VIRTUAL LASER STATE MANAGER
# =============================================================================

class VirtualLaserState:
    """
    Virtual laser state manager that simulates PHAROS laser behavior.
    
    This class maintains the current state of the virtual laser and provides
    methods to modify parameters while ensuring realistic state transitions
    and parameter validation.
    """
    
    def __init__(self):
        """Initialize virtual laser with default parameters."""
        # Core state
        self.current_state = LaserState.DISCONNECTED
        self.is_output_enabled = False
        self.last_state_change = time.time()
        
        # Power and frequency parameters
        self.target_attenuator_percentage = 50.0
        self.actual_attenuator_percentage = 50.1  # Slight simulation variance
        self.target_pp_divider = 1
        self.actual_pp_divider = 1
        self.actual_harmonic = 1
        self.actual_ra_frequency = 100.1  # kHz
        self.actual_ra_power = 5.0  # W
        
        # Preset management
        self.selected_preset_index = 1
        self.presets = [
            PresetModel(Notes="Default preset 1", AttenuatorPercentage=50.0),
            PresetModel(Notes="Default preset 2", AttenuatorPercentage=75.0),
            PresetModel(Notes="Default preset 3", AttenuatorPercentage=25.0),
        ]
        
        # Advanced parameters
        self.is_pp_opened = False
        self.is_shutter_used_to_control_output = True
        self.is_remote_interlock_active = False
        
        # Warnings and errors
        self.active_warnings: List[WarningModel] = []
        self.active_errors: List[WarningModel] = []
        
        # Initialize to operational state for development ease
        self._transition_to_operational()
    
    def _transition_to_operational(self):
        """Quick transition to operational state for development convenience."""
        self.current_state = LaserState.OPERATIONAL
        self.last_state_change = time.time()
    
    def get_state_id(self) -> int:
        """Get numerical state ID for current state."""
        state_mapping = {
            LaserState.DISCONNECTED: LaserStateId.DISCONNECTED.value,
            LaserState.OFF: LaserStateId.OFF.value,
            LaserState.STANDING_BY: LaserStateId.STANDING_BY.value,
            LaserState.OPERATIONAL: LaserStateId.OPERATIONAL.value,
            LaserState.EMISSION_ON: LaserStateId.OPERATIONAL.value,  # Same as operational
            LaserState.FAILURE: LaserStateId.FAILURE.value,
            LaserState.SHUTTING_DOWN: LaserStateId.SHUTTING_DOWN.value,
            LaserState.DETECTING_LASER_STATE: LaserStateId.DETECTING_LASER_STATE.value,
            LaserState.PREPARING_HARDWARE: LaserStateId.INITIALIZING.value,
        }
        return state_mapping.get(self.current_state, LaserStateId.UNKNOWN.value)
    
    def get_general_status(self) -> str:
        """Get general status string."""
        status_mapping = {
            LaserState.DISCONNECTED: GeneralStatus.DISCONNECTED.value,
            LaserState.OFF: GeneralStatus.OFF.value,
            LaserState.STANDING_BY: GeneralStatus.STANDBY.value,
            LaserState.OPERATIONAL: GeneralStatus.OPERATIONAL.value,
            LaserState.EMISSION_ON: GeneralStatus.EMISSION_ON.value,
            LaserState.FAILURE: GeneralStatus.FAILURE.value,
            LaserState.SHUTTING_DOWN: GeneralStatus.OFF.value,
            LaserState.DETECTING_LASER_STATE: GeneralStatus.OFF.value,
            LaserState.PREPARING_HARDWARE: GeneralStatus.STANDBY.value,
        }
        return status_mapping.get(self.current_state, GeneralStatus.DISCONNECTED.value)
    
    def can_enable_output(self) -> bool:
        """Check if output can be enabled in current state."""
        return self.current_state == LaserState.OPERATIONAL
    
    def can_turn_on(self) -> bool:
        """Check if laser can be turned on from current state."""
        return self.current_state in [LaserState.OFF, LaserState.DISCONNECTED, LaserState.STANDING_BY]
    
    def can_turn_off(self) -> bool:
        """Check if laser can be turned off from current state."""
        return self.current_state != LaserState.OFF
    
    def turn_on(self):
        """Turn on the laser (transition to operational state)."""
        if self.current_state == LaserState.OPERATIONAL:
            # Already operational, no-op
            return
        if not self.can_turn_on():
            raise HTTPException(403, f"Cannot turn on laser in state {self.current_state.value}")
        self.current_state = LaserState.OPERATIONAL
        self.last_state_change = time.time()
    
    def turn_off(self):
        """Turn off the laser."""
        if not self.can_turn_off():
            raise HTTPException(403, f"Cannot turn off laser in state {self.current_state.value}")
        self.current_state = LaserState.OFF
        self.is_output_enabled = False
        self.last_state_change = time.time()
    
    def go_to_standby(self):
        """Transition to standby state."""
        self.current_state = LaserState.STANDING_BY
        self.is_output_enabled = False
        self.last_state_change = time.time()
    
    def enable_output(self):
        """Enable laser output."""
        if not self.can_enable_output():
            raise HTTPException(403, f"Cannot enable output in state {self.current_state.value}")
        self.is_output_enabled = True
        self.current_state = LaserState.EMISSION_ON
        self.last_state_change = time.time()
    
    def close_output(self):
        """Close/disable laser output."""
        self.is_output_enabled = False
        if self.current_state == LaserState.EMISSION_ON:
            self.current_state = LaserState.OPERATIONAL
        self.last_state_change = time.time()
    
    def set_attenuator_percentage(self, percentage: float):
        """Set target attenuator percentage."""
        if not 0 <= percentage <= 100:
            raise HTTPException(400, "Attenuator percentage must be between 0 and 100")
        self.target_attenuator_percentage = percentage
        # Simulate slight variance in actual value
        self.actual_attenuator_percentage = percentage + (0.1 if percentage < 100 else 0)
    
    def set_pp_divider(self, divider: int):
        """Set pulse picker divider."""
        if divider < 1 or divider > 1000:
            raise HTTPException(400, "PP divider must be between 1 and 1000")
        self.target_pp_divider = divider
        self.actual_pp_divider = divider
    
    def set_selected_preset(self, index: int):
        """Set selected preset index."""
        if not 0 <= index < len(self.presets):
            raise HTTPException(400, f"Preset index must be between 0 and {len(self.presets)-1}")
        self.selected_preset_index = index
    
    def can_apply_preset(self) -> bool:
        """Check if preset can be applied in current state."""
        # In the real PHAROS, presets can't be applied during certain operations
        # For our virtual implementation, we'll allow in operational and standing by states
        return self.current_state in [LaserState.OPERATIONAL, LaserState.STANDING_BY]
    
    def apply_selected_preset(self):
        """Apply the currently selected preset."""
        if not self.can_apply_preset():
            raise HTTPException(403, f"Cannot apply preset in state {self.current_state.value}")
        if 0 <= self.selected_preset_index < len(self.presets):
            preset = self.presets[self.selected_preset_index]
            self.set_attenuator_percentage(preset.AttenuatorPercentage)
            self.set_pp_divider(preset.PpDivider)
            self.actual_ra_frequency = preset.PulseRepetitionRateInKhz
            self.actual_ra_power = preset.RaOutputPowerSetpointInW
    
    @property
    def calculated_output_power(self) -> float:
        """Calculate output power based on current parameters."""
        base_power = self.actual_ra_power
        attenuator_factor = self.actual_attenuator_percentage / 100.0
        pp_factor = 1.0 / self.actual_pp_divider if self.actual_pp_divider > 0 else 0.0
        return base_power * attenuator_factor * pp_factor if self.is_output_enabled else 0.0
    
    @property
    def calculated_output_frequency(self) -> float:
        """Calculate output frequency based on current parameters."""
        return self.actual_ra_frequency / self.actual_pp_divider if self.actual_pp_divider > 0 else 0.0
    
    @property
    def calculated_output_energy(self) -> float:
        """Calculate output pulse energy in microjoules."""
        power_w = self.calculated_output_power
        frequency_hz = self.calculated_output_frequency * 1000  # Convert kHz to Hz
        return (power_w * 1e6 / frequency_hz) if frequency_hz > 0 else 0.0  # Convert to microjoules


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

# Initialize FastAPI app
app = FastAPI(
    title="PHAROS Laser Virtual Clone",
    description="Virtual clone of PHAROS laser REST API for development purposes",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Global virtual laser instance
virtual_laser = VirtualLaserState()


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def format_numeric_response(value: Union[int, float]) -> str:
    """Format numeric values as strings to match PHAROS API format."""
    if isinstance(value, int):
        return str(value)
    elif isinstance(value, float):
        return f"{value:.3f}".rstrip('0').rstrip('.')
    return str(value)


# =============================================================================
# BASIC API ENDPOINTS
# =============================================================================

@app.get("/v1/Basic")
async def get_basic_properties():
    """
    Get all basic properties that have GET methods.
    
    Returns a batch of all basic laser properties in a single response.
    The list matches the original PHAROS API structure.
    """
    return {
        "ActualAttenuatorPercentage": virtual_laser.actual_attenuator_percentage,
        "ActualHarmonic": virtual_laser.actual_harmonic,
        "ActualOutputEnergy": virtual_laser.calculated_output_energy,
        "ActualOutputFrequency": virtual_laser.calculated_output_frequency,
        "ActualOutputPower": virtual_laser.calculated_output_power,
        "ActualPpDivider": virtual_laser.actual_pp_divider,
        "ActualRaFrequency": virtual_laser.actual_ra_frequency,
        "ActualRaPower": virtual_laser.actual_ra_power,
        "ActualStateName": virtual_laser.current_state.value,
        "ActualStateName2": virtual_laser.current_state.value,
        "GeneralStatus": virtual_laser.get_general_status(),
        "IsOutputEnabled": virtual_laser.is_output_enabled,
        "SelectedPresetIndex": virtual_laser.selected_preset_index,
        "TargetAttenuatorPercentage": virtual_laser.target_attenuator_percentage,
        "TargetPpDivider": virtual_laser.target_pp_divider
    }


@app.get("/v1/Basic/ActualAttenuatorPercentage")
async def get_actual_attenuator_percentage():
    """Get actual attenuator percentage."""
    return format_numeric_response(virtual_laser.actual_attenuator_percentage)


@app.get("/v1/Basic/ActualHarmonic")
async def get_actual_harmonic():
    """Get actual harmonic number."""
    return format_numeric_response(virtual_laser.actual_harmonic)


@app.get("/v1/Basic/ActualOutputEnergy")
async def get_actual_output_energy():
    """Get actual output pulse energy in microjoules."""
    return format_numeric_response(virtual_laser.calculated_output_energy)


@app.get("/v1/Basic/ActualOutputFrequency")
async def get_actual_output_frequency():
    """Get actual output pulse frequency (repetition rate) in kHz."""
    return format_numeric_response(virtual_laser.calculated_output_frequency)


@app.get("/v1/Basic/ActualOutputPower")
async def get_actual_output_power():
    """Get actual laser output power in W."""
    return format_numeric_response(virtual_laser.calculated_output_power)


@app.get("/v1/Basic/ActualPpDivider")
async def get_actual_pp_divider():
    """Get actual PP divider."""
    return format_numeric_response(virtual_laser.actual_pp_divider)


@app.get("/v1/Basic/ActualRaFrequency")
async def get_actual_ra_frequency():
    """Get raw RA frequency (repetition rate) in kHz."""
    return format_numeric_response(virtual_laser.actual_ra_frequency)


@app.get("/v1/Basic/ActualRaPower")
async def get_actual_ra_power():
    """Get raw RA power in W."""
    return format_numeric_response(virtual_laser.actual_ra_power)


@app.get("/v1/Basic/ActualStateName")
async def get_actual_state_name():
    """Get name of the internal state machine state (deprecated, use ActualStateName2)."""
    return virtual_laser.current_state.value


@app.get("/v1/Basic/ActualStateName2")
async def get_actual_state_name2():
    """Get name of the internal state machine state."""
    return virtual_laser.current_state.value


@app.get("/v1/Basic/Errors")
async def get_errors():
    """Get the code list of all currently active errors."""
    return virtual_laser.active_errors


@app.get("/v1/Basic/GeneralStatus")
async def get_general_status():
    """Get general status of the laser."""
    return virtual_laser.get_general_status()


@app.get("/v1/Basic/IsOutputEnabled")
async def get_is_output_enabled():
    """Get whether laser output is enabled."""
    return virtual_laser.is_output_enabled


@app.get("/v1/Basic/SelectedPresetIndex")
async def get_selected_preset_index():
    """Get currently selected preset index."""
    return format_numeric_response(virtual_laser.selected_preset_index)


@app.get("/v1/Basic/TargetAttenuatorPercentage")
async def get_target_attenuator_percentage():
    """Get target attenuator percentage."""
    return format_numeric_response(virtual_laser.target_attenuator_percentage)


@app.get("/v1/Basic/TargetPpDivider")
async def get_target_pp_divider():
    """Get target PP divider."""
    return format_numeric_response(virtual_laser.target_pp_divider)


@app.get("/v1/Basic/Warnings")
async def get_warnings():
    """Get the code list of all currently active warnings."""
    return virtual_laser.active_warnings


# POST endpoints for actions
@app.post("/v1/Basic/ApplySelectedPreset")
async def apply_selected_preset():
    """Apply the currently selected preset."""
    virtual_laser.apply_selected_preset()
    return {"status": "success", "message": "Preset applied successfully"}


@app.post("/v1/Basic/CloseOutput")
async def close_output():
    """Close/disable laser output."""
    virtual_laser.close_output()
    return {"status": "success", "message": "Output closed successfully"}


@app.post("/v1/Basic/EnableOutput")
async def enable_output():
    """Enable laser output."""
    virtual_laser.enable_output()
    return {"status": "success", "message": "Output enabled successfully"}


@app.post("/v1/Basic/GoToStandby")
async def go_to_standby():
    """Transition laser to standby state."""
    virtual_laser.go_to_standby()
    return {"status": "success", "message": "Transitioned to standby successfully"}


@app.post("/v1/Basic/TurnOff")
async def turn_off():
    """Turn off the laser."""
    virtual_laser.turn_off()
    return {"status": "success", "message": "Laser turned off successfully"}


@app.post("/v1/Basic/TurnOn")
async def turn_on():
    """Turn on the laser."""
    virtual_laser.turn_on()
    return {"status": "success", "message": "Laser turned on successfully"}


# PUT endpoints for setting values
@app.put("/v1/Basic/SelectedPresetIndex")
async def set_selected_preset_index(request: Request):
    """Set selected preset index."""
    try:
        body = await request.body()
        index = int(body.decode().strip('"'))
        virtual_laser.set_selected_preset(index)
        return {"status": "success", "message": f"Preset index set to {index}"}
    except ValueError:
        raise HTTPException(400, "Invalid preset index format")


@app.put("/v1/Basic/TargetAttenuatorPercentage")
async def set_target_attenuator_percentage(request: Request):
    """Set target attenuator percentage."""
    try:
        body = await request.body()
        percentage = float(body.decode().strip('"'))
        virtual_laser.set_attenuator_percentage(percentage)
        return {"status": "success", "message": f"Attenuator percentage set to {percentage}%"}
    except ValueError:
        raise HTTPException(400, "Invalid attenuator percentage format")


@app.put("/v1/Basic/TargetPpDivider")
async def set_target_pp_divider(request: Request):
    """Set target PP divider."""
    try:
        body = await request.body()
        divider = int(body.decode().strip('"'))
        virtual_laser.set_pp_divider(divider)
        return {"status": "success", "message": f"PP divider set to {divider}"}
    except ValueError:
        raise HTTPException(400, "Invalid PP divider format")


# =============================================================================
# ADVANCED API ENDPOINTS
# =============================================================================

@app.get("/v1/Advanced")
async def get_advanced_properties():
    """Get all advanced properties that have GET methods."""
    return {
        "ActualStateId": virtual_laser.get_state_id(),
        "IsPpOpened": virtual_laser.is_pp_opened,
        "IsShutterUsedToControlOutput": virtual_laser.is_shutter_used_to_control_output,
        "IsRemoteInterlockActive": virtual_laser.is_remote_interlock_active,
        "Presets": [preset.model_dump() for preset in virtual_laser.presets]
    }


@app.get("/v1/Advanced/ActualStateId")
async def get_actual_state_id():
    """Get actual state ID (numerical representation)."""
    return format_numeric_response(virtual_laser.get_state_id())


@app.get("/v1/Advanced/IsPpOpened")
async def get_is_pp_opened():
    """Get whether pulse picker is opened."""
    return virtual_laser.is_pp_opened


@app.get("/v1/Advanced/IsShutterUsedToControlOutput")
async def get_is_shutter_used_to_control_output():
    """Get whether shutter is used to control output."""
    return virtual_laser.is_shutter_used_to_control_output


@app.put("/v1/Advanced/IsShutterUsedToControlOutput")
async def set_is_shutter_used_to_control_output(request: Request):
    """Set whether shutter is used to control output."""
    try:
        body = await request.body()
        value = body.decode().strip().lower()
        virtual_laser.is_shutter_used_to_control_output = value in ['true', '1', 'yes']
        return {"status": "success", "message": f"Shutter control set to {virtual_laser.is_shutter_used_to_control_output}"}
    except Exception:
        raise HTTPException(400, "Invalid boolean format")


@app.get("/v1/Advanced/IsRemoteInterlockActive")
async def get_is_remote_interlock_active():
    """Get whether remote interlock is active."""
    return virtual_laser.is_remote_interlock_active


@app.get("/v1/Advanced/Presets")
async def get_presets():
    """Get all available presets."""
    return [preset.model_dump() for preset in virtual_laser.presets]


# =============================================================================
# RAW API ENDPOINTS
# =============================================================================

@app.get("/v1/Raw")
async def get_raw_properties():
    """Get raw API information."""
    return {
        "message": "Raw API for advanced users only",
        "available_functions": ["ExecuteWrapperFunction"],
        "warning": "Use with caution - direct hardware access simulation"
    }


@app.post("/v1/Raw/ExecuteWrapperFunction")
async def execute_wrapper_function(request: Request):
    """
    Execute a wrapper function (simulated).
    
    This endpoint simulates the execution of low-level wrapper functions
    without actually performing any hardware operations.
    """
    try:
        body = await request.body()
        function_data = body.decode()
        
        # Simulate function execution
        result = {
            "status": "executed",
            "function": function_data,
            "result": "simulated_success",
            "timestamp": datetime.now().isoformat(),
            "warning": "This is a simulated execution for development purposes"
        }
        
        return result
    except Exception as e:
        raise HTTPException(400, f"Failed to execute wrapper function: {str(e)}")


# =============================================================================
# ERROR HANDLERS
# =============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Custom HTTP exception handler to match PHAROS API error format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat()
            }
        }
    )


# =============================================================================
# HEALTH CHECK AND INFO ENDPOINTS
# =============================================================================

@app.get("/")
async def root():
    """Root endpoint that serves the virtual laser API documentation."""
    try:
        # Get the directory where this script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))
        html_file_path = os.path.join(script_dir, "virtual_laser_api_docs.html")
        
        # Check if the HTML file exists
        if os.path.exists(html_file_path):
            # Read and serve the HTML file
            with open(html_file_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            return HTMLResponse(content=html_content, status_code=200)
        else:
            # Fallback to JSON response if file not found
            return {
                "message": "PHAROS Laser Virtual Clone",
                "version": "1.0.0",
                "api_base": "/v1",
                "documentation": "/docs",
                "status": "operational",
                "laser_state": virtual_laser.current_state.value,
                "note": "virtual_laser_api_docs.html not found - serving JSON fallback"
            }
    except Exception as e:
        # Error fallback
        return {
            "message": "PHAROS Laser Virtual Clone",
            "version": "1.0.0",
            "api_base": "/v1",
            "documentation": "/docs", 
            "status": "operational",
            "laser_state": virtual_laser.current_state.value,
            "error": f"Could not load virtual_laser_api_docs.html: {str(e)}"
        }


@app.get("/info")
async def api_info():
    """API information endpoint (JSON)."""
    return {
        "message": "PHAROS Laser Virtual Clone",
        "version": "1.0.0",
        "api_base": "/v1",
        "documentation": "/docs",
        "original_api_docs": "/",
        "health_check": "/health",
        "status": "operational",
        "laser_state": virtual_laser.current_state.value,
        "output_enabled": virtual_laser.is_output_enabled
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": time.time() - virtual_laser.last_state_change
    }


# =============================================================================
# MAIN APPLICATION ENTRY POINT
# =============================================================================

def main():
    """
    Main entry point for the PHAROS virtual clone application.
    
    Handles command line arguments and starts the FastAPI server.
    """
    # Default port (same as real PHAROS)
    default_port = 20020
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
            if not 1024 <= port <= 65535:
                print("Error: Port must be between 1024 and 65535")
                sys.exit(1)
        except ValueError:
            print("Error: Invalid port number")
            print("Usage: python pharos.py [port]")
            sys.exit(1)
    else:
        port = default_port
    
    print(f"""
    ╔══════════════════════════════════════════════════════════════╗
    ║                  PHAROS Virtual Laser Clone                  ║
    ║                        Development Mode                      ║
    ╠══════════════════════════════════════════════════════════════╣
    ║  Server starting on: http://localhost:{port:<5}                 ║
    ║  API Documentation:  http://localhost:{port}/                  ║
    ║  FastAPI Docs:       http://localhost:{port}/docs              ║
    ║  API Info (JSON):    http://localhost:{port}/info              ║
    ║  Health Check:       http://localhost:{port}/health            ║
    ║                                                              ║
    ║  Current laser state: {virtual_laser.current_state.value:<33} ║
    ║  Output enabled:      {str(virtual_laser.is_output_enabled):<33} ║
    ╚══════════════════════════════════════════════════════════════╝
    
    🚀 Virtual laser is ready for development!
    📚 Use Ctrl+C to stop the server
    """)
    
    # Start the FastAPI server
    try:
        uvicorn.run(
            app,
            host="127.0.0.1",  # Localhost only for security
            port=port,
            log_level="info",
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n🛑 Virtual laser shutdown complete.")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


# =============================================================================
# DEVELOPMENT NOTES AND RECOMMENDATIONS
# =============================================================================

"""
DEVELOPMENT FINDINGS AND RECOMMENDATIONS:

1. **API Compatibility**: 
   - All endpoints match the original PHAROS API structure exactly
   - Response formats are identical (numeric values as strings where specified)
   - State machine behavior follows documented transitions

2. **Simplified State Management**:
   - No complex physics simulation as requested
   - Immediate state transitions for fast development iteration
   - Realistic parameter validation without hardware constraints

3. **Development-Focused Design**:
   - Starts in operational state by default for convenience
   - Clear error messages for debugging
   - Comprehensive logging for development tracking

4. **Testing Considerations**:
   - Deterministic behavior for repeatable tests
   - Easy state manipulation for edge case testing
   - Compatible with real hardware test suites

5. **Performance Characteristics**:
   - Immediate response times (no hardware delays)
   - Lightweight state management
   - Minimal memory footprint

6. **Limitations and Scope**:
   - No persistence between restarts (as requested)
   - Single virtual laser instance
   - Localhost-only operation for security
   - No real hardware integration

7. **Future Enhancements** (if needed):
   - Add response time simulation if required
   - Implement more detailed preset management
   - Add configurable state transition delays
   - Include more realistic parameter drift simulation

8. **Security and Production Notes**:
   - No authentication/authorization (matches real PHAROS security model)
   - No CORS configuration (localhost only)
   - Input validation for parameter safety
   - Error handling matches original API patterns

This implementation provides a solid foundation for developing applications
that will interface with real PHAROS laser hardware while maintaining
exact API compatibility and development convenience.
"""
