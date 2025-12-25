import json
from typing import Any, Dict, Optional
from tau_bench.envs.tool import Tool


class CreateNewSceneAction(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        scene_id: str,
        device_id: str,
        device_attributes: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a new scene action linking a scene to a device with optional device attributes.
        """
        if not isinstance(data, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid data format: 'data' must be a dict"
            })

        scene_actions_dict = data.get("scene_actions", {})
        if not isinstance(scene_actions_dict, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid scene_actions container: expected dict at data['scene_actions']"
            })

        scenes_dict = data.get("scenes", {})
        if not isinstance(scenes_dict, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid scenes container: expected dict at data['scenes']"
            })

        devices_dict = data.get("devices", {})
        if not isinstance(devices_dict, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid devices container: expected dict at data['devices']"
            })

        scene_action_attributes_dict = data.get("scene_action_attributes", {})
        if not isinstance(scene_action_attributes_dict, dict):
            return json.dumps({
                "success": False,
                "error": "Invalid scene_action_attributes container: expected dict at data['scene_action_attributes']"
            })

        # Validate required parameters
        if not scene_id:
            return json.dumps({
                "success": False,
                "error": "scene_id is required"
            })

        if not device_id:
            return json.dumps({
                "success": False,
                "error": "device_id is required"
            })

        scene_id_str = str(scene_id).strip()
        device_id_str = str(device_id).strip()

        # Validate scene exists
        if scene_id_str not in scenes_dict:
            return json.dumps({
                "success": False,
                "error": f"Scene with ID '{scene_id_str}' not found"
            })

        # Validate device exists
        if device_id_str not in devices_dict:
            return json.dumps({
                "success": False,
                "error": f"Device with ID '{device_id_str}' not found"
            })

        # Generate new scene_action_id
        numeric_ids = []
        for key in scene_actions_dict.keys():
            try:
                numeric_ids.append(int(key))
            except (TypeError, ValueError):
                continue
        new_scene_action_id = str(max(numeric_ids, default=0) + 1)

        timestamp = "2025-12-19T23:59:00"

        # Get scene and device info for action_name
        scene_info = scenes_dict[scene_id_str]
        device_info = devices_dict[device_id_str]
        scene_name = scene_info.get("scene_name", "Unknown Scene")
        device_name = device_info.get("device_name", "Unknown Device")

        # Create new scene action record
        new_scene_action = {
            "scene_action_id": new_scene_action_id,
            "scene_id": scene_id_str,
            "device_id": device_id_str,
            "created_at": timestamp,
            "action_name": f"{scene_name} - Control {device_name}"
        }

        # Add to data
        scene_actions_dict[new_scene_action_id] = new_scene_action

        # Parse and create device attributes if provided
        created_attributes = []
        if device_attributes:
            try:
                if not isinstance(device_attributes, dict):
                    return json.dumps({
                        "success": False,
                        "error": "device_attributes must be a dictionary"
                    })

                attrs_dict = device_attributes

                # Generate attribute IDs
                attr_numeric_ids = []
                for key in scene_action_attributes_dict.keys():
                    try:
                        attr_numeric_ids.append(int(key))
                    except (TypeError, ValueError):
                        continue

                # Create attribute records
                for attr_name, attr_value in attrs_dict.items():
                    if not isinstance(attr_name, str) or not attr_name.strip():
                        continue

                    new_attr_id = str(max(attr_numeric_ids, default=0) + 1)
                    attr_numeric_ids.append(int(new_attr_id))

                    attr_value_str = str(attr_value) if attr_value is not None else ""

                    new_attribute = {
                        "attribute_id": new_attr_id,
                        "scene_action_id": new_scene_action_id,
                        "attribute_name": attr_name.strip(),
                        "attribute_value": attr_value_str,
                        "created_at": timestamp,
                        "attribute_description": f"Configure {attr_name.strip()}: {attr_value_str}"
                    }

                    scene_action_attributes_dict[new_attr_id] = new_attribute
                    created_attributes.append(new_attribute)

            except Exception as e:
                return json.dumps({
                    "success": False,
                    "error": f"Error processing device_attributes: {str(e)}"
                })

        return json.dumps({
            "success": True,
            "scene_action": new_scene_action,
            "attributes": created_attributes
        })

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "create_new_scene_action",
                "description": "Create a new scene action linking a scene to a device. Optionally accepts device_attributes as a JSON object (dictionary) to create scene action attributes. Validates that the scene and device exist before creating the action. Possible device_attributes depend on device_type: camera (power, recording, motion_detection), bulb (power, brightness), thermostat (power, mode, temperature, target_temperature), speaker (power, playback_state, volume, mute), door_lock (lock_state), motion_sensor (motion_state), temperature_sensor (temperature), humidity_sensor (humidity), light_sensor (brightness_level), door_sensor (door_state), water_leak_sensor (leak_state), smoke_detector_sensor (smoke_state), power_outlet (power, power_consumption), air_conditioner (power, mode, temperature, target_temperature).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scene_id": {
                            "type": "string",
                            "description": "The ID of the scene to add the action to."
                        },
                        "device_id": {
                            "type": "string",
                            "description": "The ID of the device to control in this scene action."
                        },
                        "device_attributes": {
                            "type": "object",
                            "description": "Optional JSON object (dictionary) of device attributes. Attribute values are numeric without units (e.g., brightness 0-100, temperature 32-104, volume 0-100).",
                            "properties": {
                                "power": {
                                    "type": "string",
                                    "description": "Power state (for camera, bulb, thermostat, speaker, power_outlet, air_conditioner): possible values: on, off"
                                },
                                "recording": {
                                    "type": "string",
                                    "description": "Recording state (for camera): possible values: recording, paused, stopped"
                                },
                                "motion_detection": {
                                    "type": "string",
                                    "description": "Motion detection state (for camera): possible values: motion_detected, clear"
                                },
                                "brightness": {
                                    "type": "number",
                                    "description": "Brightness level 0 to 100 (for bulb)"
                                },
                                "mode": {
                                    "type": "string",
                                    "description": "Mode (for thermostat: heating/cooling/idle; for air_conditioner: cooling/idle): possible values: heating, cooling, idle"
                                },
                                "temperature": {
                                    "type": "number",
                                    "description": "Temperature 32 to 104 (for thermostat, temperature_sensor, air_conditioner)"
                                },
                                "target_temperature": {
                                    "type": "number",
                                    "description": "Target temperature 60 to 90 for thermostat, 60 to 85 for air_conditioner"
                                },
                                "playback_state": {
                                    "type": "string",
                                    "description": "Playback state (for speaker): possible values: playing, paused, stopped"
                                },
                                "volume": {
                                    "type": "number",
                                    "description": "Volume level 0 to 100 (for speaker): possible values: 0-100 for speaker"
                                },
                                "mute": {
                                    "type": "string",
                                    "description": "Mute state (for speaker): possible values: muted, unmuted"
                                },
                                "lock_state": {
                                    "type": "string",
                                    "description": "Lock state (for door_lock): possible values: locked, unlocked"
                                },
                                "motion_state": {
                                    "type": "string",
                                    "description": "Motion state (for motion_sensor): possible values: motion_detected, clear"
                                },
                                "humidity": {
                                    "type": "number",
                                    "description": "Humidity level 0 to 100 (for humidity_sensor)"
                                },
                                "brightness_level": {
                                    "type": "number",
                                    "description": "Brightness level 0 to 65535 (for light_sensor)"
                                },
                                "door_state": {
                                    "type": "string",
                                    "description": "Door state (for door_sensor): possible values: open, closed"
                                },
                                "leak_state": {
                                    "type": "string",
                                    "description": "Leak state (for water_leak_sensor): possible values: leak_detected, no_leak"
                                },
                                "smoke_state": {
                                    "type": "string",
                                    "description": "Smoke state (for smoke_detector_sensor): possible values: smoke_detected, no_smoke, alarm_triggered"
                                },
                                "power_consumption": {
                                    "type": "number",
                                    "description": "Power consumption 0 to 3680 (for power_outlet)"
                                }
                            },
                            "additionalProperties": False
                        }
                    },
                    "required": ["scene_id", "device_id"]
                }
            }
        }