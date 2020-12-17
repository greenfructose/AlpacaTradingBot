import pandas as pd
import openpyxl


def top_buys():
    columns = [
        'Ticker',
        'Number of Shares to Buy'
    ]

    idf = pd.read_excel('value_by_momentum_strategy.xlsx', engine='openpyxl')

    idf = idf[:25]
    idf.to_csv('top-buys.csv', columns=columns, index=False)
