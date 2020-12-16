import numpy as np
import pandas as pd
import requests
from scipy import stats
from statistics import mean
import xlsxwriter
import datetime as dt
from secret import IEX_CLOUD_API_TOKEN
from dry import symbolStrings


def hq_quantitative_momentum():
    stocks = pd.read_csv('sp_500_stocks.csv')
    symbol_strings = symbolStrings(stocks)
    columns = [
        'Ticker',
        'Stock Price',
        'One-Year Return',
        'One-Year Return Percentile',
        'Six-Month Return',
        'Six-Month Return Percentile',
        'Three-Month Return',
        'Three-Month Return Percentile',
        'One-Month Return',
        'One-Month Return Percentile',
        'HQM Score',
        'Number of Shares to Buy',
        'Date of Quote'
    ]
    time_periods = [
        'One-Year',
        'Six-Month',
        'Three-Month',
        'One-Month'
    ]
    df = pd.DataFrame(columns=columns)
    for symbol_string in symbol_strings:
        batch_call_url = f'https://cloud.iexapis.com/stable/stock/market/batch?symbols={symbol_string}&types=price,' \
                         f'stats&token={IEX_CLOUD_API_TOKEN}'
        data = requests.get(batch_call_url).json()
        for symbol in symbol_string.split(','):
            df = df.append(
                pd.Series(
                    [
                        symbol,
                        data[symbol]['price'],
                        data[symbol]['stats']['year1ChangePercent'],
                        'N/A',
                        data[symbol]['stats']['month6ChangePercent'],
                        'N/A',
                        data[symbol]['stats']['month3ChangePercent'],
                        'N/A',
                        data[symbol]['stats']['month1ChangePercent'],
                        'N/A',
                        'N/A',
                        0,
                        dt.date.today().strftime("%m/%d/%Y")
                    ],
                    index=columns
                ),
                ignore_index=True
            )
    for row in df.index:
        for time_period in time_periods:
            if df.loc[row, f'{time_period} Return'] is None:
                df.loc[row, f'{time_period} Return'] = float(0)
    for row in df.index:
        for time_period in time_periods:
            df.loc[row, f'{time_period} Return Percentile'] = stats.percentileofscore(df[f'{time_period} Return'], float(
                df.loc[row, f'{time_period} Return']))/100
    for row in df.index:
        momentum_percentiles = []
        for time_period in time_periods:
            momentum_percentiles.append(df.loc[row, f'{time_period} Return Percentile'])
        df.loc[row, 'HQM Score'] = mean(momentum_percentiles)

    pd.set_option("display.max_rows", None, "display.max_columns", None)
    df.sort_values('HQM Score', ascending=False, inplace=True)
    df.reset_index(inplace=True, drop=True)

    writer = pd.ExcelWriter('momentum_strategy.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Momentum Strategy', index=False)
    background_color = '#0a0a23'
    font_color = '#ffffff'
    header_format = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': '#15154B',
            'border': 1,
            'align': 'center',
            'bold': True
        }
    )
    string_format = writer.book.add_format(
        {
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    dollar_format = writer.book.add_format(
        {
            'num_format': '$0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    integer_format = writer.book.add_format(
        {
            'num_format': '0',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    percent_format = writer.book.add_format(
        {
            'num_format': '0.0%',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    column_formats = {
        'A': ['Ticker', string_format],
        'B': ['Stock Price', dollar_format],
        'C': ['One-Year Return', percent_format],
        'D': ['One-Year Return Percentile', percent_format],
        'E': ['Six-Month Return', percent_format],
        'F': ['Six-Month Return Percentile', percent_format],
        'G': ['Three-Month Return', percent_format],
        'H': ['Three-Month Return Percentile', percent_format],
        'I': ['One-Month Return', percent_format],
        'J': ['One-Month Return Percentile', percent_format],
        'K': ['HQM Score', percent_format],
        'L': ['Number of Shares to Buy', integer_format],
        'M': ['Date of Quote', string_format]
    }

    for column in column_formats.keys():
        writer.sheets['Momentum Strategy'].set_column(f'{column}:{column}', 25, column_formats[column][1])
        writer.sheets['Momentum Strategy'].write(f'{column}1', column_formats[column][0], header_format)

    writer.save()
