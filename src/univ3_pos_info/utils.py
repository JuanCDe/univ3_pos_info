import math

def human_readable(x):
    #Quantities for humans
    # x = round(num, 3)
    # x = pd.to_numeric(x)
    try:
        zeros = int(math.log10(x))
        if 3 <= zeros < 6:
            return f"{round(x/1e3, 2)}K"
        elif 6 <= zeros < 9:
            return f"{round(x/1e6, 2)}M"
        elif zeros >= 9:
            return f"{round(x/1e9, 2)}B"
        else:
            return f"{round(x, 6)}"
    except ValueError:
        return f'0'