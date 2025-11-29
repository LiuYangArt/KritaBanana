import os
import json


class PresetManager:
    def __init__(self):
        self.config_file = os.path.join(os.path.dirname(__file__), "presets.json")
        self.presets = {}
        self.load()

    def load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    self.presets = json.load(f)
            except Exception as e:
                print(f"Error loading presets: {e}")
                self.presets = {}
        else:
            self.presets = {}

    def save(self):
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.presets, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving presets: {e}")

    def get_all_names(self):
        return sorted(list(self.presets.keys()))

    def get_prompt(self, name):
        return self.presets.get(name, "")

    def add_preset(self, name, prompt):
        if name in self.presets:
            return False, "Preset already exists."
        self.presets[name] = prompt
        self.save()
        return True, "Preset added."

    def update_preset(self, name, prompt):
        # Updates the content of an existing preset, or creates if not exists (but usually used for saving over)
        self.presets[name] = prompt
        self.save()
        return True, "Preset saved."

    def rename_preset(self, old_name, new_name):
        if old_name not in self.presets:
            return False, "Original preset not found."
        if new_name in self.presets:
            return False, "New name already exists."

        prompt = self.presets.pop(old_name)
        self.presets[new_name] = prompt
        self.save()
        return True, "Preset renamed."

    def delete_preset(self, name):
        if name in self.presets:
            del self.presets[name]
            self.save()
            return True, "Preset deleted."
        return False, "Preset not found."
