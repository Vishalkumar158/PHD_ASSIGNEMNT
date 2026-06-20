import json
from pathlib import Path
from datetime import datetime
import yaml


class ExperimentManager:
    def __init__(self, base_dir="experiments"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.exp_dir = Path(base_dir) / f"exp_{timestamp}"
        self.exp_dir.mkdir(parents=True, exist_ok=True)

    def save_config(self, config):
        with open(self.exp_dir / "config.yaml", "w") as f:
            yaml.dump(config, f)

    def save_metrics(self, metrics):
        with open(self.exp_dir / "metrics.json", "w") as f:
            json.dump(metrics, f, indent=2)

    def save_results(self, results):
        with open(self.exp_dir / "results.json", "w") as f:
            json.dump(results, f, indent=2)