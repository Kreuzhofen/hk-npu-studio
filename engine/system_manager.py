"""
HK NPU STUDIO

System Manager

Created by Holger Kreuzhofen
Phoenix Engine
"""

import version


class SystemManager:
    def __init__(self, hardware, plugins, skills):
        self.hardware = hardware
        self.plugins = plugins
        self.skills = skills

    def get_status(self):
        plugin_list = self.plugins.scan()
        skill_list = self.skills.list_skills()
        hardware_info = self.hardware.get_system_info()

        return {
            "app_name": version.APP_NAME,
            "version": version.VERSION,
            "codename": version.CODENAME,
            "author": version.AUTHOR,
            "hardware": hardware_info,
            "plugin_count": len(plugin_list),
            "skill_count": len(skill_list),
            "skills": skill_list,
            "qnn_available": hardware_info.get("qnn_available", False),
            "is_arm64": hardware_info.get("is_arm64", False),
        }