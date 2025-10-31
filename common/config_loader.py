import os
import json
import yaml
from dotenv import load_dotenv

class ConfigLoader:
    def __init__(self, config_dir):
        """
        config_dir: 项目配置所在目录
        """
        self.config_dir = config_dir
        self.config = {}
        # 优先读取环境变量
        load_dotenv(os.path.join(config_dir, '.env'))

    def load_json(self, filename="wallet.json"):
        path = os.path.join(self.config_dir, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.config.update(json.load(f))
        return self

    def load_yaml(self, filename="config.yaml"):
        path = os.path.join(self.config_dir, filename)
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                self.config.update(yaml.safe_load(f))
        return self

    def load_env(self, keys=None):
        """
        keys: 要读取的环境变量列表, 默认读取所有已配置的 keys
        """
        if keys:
            for k in keys:
                value = os.getenv(k)
                if value is not None:
                    self.config[k] = value
        else:
            # 读取已有键，覆盖 config
            for k in self.config.keys():
                value = os.getenv(k)
                if value is not None:
                    self.config[k] = value
        return self

    def get(self, key, default=None):
        return self.config.get(key, default)