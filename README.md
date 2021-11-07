# Formant ONVIF adapter
This adapter will connect a ONVIF PTZ camera to the Formant Agent so that it can be teleoperated through the Formant cloud platform.

ONVIF is a standard for how IP products within video surveillance and other physical security areas can communicate with each other.

[Formant](https://formant.io) is a robot data and operations platform that allows companies to remotely manage all aspects of deployed systems, teleoperate them, and collect and analyze the sensor and telemetry data.

## Hardware
Any ONVIF PTZ camera will work with this adapter. These have been well tested and are recommended:

| Item | Zoom | Price |
|------|------|-------|
| [Hikvision compatible camera](https://www.amazon.com/gp/product/B089M9WR7L/) | 18x | $250 |
| [Axis M5065](https://www.bhphotovideo.com/c/product/1390217-REG/axis_communications_01107_004_m5065_palm_sized_ptz_network.html) | 5x | $600 |

## Setup
### Install the Formant Agent
The agent should be installed before the adapter setup script is run.

On the Formant Settings -> Devices page, click `ADD DEVICE` in the top right. 

Name the device `ptz.xyz` where `xyz` is an unused three-digit number.

SSH in to a device on the same network as the PTZ camera to run the installation script.

Follow the provided instructions to walk through the installation and provisioning process, skipping any references to ROS or Catkin as they are not used for this adapter.

### Running in Docker (optional)
This deployment requires python3, pip3, and the Formant agent installed. If you are using a docker agent, it must clone this repository and run the `setup.sh` script to install dependencies.

### Deploy the Formant ONVIF Adapter
Once the ONVIF camera is online and the device connected to Formant, run this script to clone this repository to your home directory:
```
git clone https://github.com/FormantIO/formant-onvif-adapter.git
```

Run the setup script (this could take a very long time while building `grpcio`):
```
cd formant-onvif-adapter
sudo ./setup.sh
```

Run the adapter zip creation script to build a properly formatted zip file for upload to Formant:
```
./create_adapter_zip.sh
```

Take the generated zip file, add upload it as a new adapter:
1. Navigate to `Settings` -> `Adapters` and click `ADD ADAPTER`
2. Name it something like "ONVIF adapter"
2. The `Exec Command` should be `./start.sh`
3. Save the adapter

## Device configuration
### Adapter setup
In your device's configuration, select the adapter and save the configuration. It will automatically start once it has been downloaded to the device.

### Configuration parameters and defaults
Default configuration values can be overridden with agent application configuration variables. The following application configuration parameters can be set on the device's `GENERAL` tab:

| Name | Default Value | Description |
|------------------------|--------------------|--------------------|
| `onvif_ip` | `192.168.1.110` | IP of camera to connect to |
| `onvif_port` | `80` | ONVIF port of camera to connect to |
| `onvif_username` | `admin` | Username of camera to connect to |
| `onvif_password` | `123456` | Password of camera to connect to |
| `pan_rate` | `1.0` |  The rate to affect the pan of the camera |
| `tilt_rate` | `1.0` |  The rate to affect the tilt of the camera |
| `zoom_rate` | `0.5` | The rate to affect the zoom of the camera |

### Telemetry configuration (optional)
Even without the ONVIF adapter, the Formant Agent is able to pick up IP video streams from devices on the local network. 

To add the PTZ camera's stream for recording:
1. Navigate to the device's `TELEMETRY` tab
2. Click `ADD STREAM` and select `HARDWARE`
3. Give the stream a name, such as `PTZ Camera`
4. If desired, select `On demand` to buffer the stream to the device until requested
5. For `Preferred video quality`, select the desired recording quality
6. For `Hardware type`, select `ip`
7. For `Path of Video Hardware Device`, click into the box and select the auto-discovered device, or enter the IP rtsp address manually
8. For `Encoding required`, select `NO`
9. For `Supports ONVIF`, select `YES` and fill in the username and password only if has properly auto-discovered the device
10. Click `DONE` and `SAVE` the device configuration.

### Teleoperation configuration
This adapter is primarily for use with teleoperation. Three items must be configured:

#### Image
1. Click the `+` button next to `IMAGE` and select `Add from Hardware`
2. For `Hardware type`, select `ip`
3. For `RTSP URI`, allow the device to autocomplete or type in the RTSP stream address manually
4. For `Encoding required`, select `NO`
5. For `Supports ONVIF`, select `YES` and fill in the username and password only if has properly auto-discovered the device
6. Click `DONE` and `SAVE` the device configuration

#### Joystick
1. Click the `+` button next to `JOYSTICK` and select `Add from API`
2. Enter `joystick` as the name of the control stream
3. Click `DONE`, and the default joystick configuration will be added, which this adapter uses
4. Click to `SAVE` the device configuration

#### Buttons
1. Click the `+` button next to `BUTTONS` and select `Add from API`
2. Type in `zoom in` as the name of the key, and press `DONE`
3. Click the `+` and select `Add from API` again
4. Type in `zoom out` as the name of the key, and press `DONE`
5. Click to `SAVE` the device configuration

## Usage
To use the adapter, enter teleoperation for your newly created device. 

The joystick will control the camera, and the buttons will allow you to zoom in and out.