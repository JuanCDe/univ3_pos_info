"""
Info de posición en Uniswap V3
Enlaces útiles:
https://docs.uniswap.org/sdk/subgraph/subgraph-data
https://github.com/Uniswap/v3-subgraph/blob/main/schema.graphql#L192
"""
import yaml
from src.univ3_pos_info.info_pos import InfoPos

config_file = yaml.safe_load(open("../../config_pos.yml"))

if __name__ == "__main__":
    info_pos = InfoPos(config_file["pos_id"])
    try:
        info_pos.get_summary()
    except Exception:
        print("[ERROR]: During execution")
