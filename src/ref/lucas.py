## Thanks to https://twitter.com/JNP7771 for the script at https://playcode.io/780618/

## imports
import requests
import json
import pandas as pd
import math

x96 = math.pow(2, 96)
x128 = math.pow(2, 128)
exampleNFTid = "254607"
graphqlEndpoint = "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3"

def getPosition(id):
    print("Uni Position Query")

    positionRes = r = requests.post(graphqlEndpoint, json={'query': positionQuery.replace("%1", id)})

    # Setting up some variables to keep things shorter & clearer
    data = json.loads(r.text)
    position = data["data"]["position"]
    positionLiquidity = position["liquidity"]
    pool = position["pool"]
    decimalDifference = int(position["token1"]["decimals"], 10) - int(position["token0"]["decimals"], 10)
    [symbol_0, symbol_1] = [position["token0"]["symbol"], position["token1"]["symbol"]]

    # Prices (not decimal adjusted)
    priceCurrent = sqrtPriceToPrice(pool["sqrtPrice"])
    priceUpper = float(position["tickUpper"]["price0"])
    priceLower = float(position["tickLower"]["price0"])

    # Square roots of the prices (not decimal adjusted)
    priceCurrentSqrt = float(pool["sqrtPrice"]) / math.pow(2, 96)
    priceUpperSqrt = math.sqrt(float(position["tickUpper"]["price0"]))
    priceLowerSqrt = math.sqrt(float(position["tickLower"]["price0"]))

    # Prices (decimal adjusted)
    priceCurrentAdjusted = sqrtPriceToPriceAdjusted(
        pool["sqrtPrice"],
        decimalDifference
    )
    priceUpperAdjusted = float(position["tickUpper"]["price0"]) / math.pow(10, decimalDifference)
    priceLowerAdjusted = float(position["tickLower"]["price0"]) / math.pow(10, decimalDifference)

    # Prices (decimal adjusted and reversed)
    priceCurrentAdjustedReversed = 1 / priceCurrentAdjusted
    priceLowerAdjustedReversed = 1 / priceUpperAdjusted
    priceUpperAdjustedReversed = 1 / priceLowerAdjusted

    positionLiquidity = int(positionLiquidity)

    # The amount calculations using positionLiquidity & current, upper and lower priceSqrt
    amount_0, amount_1 = 0, 0
    if (priceCurrent <= priceLower):
        amount_0 = float(positionLiquidity * int(1 / priceLowerSqrt - 1 / priceUpperSqrt))
        amount_1 = 0
    elif (priceCurrent < priceUpper):
        amount_0 = float(positionLiquidity * int(1 / priceCurrentSqrt - 1 / priceUpperSqrt))
        amount_1 = float(positionLiquidity * int(priceCurrentSqrt - priceLowerSqrt))
    else:
        amount_1 = float(positionLiquidity * int(priceUpperSqrt - priceLowerSqrt))
        amount_0 = 0


    # Decimal adjustment for the amounts
    print(amount_0)
    amount_0_Adjusted = amount_0 / math.pow(10, float(position["token0"]["decimals"]))
    amount_1_Adjusted = amount_1 / math.pow(10, float(position["token1"]["decimals"]))

    # Check out the relevant formulas below which are from Uniswap Whitepaper Section 6.3 and 6.4
    # 𝑓𝑟 =𝑓𝑔−𝑓𝑏(𝑖𝑙)−𝑓𝑎(𝑖𝑢)
    # 𝑓𝑢 =𝑙·(𝑓𝑟(𝑡1)−𝑓𝑟(𝑡0))

    # These will be used for both tokens' fee amounts
    tickCurrent = float(position["pool"]["tick"])
    tickLower = float(position["tickLower"]["tickIdx"])
    tickUpper = float(position["tickUpper"]["tickIdx"])

    # Global fee growth per liquidity '𝑓𝑔' for both token 0 and token 1
    feeGrowthGlobal_0 = float(position["pool"]["feeGrowthGlobal0X128"]) / x128
    feeGrowthGlobal_1 = float(position["pool"]["feeGrowthGlobal1X128"]) / x128

    # Fee growth outside '𝑓𝑜' of our lower tick for both token 0 and token 1
    tickLowerFeeGrowthOutside_0 = float(position["tickLower"]["feeGrowthOutside0X128"]) / x128
    tickLowerFeeGrowthOutside_1 = float(position["tickLower"]["feeGrowthOutside1X128"]) / x128

    # Fee growth outside '𝑓𝑜' of our upper tick for both token 0 and token 1
    tickUpperFeeGrowthOutside_0 = float(position["tickUpper"]["feeGrowthOutside0X128"]) / x128
    tickUpperFeeGrowthOutside_1 = float(position["tickUpper"]["feeGrowthOutside1X128"]) / x128

    # These are '𝑓𝑏(𝑖𝑙)' and '𝑓𝑎(𝑖𝑢)' from the formula
    # for both token 0 and token 1
    tickLowerFeeGrowthBelow_0 = 0
    tickLowerFeeGrowthBelow_1 = 0
    tickUpperFeeGrowthAbove_0 = 0
    tickUpperFeeGrowthAbove_1 = 0

    # These are the calculations for '𝑓𝑎(𝑖)' from the formula
    # for both token 0 and token 1
    if (tickCurrent >= tickUpper):
        tickUpperFeeGrowthAbove_0 = feeGrowthGlobal_0 - tickUpperFeeGrowthOutside_0
        tickUpperFeeGrowthAbove_1 = feeGrowthGlobal_1 - tickUpperFeeGrowthOutside_1
    else:
        tickUpperFeeGrowthAbove_0 = tickUpperFeeGrowthOutside_0
        tickUpperFeeGrowthAbove_1 = tickUpperFeeGrowthOutside_1

    # These are the calculations for '𝑓b(𝑖)' from the formula
    # for both token 0 and token 1
    if (tickCurrent >= tickLower):
        tickLowerFeeGrowthBelow_0 = tickLowerFeeGrowthOutside_0
        tickLowerFeeGrowthBelow_1 = tickLowerFeeGrowthOutside_1
    else:
        tickLowerFeeGrowthBelow_0 = feeGrowthGlobal_0 - tickLowerFeeGrowthOutside_0
        tickLowerFeeGrowthBelow_1 = feeGrowthGlobal_1 - tickLowerFeeGrowthOutside_1


    # Calculations for '𝑓𝑟(𝑡1)' part of the '𝑓𝑢 =𝑙·(𝑓𝑟(𝑡1)−𝑓𝑟(𝑡0))' formula
    # for both token 0 and token 1
    fr_t1_0 = feeGrowthGlobal_0 - tickLowerFeeGrowthBelow_0 - tickUpperFeeGrowthAbove_0
    fr_t1_1 = feeGrowthGlobal_1 - tickLowerFeeGrowthBelow_1 - tickUpperFeeGrowthAbove_1

    # '𝑓𝑟(𝑡0)' part of the '𝑓𝑢 =𝑙·(𝑓𝑟(𝑡1)−𝑓𝑟(𝑡0))' formula
    # for both token 0 and token 1
    feeGrowthInsideLast_0 = float(position["feeGrowthInside0LastX128"]) / x128
    feeGrowthInsideLast_1 = float(position["feeGrowthInside1LastX128"]) / x128

    # The final calculations for the '𝑓𝑢 =𝑙·(𝑓𝑟(𝑡1)−𝑓𝑟(𝑡0))' uncollected fees formula
    # for both token 0 and token 1 since we now know everything that is needed to compute it
    uncollectedFees_0 = positionLiquidity * (fr_t1_0 - feeGrowthInsideLast_0)
    uncollectedFees_1 = positionLiquidity * (fr_t1_1 - feeGrowthInsideLast_1)

    # Decimal adjustment to get final results
    uncollectedFeesAdjusted_0 = uncollectedFees_0 / math.pow(10, float(position["token0"]["decimals"]))
    uncollectedFeesAdjusted_1 = uncollectedFees_1 / math.pow(10, float(position["token1"]["decimals"]))


    print(f'priceUpperAdjustedReversed: {priceUpperAdjustedReversed}\n'
          f'priceCurrentAdjustedReversed: {priceCurrentAdjustedReversed}\n'
          f'priceLowerAdjustedReversed: {priceLowerAdjustedReversed}\n'
          f'uncollectedFeesAdjusted_0: {uncollectedFeesAdjusted_0}\n'
          f'uncollectedFeesAdjusted_1: {uncollectedFeesAdjusted_1}')

def sqrtPriceToPriceAdjusted(sqrtPriceX96Prop, decimalDifference):
    sqrtPrice = float(sqrtPriceX96Prop) / x96
    divideBy = math.pow(10, decimalDifference)
    price = math.pow(sqrtPrice, 2) / divideBy

    return price

def sqrtPriceToPrice(sqrtPriceX96Prop):
    sqrtPrice = float(sqrtPriceX96Prop) / x96
    price = math.pow(sqrtPrice, 2)

    return price

# Subgraph query for the position
positionQuery = """
      query tokenPosition {
        position(id: "%1"){
            id
            token0{
                symbol
                derivedETH
                id
                decimals
            }
            token1{
                symbol
                derivedETH
                id
                decimals
            }
            pool{
                id
                liquidity
                sqrtPrice
                tick
                feeGrowthGlobal0X128
                feeGrowthGlobal1X128
            }
            liquidity
            depositedToken0
            depositedToken1
            feeGrowthInside0LastX128
            feeGrowthInside1LastX128
            tickLower {
                tickIdx
                price0
                price1
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            }
            tickUpper {
                tickIdx
                price0
                price1
                feeGrowthOutside0X128
                feeGrowthOutside1X128
            }
            withdrawnToken0
            withdrawnToken1
            collectedFeesToken0
            collectedFeesToken1
            transaction{
                timestamp
                blockNumber
            }
        }
    }"""

getPosition(exampleNFTid)