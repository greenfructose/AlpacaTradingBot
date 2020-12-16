import math


def chunks(lst, n):
    """Yield successive n-sized chunks from list"""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def symbolStrings(stocks):
    symbol_groups = list(chunks(stocks['Ticker'], 100))
    symbol_strings = []
    for i in range(0, len(symbol_groups)):
        symbol_strings.append(','.join(symbol_groups[i]))
    return symbol_strings


def sharesToBuy(df):
    portfolio_size = input('Enter the value of your portfolio:')
    try:
        val = float(portfolio_size)
    except ValueError:
        print('Please enter a number')
        portfolio_size = input('Enter the value of your portfolio:')
        val = float(portfolio_size)

    position_size = val / len(df.index)
    for i in range(0, len(df.index)):
        df.loc[i, 'Number of Shares to Buy'] = math.floor(position_size / df.loc[i, 'Price'])
    return df
