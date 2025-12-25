import json
from typing import Any, Dict
from tau_bench.envs.tool import Tool

class DeleteHomeScene(Tool):
    @staticmethod
    def invoke(
        data: Dict[str, Any],
        home_name: str,
        scene_id: str,
        delete_automation_actions: bool = True,
    ) -> str:
        """
        Delete a scene and cascade delete related actions.
        Optionally deletes routine actions that reference this scene.
        """

        if not isinstance(data, dict):
            return json.dumps({"success": False, "error": "Invalid data container"})

        homes = data.get("homes")
        scenes = data.get("scenes")
        scene_actions = data.get("scene_actions")
        scene_action_attributes = data.get("scene_action_attributes")
        routine_actions = data.get("routine_actions")
        routine_action_attributes = data.get("routine_action_attributes")

        if not isinstance(homes, dict):
            return json.dumps({"success": False, "error": "homes store missing"})
        if not isinstance(scenes, dict):
            return json.dumps({"success": False, "error": "scenes store missing"})

        if not isinstance(home_name, str) or not home_name.strip():
            return json.dumps({"success": False, "error": "home_name must be provided"})
        home_name = home_name.strip()

        # Find home by name
        home_id = None
        for hid, home in homes.items():
            if home.get("home_name", "").strip().lower() == home_name.lower():
                home_id = hid
                break
        if not home_id:
            return json.dumps({"success": False, "error": f"Home '{home_name}' not found"})

        if not isinstance(scene_id, str) or not scene_id.strip():
            return json.dumps({"success": False, "error": "scene_id must be provided"})
        scene_id = scene_id.strip()

        if scene_id not in scenes:
            return json.dumps({"success": False, "error": f"Scene '{scene_id}' not found"})

        if scenes[scene_id].get("home_id") != home_id:
            return json.dumps({"success": False, "error": f"Scene '{scene_id}' does not belong to home '{home_name}'"})

        deleted_scene = scenes.pop(scene_id)

        # Track deleted automation references
        deleted_automation_actions = []

        # Delete routine_actions that reference this scene (if delete_automation_actions is True)
        if delete_automation_actions and isinstance(routine_actions, dict):
            routine_action_ids_to_delete = [
                k for k, v in routine_actions.items() 
                if v.get("target_scene_id") == scene_id
            ]
            
            # Delete routine_action_attributes for these actions
            if isinstance(routine_action_attributes, dict):
                for attr_id in list(routine_action_attributes.keys()):
                    if routine_action_attributes[attr_id].get("action_id") in routine_action_ids_to_delete:
                        routine_action_attributes.pop(attr_id)
            
            # Delete the routine actions and track them
            for action_id in routine_action_ids_to_delete:
                deleted_action = routine_actions.pop(action_id)
                deleted_automation_actions.append({
                    "action_id": action_id,
                    "routine_id": deleted_action.get("routine_id")
                })

        # Delete scene_actions and their attributes
        if isinstance(scene_actions, dict):
            action_ids_to_delete = [k for k, v in scene_actions.items() if v.get("scene_id") == scene_id]
            
            if isinstance(scene_action_attributes, dict):
                for attr_id in list(scene_action_attributes.keys()):
                    if scene_action_attributes[attr_id].get("scene_action_id") in action_ids_to_delete:
                        scene_action_attributes.pop(attr_id)
            
            for action_id in action_ids_to_delete:
                scene_actions.pop(action_id)

        # Prepare response
        response = {
            "success": True,
            "deleted_scene": {
                "scene_id": deleted_scene.get("scene_id") or scene_id,
                "scene_name": deleted_scene.get("scene_name"),
            }
        }

        # Add automation info if any were deleted
        if deleted_automation_actions:
            response["deleted_automation_references"] = {
                "count": len(deleted_automation_actions),
                "actions": deleted_automation_actions
            }

        return json.dumps(response)

    @staticmethod
    def get_info() -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": "delete_home_scene",
                "description": "Delete a scene and all its actions. If delete_automation_actions is true, will also delete any routine actions that reference this scene as a target.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "home_name": {
                            "type": "string",
                            "description": "Name of the home.",
                        },
                        "scene_id": {
                            "type": "string",
                            "description": "Identifier of the scene to delete.",
                        },
                        "delete_automation_actions": {
                            "type": "boolean",
                            "description": "If true, will delete automation actions that reference this scene. If false, only the scene itself is deleted. Defaults to true.",
                        },
                    },
                    "required": ["home_name", "scene_id"],
                },
            },
        }