
def fee_token(pool, token, liquidity, decimals, ticks_dict):
    # Repasar y comparar lógica del fuera de rango con white paper

    # Replacement
    token = "0" if token == "token0" else "1"

    # Variables
    # https://ethereum.stackexchange.com/questions/101955/trying-to-make-sense-of-uniswap-v3-fees-feegrowthinside0lastx128-feegrowthglob
    x128 = 2**128
    fg = float(pool["pool"][f"feeGrowthGlobal{token}X128"])/x128  # Section 6.2.2 wp
    fo_b = float(pool["tickLower"][f"feeGrowthOutside{token}X128"])/x128  # Table 2 and below. Fee below the tick. wp
    fo_a = float(pool["tickUpper"][f"feeGrowthOutside{token}X128"])/x128  # Table 2 and below. Fee above the tick. wp
    fr_t0 = float(pool[f"feeGrowthInside{token}LastX128"]) / x128  # Table 3 wp

    # Conditions
    under_range = ticks_dict["current"] < ticks_dict["lower"] < ticks_dict["upper"]
    in_range = ticks_dict["lower"] <= ticks_dict["current"] < ticks_dict["upper"]
    # over_range = ticks_dict["lower"] < ticks_dict["upper"] < ticks_dict["current"]

    # https://github.com/code-423n4/2021-09-sushitrident-2-findings/issues/1
    # wp, https://uniswap.org/whitepaper-v3.pdf
    if under_range:
        fa = fo_a  # 6.17, bottom case
        fb = fg - fo_b  # 6.18, bottom case
    elif in_range:
        fa = fo_a  # 6.17, bottom case
        fb = fo_b  # 6.18, top case
    else:
        fa = fg - fo_a  # 6.17, top case
        fb = fo_b  # 6.18, top case

    # 6.19 in wp
    fr_t1 = fg - fb - fa

    # 6.28 in wp
    fu = liquidity * (fr_t1 - fr_t0)

    # Encontrar una pool con fees collected en pool[f"collectedFees{token}]
    feetoken = fu / (10 ** decimals)
    return feetoken
