import os
import time
import json
import pathlib
import isodate
import datetime

from onvif import ONVIFCamera

from formant.sdk.agent.v1 import Client as FormantClient

DEFAULT_ONVIF_IP = '192.168.1.110'
DEFAULT_ONVIF_PORT = 80
DEFAULT_ONVIF_USERNAME = 'admin'
DEFAULT_ONVIF_PASSWORD = '123456'
DEFAULT_PTZ_RATE = 1.0
DEFAULT_ZOOM_RATE = 0.5
CONTINUOUS_MOVE_TIMEOUT = isodate.Duration(seconds = 3)
PUBLISH_THROTTLE_SECONDS = 5.0


class FormantONVIFAdapter:
    def __init__(self):
        print("Initializing Formant ONVIF adapter")


        self._debug_mode = True
        
        # Set up the PTZ camera properties
        self._move_timeout = CONTINUOUS_MOVE_TIMEOUT
        self._zoom_timeout = CONTINUOUS_MOVE_TIMEOUT
        self._zoom_rate = DEFAULT_ZOOM_RATE
        self._pan_rate = DEFAULT_PTZ_RATE
        self._tilt_rate = DEFAULT_PTZ_RATE
        self._onvif_wsdl_path = os.path.join(str(pathlib.Path().resolve()), "ver10/wsdl/device")
        self._ptz_connected = False
        self._ptz_cam = None
        self._ptz_service = None
        self._devicemgmt_service = None
        self._media_service = None
        self._master_token = None
        self._encoder_config_options = None
        self._encoder_config = None
        self._camera_config_options = None
        
        # # Create Formant client and register callbacks
        self._fclient = FormantClient(ignore_throttled=True, ignore_unavailable=True)
        self._fclient.register_config_update_callback(self._start_restart)
        self._fclient.create_event("ONVIF Adapter online", notify=False, severity="info")
        self._fclient.register_teleop_callback(self._handle_teleop)

       
        # Wait on ptz services
        while self._devicemgmt_service == None:
            time.sleep(0.01)

        self._start_publishing_state()

    def _formant_log(self, log):
        print(log)
        if self._debug_mode:
            self._fclient.post_text(
                "onvif_adapter.info", log)
            time.sleep(0.25)

    def _start_restart(self):
        print("restarting")
        try:
            self._formant_log("updating config")
            # Pull and set config values
            self._update_config()
            self._formant_log("Starting authentication")
            # Create camera node and services
            self._ptz_cam = ONVIFCamera(
                self._onvif_ip, 
                self._onvif_port, 
                self._onvif_username, 
                self._onvif_password,
                wsdl_dir=self._onvif_wsdl_path
            )
            self._formant_log("ONVIF camera initialized")
            self._ptz_service = self._ptz_cam.create_ptz_service()
            self._formant_log("PTZ service initialized")

            self._devicemgmt_service = self._ptz_cam.create_devicemgmt_service()
            self._formant_log("Device management initialized")
            self._media_service = self._ptz_cam.create_media_service()
            self._formant_log("Media service initialized")
            self._master_token = self._media_service.GetProfiles()[0].Name
            self._formant_log("Token received")
            # Publish the current encoder configuration
            self._encoder_config = self._media_service.GetVideoEncoderConfigurations({})
            encoder_config_str = {"encoder config": eval(self._encoder_config.__repr__())}
            encoder_config_json = json.dumps(encoder_config_str, default=lambda o : o.__str__())
            self._fclient.post_json("onvif_adapter.encoder_config",encoder_config_json)

        except Exception as e:
            self._fclient.post_text("onvif_adapter.errors", "Error starting: %s" % str(e))

    def _update_config(self):
        # Pull new values from app config if they exist
        try:
            self._formant_log("Starting config update")
            self._onvif_ip = str(self._fclient.get_app_config("onvif_ip", DEFAULT_ONVIF_IP))
            self._formant_log("IP: %s" % str(self._onvif_ip))
            self._onvif_port = str(self._fclient.get_app_config("onvif_port", DEFAULT_ONVIF_PORT))
            self._onvif_username = str(self._fclient.get_app_config("onvif_username", DEFAULT_ONVIF_USERNAME))
            self._formant_log("Username: %s" % str(self._onvif_username))
            self._onvif_password = str(self._fclient.get_app_config("onvif_password", DEFAULT_ONVIF_PASSWORD))
            self._pan_rate = float(self._fclient.get_app_config("pan_rate", DEFAULT_PTZ_RATE))
            self._tilt_rate = float(self._fclient.get_app_config("tilt_rate", DEFAULT_PTZ_RATE))
            self._zoom_rate = float(self._fclient.get_app_config("zoom_rate", DEFAULT_ZOOM_RATE))
            debug_string = self._fclient.get_app_config(
                "debug_mode", "false")
            self._debug_mode = debug_string in ["True", "true"]
        except Exception as e:
            self._formant_log("Failed config update %s" % str(e))

    def _set_ptz_connection_state(self, state):
        if (self._ptz_connected == False) and (state == True):
            # Just connected
            self._fclient.create_event("ONVIF camera connected", notify=False, severity="info")

        elif (self._ptz_connected == True) and (state == True):
            # Still connected
            pass

        elif (self._ptz_connected == True) and (state == False):
            # Just disconnected
            self._fclient.create_event("ONVIF camera disconnected", notify=False, severity="warning")

        elif (self._ptz_connected == False) and (state == False):
            # Still disconnected
            pass

        self._ptz_connected = state

    def _start_publishing_state(self):
        while True:
            try:
                if self._ptz_cam.devicemgmt:
                    self._set_ptz_connection_state(True)
                else:
                    self._set_ptz_connection_state(False)

                # Report the adapter state
                self._fclient.post_bitset(
                    "onvif_adapter.state", 
                    {"online": True, "connected": self._ptz_connected}
                )

                # Sleep the publishing process
                time.sleep(PUBLISH_THROTTLE_SECONDS)

            except Exception as e:
                self._fclient.post_text("onvif_adapter.errors", "Error publishing state: %s" %  str(e))

                # Try to restart if it fails
                self._start_restart()

    def _handle_teleop(self, control):
        try:
            if control.stream.casefold() == "joystick".casefold():
                # Handle the joystick to move the camera around
                self._pan_tilt(control)

            elif control.stream.casefold() == "buttons".casefold():
                # Handle the buttons, "zoom in" and "zoom out"
                self._zoom_in_out(control)

        except Exception as e:
            self._fclient.post_text("onvif_adapter.errors", "Error handling teleop: %s" %  str(e))

    def _pan_tilt(self, control):
        #  If any values are passed, move - otherwise stop.
        if control.twist.linear.x or control.twist.angular.z:
            self._ptz_service.ContinuousMove({
                "ProfileToken": self._master_token,
                "Velocity": {
                    "PanTilt": {
                        "x": self._pan_rate * control.twist.angular.z,
                        "y": self._tilt_rate * control.twist.linear.x
                    },
                },
                "Timeout": self._move_timeout
            })
        else:
            self._stop_move()

    def _zoom_in_out(self, control):
        for bit in control.bitset.bits:
            if bit.value:
                if bit.key == "zoom in":
                    self._ptz_service.ContinuousMove({
                        "ProfileToken": self._master_token,
                        "Velocity": {"Zoom": {"x": self._zoom_rate}},
                        "Timeout": self._zoom_timeout
                    })

                if bit.key == "zoom out":
                    self._ptz_service.ContinuousMove({
                        "ProfileToken": self._master_token,
                        "Velocity": {"Zoom": {"x": self._zoom_rate * -1}},
                        "Timeout": self._zoom_timeout
                    })

            else:
                self._stop_move()

    def _stop_move(self):
        self._ptz_service.Stop({"ProfileToken": self._master_token})


if __name__ == "__main__":
    FormantONVIFAdapter()
