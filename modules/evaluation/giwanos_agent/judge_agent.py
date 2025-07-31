class JudgeAgent:
    def evaluate_files(self, file_info, threshold_days):
        actions = {"move": [], "keep": []}
        for file_path, days_since_accessed in file_info:
            if days_since_accessed > threshold_days or file_path.endswith(("_test.py", "_old.py", ".tmp")):
                actions["move"].append(file_path)
            else:
                actions["keep"].append(file_path)
        return actions