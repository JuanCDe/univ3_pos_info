from datetime import datetime

from queries import query_thegraph
from calc_fees import fee_token
from utils import human_readable


class InfoPos:
    def __init__(self, pos_id):
        # from https://github.com/atiselsts/uniswap-v3-liquidity-math/blob/master/subgraph-liquidity-query-example.py
        # https://thegraph.com/hosted-service/subgraph/ianlapham/uniswap-v3-subgraph
        # entities https://github.com/Uniswap/v3-subgraph/blob/main/schema.graphql
        # https://docs.uniswap.org/sdk/subgraph/subgraph-examples

        # Get position current info
        query_current = """query position($position_id: ID!) {
                            position(id:$position_id) {
                              id
                              pool {
                                id
                                feeGrowthGlobal0X128
                                feeGrowthGlobal1X128
                                tick
                                token0Price
                                token1Price
                              }
                              tickLower {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                              }
                              tickUpper {
                                tickIdx
                                feeGrowthOutside0X128
                                feeGrowthOutside1X128
                              }
                              liquidity
                              depositedToken0
                              depositedToken1
                              
                              withdrawnToken0
                              withdrawnToken1
                              
                              collectedFeesToken0
                              collectedFeesToken1
                              
                              feeGrowthInside0LastX128
                              feeGrowthInside1LastX128
                              token0 {
                                symbol
                                id
                                decimals
                              }
                              token1 {
                                id
                                symbol
                                decimals
                              }
                              transaction {
                                id
                                timestamp
                              }
                              owner
                              }
                            }
                    """
        variables_current = {"position_id": pos_id}
        obj = query_thegraph(query_current, variables_current)

        try:
            self.pool = obj['data']['position']
            pool_contract = self.get_pool_id()
            origin_addr = self.get_owner()
        except TypeError:
            print("Not able to get info from position")
            return None


        # Get closing info
        query_closing = """query position($pool_contract: String, $origin_addr: String) {
          burns(orderBy: timestamp,
            orderDirection: desc,
            first:1000,
            where:{
              origin: $origin_addr,
              pool: $pool_contract})
          {
            tickUpper
            tickLower
            timestamp
            amountUSD
          }
        }
        """
        variables_closing = {"pool_contract": pool_contract, "origin_addr": origin_addr}
        obj = query_thegraph(query_closing, variables_closing)
        closing_info = [burn for burn in obj['data']['burns']
                        if burn["tickUpper"] == str(self.get_upper()) and
                        burn["tickLower"] == str(self.get_lower())]
        if not closing_info:
            self.closing_info = []
        else:
            self.closing_info = closing_info[0]


        # Get opening info (if any)
        query_opening = """query position($pool_contract: String, $origin_addr: String) {
          mints(orderBy: timestamp,
            orderDirection: desc,
            first:1000,
            where:{
              origin: $origin_addr,
              pool: $pool_contract})
          {
            tickUpper
            tickLower
            timestamp
            amount0
            amount1
            amountUSD
          }
        }
        """
        variables_opening = {"pool_contract": pool_contract, "origin_addr": origin_addr}
        obj = query_thegraph(query_opening, variables_opening)

        try:
            opening_info = [mint for mint in obj['data']['mints']
                            if mint["tickUpper"] == str(self.get_upper()) and
                            mint["tickLower"] == str(self.get_lower())]
            self.opening_info = opening_info[0]
        except Exception:
            print("Position doesn't exist")
            return None

    # Functions to get minting conditions
    def get_opening_time(self):
        return datetime.utcfromtimestamp(int(self.opening_info["timestamp"]))

    def get_opening_value(self):
        return float(self.opening_info["amountUSD"])

    def get_owner(self):
        return self.pool["owner"]

    def get_id(self):
        return self.pool["id"]

    def get_pool_id(self):
        return self.pool["pool"]["id"]

    def get_current_tick(self):
        return int(self.pool["pool"]["tick"])

    def get_lower(self):
        # pool_id_extra = self.pool["pool"]["id"] + "#-"
        return int(self.pool["tickLower"]["tickIdx"])

    def get_lower_price(self):
        raw_price = 1.0001**self.get_lower()
        decimals_difference = abs(self.get_token1_decimals() - self.get_token0_decimals())
        lower_price = raw_price / 10**decimals_difference
        return lower_price

    def get_upper(self):
        # pool_id_extra = self.pool["pool"]["id"] + "#"
        return int(self.pool["tickUpper"]["tickIdx"])

    def get_upper_price(self):
        raw_price = 1.0001**self.get_upper()
        decimals_difference = abs(self.get_token1_decimals() - self.get_token0_decimals())
        upper_price = raw_price / 10**decimals_difference
        return upper_price

    def get_deposited_token0(self):
        return float(self.pool["depositedToken0"])

    def get_deposited_token1(self):
        return float(self.pool["depositedToken1"])

    def get_token0_contract(self):
        return self.pool["token0"]["id"]

    def get_token0_symbol(self):
        return self.pool["token0"]["symbol"]

    def get_token0_decimals(self):
        return int(self.pool["token0"]["decimals"])

    def get_token1_contract(self):
        return self.pool["token1"]["id"]

    def get_token1_symbol(self):
        return self.pool["token1"]["symbol"]

    def get_token1_decimals(self):
        return int(self.pool["token1"]["decimals"])

    def get_mint_ts(self):
        timestamp = int(self.pool["transaction"]["timestamp"])
        return datetime.utcfromtimestamp(timestamp)

    # Get current conditions
    def get_pos_status(self):
        if self.get_current_liquidity() == 0:
            return "Closed"
        elif self.get_upper() <= self.get_current_tick():
            return "Over the range"
        elif self.get_current_tick() <= self.get_lower():
            return "Below the range"
        elif self.get_upper() >= self.get_current_tick() >= self.get_lower():
            return "On range"
        else:
            return "Out range"

    def get_current_liquidity(self):
        return float(self.pool["liquidity"])

    # Get closing conditions
    def get_closing_time(self):
        if self.get_pos_status() == "Closed":
            return datetime.utcfromtimestamp(int(self.closing_info["timestamp"]))
        else:
            print("Position still open")
            return None

    def get_closing_value(self):
        if self.get_pos_status() == "Closed":
            return float(self.closing_info["amountUSD"])
        else:
            print("Position still open")
            return None

    def get_tick_dict(self):
        tick_dict = {"lower": self.get_lower(), "current": self.get_current_tick(), "upper": self.get_upper()}
        return tick_dict

    # Get fees??
    def get_fee_token(self, token_x):
        decimals = self.get_token0_decimals() if token_x == "token0" else self.get_token1_decimals()
        feetoken = fee_token(pool=self.pool, token=token_x, liquidity=self.get_current_liquidity(),
                             decimals=decimals, ticks_dict=self.get_tick_dict())
        return feetoken

    def get_amount_token0(self, sqrt_lower, sqrt_upper):
        sqrt_liquidity = self.get_current_liquidity() * 2 ** 96
        decimals_token0 = self.get_token0_decimals()
        # Obtener la cantidad de token base
        # Se reordenan los ticks del rango
        if sqrt_lower > sqrt_upper:
            sqrt_lower, sqrt_upper = sqrt_upper, sqrt_lower
        # Fórmula 4 de Elsts
        amount_token0 = (sqrt_liquidity * (sqrt_upper - sqrt_lower) / sqrt_upper / sqrt_lower) / (10 ** decimals_token0)
        # amount_token0 = liquidity * ((sqrt_upper - sqrt_lower) / (sqrt_upper * sqrt_lower)) / (10 ** decimals_token0)
        return amount_token0

    def get_amount_token1(self, sqrt_lower, sqrt_upper):
        liquidity = self.get_current_liquidity()
        decimals_token1 = self.get_token1_decimals()
        # Se reordenan los ticks del rango
        if sqrt_lower > sqrt_upper:
            sqrt_lower, sqrt_upper = sqrt_upper, sqrt_lower
        # Formula 8 de Elsts
        amount_token1 = liquidity * (sqrt_upper - sqrt_lower) / 2 ** 96 / 10 ** decimals_token1
        # amount_token1 = liquidity * (sqrt_upper - sqrt_lower)
        return amount_token1

    def get_amount_token(self):
        tick = self.get_current_tick()
        tick_lower = self.get_lower()
        tick_upper = self.get_upper()

        sqrt = (1.0001**(tick/2) * (2**96))
        sqrt_lower = (1.0001**(tick_lower/2) * (2**96))
        sqrt_upper = (1.0001**(tick_upper/2) * (2**96))

        if sqrt_lower > sqrt_upper:
            sqrt_lower, sqrt_upper = sqrt_upper, sqrt_lower

        if sqrt <= sqrt_lower:
            amount_token0 = self.get_amount_token0(sqrt_lower, sqrt_upper)
            return amount_token0, 0

        elif sqrt_lower < sqrt < sqrt_upper:
            amount_token0 = self.get_amount_token0(sqrt, sqrt_upper)
            amount_token1 = self.get_amount_token1(sqrt_lower, sqrt)
            return amount_token0, amount_token1

        else:
            amount_token1 = self.get_amount_token1(sqrt_lower, sqrt_upper)
            return 0, amount_token1

    def get_summary(self):
        current_token0, current_token1 = self.get_amount_token()
        print(f'\n{"#"*15} INFO {"#"*15}\n'
              f'Status: {self.get_pos_status()}\n'
              f'Pair: {self.get_token0_symbol()}/{self.get_token1_symbol()}\n'
              f'Owner: {self.get_owner()}\n'
              f'\n{"#"*15} TICKS {"#"*15}\n'
              f'Current tick: {self.get_current_tick()}\n'
              f'Ranges (ticks): {self.get_upper()} <-> {self.get_lower()}\n'
              f'Ranges (price): {self.get_upper_price()} <-> {self.get_lower_price()}\n'
              f'\n{"#"*15} OPENING INFO {"#"*15}\n'
              f'Opening date: {self.get_opening_time().strftime("%c")}\n'
              f'Opening: {human_readable(self.get_deposited_token0())} {self.get_token0_symbol()} | '
              f'{human_readable(self.get_deposited_token1())} {self.get_token1_symbol()}\n'
              f'Opening value ($): {human_readable(self.get_opening_value())}\n'
              f'\n{"#"*15} CURRENT INFO {"#"*15}\n'
              f'Current funds: {human_readable(current_token0)} {self.get_token0_symbol()} | '
              f'{human_readable(current_token1)} {self.get_token1_symbol()}\n'
              f'Fees on {self.get_token0_symbol()}: {human_readable(self.get_fee_token("token0"))}\n'
              f'Fees on {self.get_token1_symbol()}: {human_readable(self.get_fee_token("token1"))}\n'
              )
        if self.get_pos_status() == "Close":
            print(f'\n{"#"*15} CLOSING INFO {"#"*15}\n'
                  f'Closing time: {self.get_closing_time()}\n'
                  f'Duration: {self.get_closing_time() - self.get_opening_time()}\n'
                  f'Closing value ($): {round(self.get_closing_value(), 2)}\n'
                  f'Diff value ($): {round(self.get_opening_value() - self.get_closing_value(), 2)}\n')

        print(f'{"#"*15} LINKS {"#"*15}\n'
              f'Revert URL: https://revert.finance/#/uniswap-position/mainnet/{self.get_id()}\n'
              f'Uniswap URL: https://app.uniswap.org/#/pool/{self.get_id()}\n')



