from flask import Flask, request, jsonify
import subprocess
import os
import time

app = Flask(__name__)

# Path to store the projector IP configuration
CONFIG_FILE = "/app/projector_config.txt"

# Global variable to hold the projector IP
projector_ip = None


# Helper function to connect ADB to the projector
def adb_connect(ip):
    try:
        result = subprocess.check_output(["adb", "connect", ip], stderr=subprocess.STDOUT, text=True)
        if "connected" in result or "already connected" in result:
            return True, result.strip()
        else:
            return False, result.strip()
    except subprocess.CalledProcessError as e:
        return False, e.output.strip()


# Load the projector IP from the config file on container start
if os.path.exists(CONFIG_FILE):
    with open(CONFIG_FILE, "r") as f:
        projector_ip = f.read().strip()
    # Attempt to connect to the stored IP
    success, message = adb_connect(projector_ip)
    if not success:
        print(f"Failed to connect to projector at {projector_ip}: {message}")


@app.route('/api/set-ip', methods=['POST'])
def set_projector_ip():
    global projector_ip
    ip = request.json.get("ip")
    if not ip:
        return jsonify({"success": False, "error": "IP address is required"}), 400

    projector_ip = ip
    # Save the IP to the config file
    with open(CONFIG_FILE, "w") as f:
        f.write(ip)

    # Attempt to connect to the projector
    success, message = adb_connect(ip)
    if success:
        return jsonify({"success": True, "message": f"Connected to projector at {ip}"})
    else:
        return jsonify({"success": False, "error": f"Failed to connect to {ip}: {message}"}), 400


@app.route('/api/power/status', methods=['GET'])
def check_power():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400

    try:
        # Run dumpsys power and capture output
        result = subprocess.check_output(["adb", "shell", "dumpsys", "power"], stderr=subprocess.STDOUT, text=True)

        # Check for wakefulness
        is_awake = "mWakefulness=Awake" in result

        # Check for SCREEN_BRIGHT_WAKE_LOCK
        screen_bright_lock = any("SCREEN_BRIGHT_WAKE_LOCK" in line for line in result.splitlines())

        # Infer state based on SCREEN_BRIGHT_WAKE_LOCK
        if is_awake and screen_bright_lock:
            return jsonify({"success": True, "power": "on"})
        elif is_awake and not screen_bright_lock:
            return jsonify({"success": True, "power": "standby"})
        else:
            return jsonify({"success": True, "power": "off"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/power/on', methods=['POST'])
def power_on():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400

    try:
        power_status = check_power().get_json().get("power")
        if power_status == "on":
            return jsonify({"success": True, "message": "Projector is already on"})

        subprocess.run(["adb", "shell", "input", "keyevent", "26"], check=True)  # Keycode for POWER
        return jsonify({"success": True, "message": "Power on command sent"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/power/off', methods=['POST'])
def power_off():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400

    try:
        power_status = check_power().get_json().get("power")
        if power_status == "off":
            return jsonify({"success": True, "message": "Projector is already off"})

        subprocess.run(["adb", "shell", "input", "keyevent", "26"], check=True)  # Keycode for POWER
        subprocess.run(["adb", "shell", "input", "keyevent", "23"], check=True)  # Keycode for OK
        return jsonify({"success": True, "message": "Power off command sent"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/input/hdmi', methods=['POST'])
def switch_to_hdmi():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400

    hdmi_number = request.json.get("hdmi")
    if hdmi_number not in [1, 2, 3]:
        return jsonify({"success": False, "error": "Invalid HDMI number. Must be 1, 2, or 3"}), 400

    try:
        commands = [
            ["adb", "shell", "am", "start", "-n", "com.optoma.inputsource.projector.p1/.MainActivity"],
            ["adb", "shell", "input", "keyevent", "21"],  # Left
            ["adb", "shell", "input", "keyevent", "21"],
            ["adb", "shell", "input", "keyevent", "21"],
            ["adb", "shell", "input", "keyevent", "21"],
            ["adb", "shell", "input", "keyevent", "21"],
        ]

        right_presses = hdmi_number - 1
        for _ in range(right_presses):
            commands.append(["adb", "shell", "input", "keyevent", "22"])  # Right

        commands.append(["adb", "shell", "input", "keyevent", "23"])  # OK

        for command in commands:
            subprocess.run(command, check=True)

        return jsonify({"success": True, "message": f"Switched to HDMI {hdmi_number}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/system/reboot', methods=['POST'])
def reboot_system():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400
    try:
        subprocess.run(["adb", "shell", "reboot"], check=True)
        return jsonify({"success": True, "message": "Projector is rebooting"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/remote/<key>', methods=['POST'])
def remote_control(key):
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400

    key_events = {
        "left": 21, "right": 22, "up": 19, "down": 20, "ok": 23,
        "home": 3, "volume_up": 24, "volume_down": 25, "back": 4,
        "quick_menu": 82, "android_settings": 176, "focus": "focus"
    }

    if key == "focus":
        try:
            subprocess.run(["adb", "shell", "input", "keyevent", "--longpress", "176"], check=True)
            return jsonify({"success": True, "message": "Focus command executed"})
        except subprocess.CalledProcessError as e:
            return jsonify({"success": False, "error": e.output.strip()}), 500

    if key not in key_events:
        return jsonify({"success": False, "error": f"Invalid key: {key}"}), 400

    try:
        subprocess.run(["adb", "shell", "input", "keyevent", str(key_events[key])], check=True)
        return jsonify({"success": True, "message": f"{key.capitalize()} key pressed"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/adb/custom', methods=['POST'])
def custom_adb_command():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400
    command = request.json.get("command")
    if not command:
        return jsonify({"success": False, "error": "ADB command is required"}), 400
    try:
        result = subprocess.check_output(["adb"] + command.split(), stderr=subprocess.STDOUT, text=True)
        return jsonify({"success": True, "output": result})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 400


@app.route('/api/get-timestamp', methods=['GET'])
def get_timestamp():
    return jsonify({"success": True, "timestamp": int(time.time())})


@app.route('/api/device/info', methods=['GET'])
def get_device_info():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400

    try:
        # Fetch basic device information
        model = subprocess.check_output(["adb", "shell", "getprop", "ro.product.model"], text=True).strip()
        android_version = subprocess.check_output(["adb", "shell", "getprop", "ro.build.version.release"], text=True).strip()
        uptime = subprocess.check_output(["adb", "shell", "uptime"], text=True).strip()
        return jsonify({
            "success": True,
            "model": model,
            "android_version": android_version,
            "uptime": uptime,
            "ip_address": projector_ip
        })
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/system/factory-reset', methods=['POST'])
def factory_reset():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400

    # Verify the provided timestamp
    timestamp = request.json.get("timestamp")
    if not timestamp:
        return jsonify({"success": False, "error": "Timestamp is required"}), 400

    try:
        server_time = int(time.time())
        if abs(server_time - timestamp) > 60:  # Allow ±1 minute
            return jsonify({"success": False, "error": "Timestamp verification failed"}), 400

        # Perform factory reset
        subprocess.run(["adb", "shell", "am", "broadcast", "-a", "android.intent.action.MASTER_CLEAR"], check=True)
        return jsonify({"success": True, "message": "Factory reset initiated"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/display/brightness', methods=['POST'])
def set_brightness():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400
    brightness_level = request.json.get("level")
    if brightness_level is None or not (0 <= brightness_level <= 100):
        return jsonify({"success": False, "error": "Brightness level must be between 0 and 100"}), 400
    try:
        subprocess.run(["adb", "shell", "settings", "put", "system", "screen_brightness", str(brightness_level)], check=True)
        return jsonify({"success": True, "message": f"Brightness set to {brightness_level}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/audio/mute', methods=['POST'])
def mute_audio():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400
    mute = request.json.get("mute")
    if mute not in [True, False]:
        return jsonify({"success": False, "error": "Mute value must be true or false"}), 400
    try:
        subprocess.run(["adb", "shell", "input", "keyevent", "164"], check=True)  # KEYCODE_MUTE
        action = "muted" if mute else "unmuted"
        return jsonify({"success": True, "message": f"Audio {action}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/audio/increase', methods=['POST'])
def increase_volume():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400
    try:
        subprocess.run(["adb", "shell", "input", "keyevent", "24"], check=True)  # KEYCODE_VOLUME_UP
        return jsonify({"success": True, "message": "Volume increased"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/audio/decrease', methods=['POST'])
def decrease_volume():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400
    try:
        subprocess.run(["adb", "shell", "input", "keyevent", "25"], check=True)  # KEYCODE_VOLUME_DOWN
        return jsonify({"success": True, "message": "Volume decreased"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


@app.route('/api/audio/set-level', methods=['POST'])
def set_volume_level():
    if not projector_ip:
        return jsonify({"success": False, "error": "Projector IP not set"}), 400

    volume_level = request.json.get("level")
    if volume_level is None or not (0 <= volume_level <= 100):
        return jsonify({"success": False, "error": "Volume level must be between 0 and 100"}), 400

    try:
        # Handle volume level `0` as a special case
        if volume_level == 0:
            subprocess.run(["adb", "shell", "input", "keyevent", "164"], check=True)  # KEYCODE_MUTE
            return jsonify({"success": True, "message": "Volume set to 0 (muted)"})

        # Set volume level for other values
        subprocess.run(["adb", "shell", "media", "volume", "--set", str(volume_level)], check=True)
        return jsonify({"success": True, "message": f"Volume set to {volume_level}"})
    except subprocess.CalledProcessError as e:
        return jsonify({"success": False, "error": e.output.strip()}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
