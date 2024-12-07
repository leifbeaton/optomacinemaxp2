# optomacinemaxp2
Optoma Cinemax P2 API to ADB

Container build to expose a RESTful API to control an Optoma Cinemax P2 projector - and likely other Android based projectors as well.

The server.py can be used on its own if you prefer to run it outside of containers, but ensure ADB is installed and present on said system. If you prefer containers, a Dockerfile is present for your convenience.


ADB-Based Projector Control API
This API allows you to control an Optoma projector (or any compatible Android-based device) using ADB commands via a RESTful API.

Features
Power Control: Turn the projector on/off, check power status.
Input Switching: Switch between HDMI inputs (1, 2, or 3).
Volume Control: Adjust volume, mute/unmute, or set a specific volume level.
Brightness Control: Set screen brightness.
Device Info: Retrieve basic device information.
Remote Control: Simulate remote key presses.
Custom ADB Commands: Execute arbitrary ADB commands.
System Management: Reboot or factory reset the projector.
Prerequisites
ADB Installed: Ensure ADB is installed and accessible on the machine running this API.

Download ADB
Python: Install Python 3.6+.

Projector Setup:

Ensure the projector is on the same network as the machine running this API.
Enable ADB debugging on the projector.
Docker (Optional): You can run this API in a Docker container for isolation.

Setup Instructions
1. Clone the Repository
bash
Copy code
git clone https://github.com/leifbeaton/optomacinemaxp2.git
cd projector-control-api
2. Install Dependencies
bash
Copy code
pip install flask
3. Run the API
bash
Copy code
python app.py
The API will be available at http://<your-server-ip>:8080.

4. (Optional) Run with Docker
Build and run the API in a Docker container:

bash
Copy code
docker build -t projector-api .
docker run -d -p 8080:8080 --name projector-api projector-api
Usage
Base URL
arduino
Copy code
http://<your-server-ip>:8080
1. Set the Projector IP
Endpoint: /api/set-ip
Method: POST
Payload:

json
Copy code
{
  "ip": "192.168.1.100"
}
2. Power Control
Check Power Status
Endpoint: /api/power/status
Method: GET

Turn On
Endpoint: /api/power/on
Method: POST

Turn Off
Endpoint: /api/power/off
Method: POST

3. Input Switching
Switch to HDMI Input
Endpoint: /api/input/hdmi
Method: POST
Payload:
json
Copy code
{
  "hdmi": 1
}
Replace 1 with 2 or 3 for other HDMI inputs.
4. Volume Control
Mute/Unmute
Endpoint: /api/audio/mute
Method: POST
Payload:

json
Copy code
{
  "mute": true
}
Increase Volume
Endpoint: /api/audio/increase
Method: POST

Decrease Volume
Endpoint: /api/audio/decrease
Method: POST

Set Volume Level
Endpoint: /api/audio/set-level
Method: POST
Payload:

json
Copy code
{
  "level": 50
}
5. Brightness Control
Set Brightness
Endpoint: /api/display/brightness
Method: POST
Payload:
json
Copy code
{
  "level": 70
}
6. Remote Control
Simulate remote control key presses.
Endpoint: /api/remote/<key>
Method: POST

Supported Keys:

left, right, up, down, ok, home, back
volume_up, volume_down, quick_menu, android_settings, focus
Example: Press the home key.

bash
Copy code
curl -X POST http://<your-server-ip>:8080/api/remote/home
7. Custom ADB Command
Execute any ADB command.
Endpoint: /api/adb/custom
Method: POST
Payload:

json
Copy code
{
  "command": "shell input keyevent 26"
}
8. System Management
Reboot
Endpoint: /api/system/reboot
Method: POST

Factory Reset
Endpoint: /api/system/factory-reset
Method: POST
Payload:

json
Copy code
{
  "timestamp": 1693555200
}
Use /api/get-timestamp to fetch the current server timestamp.

9. Device Information
Retrieve Device Info
Endpoint: /api/device/info
Method: GET
Contribution
Feel free to submit pull requests or issues to improve this API.

License

