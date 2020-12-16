import numpy as np
import pandas as pd
import requests
from scipy import stats
from statistics import mean
import xlsxwriter
import datetime as dt
from secret import IEX_CLOUD_API_TOKEN
from dry import symbolStrings


def robust_value():
    stocks = pd.read_csv('sp_500_stocks.csv')
    symbol_strings = symbolStrings(stocks)
    columns = [
        'Ticker',
        'Stock Price',
        'Price-to-Earnings Ratio',
        'PE Percentile',
        'Price-to-Book Ratio',
        'PB Percentile',
        'Price-to-Sales Ratio',
        'PS Percentile',
        'Enterprise-Value/EBITDA',
        'EV/EBITDA Percentile',
        'Enterprise-Value/Gross-Profit',
        'EV/GP Percentile',
        'RV Score',
        'Number of Shares to Buy',
        'Date of Quote'
    ]
    numeric_data_columns = [
        'Price-to-Earnings Ratio',
        'Price-to-Book Ratio',
        'Price-to-Sales Ratio',
        'Enterprise-Value/EBITDA',
        'Enterprise-Value/Gross-Profit',
    ]
    missing_data = []
    df = pd.DataFrame(columns=columns)
    for symbol_string in symbol_strings:
        batch_call_url = f'https://cloud.iexapis.com/stable/stock/market/batch/?types=quote,advanced-stats&symbols={symbol_string}&token={IEX_CLOUD_API_TOKEN}'
        data = requests.get(batch_call_url).json()
        for symbol in symbol_string.split(','):
            enterprise_value = data[symbol]['advanced-stats']['enterpriseValue']
            ebitda = data[symbol]['advanced-stats']['EBITDA']
            gross_profit = data[symbol]['advanced-stats']['grossProfit']
            try:
                ev_to_ebitda = enterprise_value / ebitda
            except TypeError:
                ev_to_ebitda = np.NaN
                missing_data.append(
                    {
                        'stock': symbol,
                        'missing_data': 'ev_to_ebitda'
                    }
                )
            try:
                ev_to_gp = enterprise_value / gross_profit
            except TypeError:
                ev_to_gp = np.NaN
                missing_data.append(
                    {
                        'stock': symbol,
                        'missing_data': 'ev_to_gp'
                    }
                )
            df = df.append(
                pd.Series(
                    [
                        symbol,
                        data[symbol]['quote']['latestPrice'],
                        data[symbol]['quote']['peRatio'],
                        'N/A',
                        data[symbol]['advanced-stats']['priceToBook'],
                        'N/A',
                        data[symbol]['advanced-stats']['priceToSales'],
                        'N/A',
                        ev_to_ebitda,
                        'N/A',
                        ev_to_gp,
                        'N/A',
                        'N/A',
                        0,
                        dt.date.today().strftime("%m/%d/%Y")
                    ],
                    index=columns
                ),
                ignore_index=True
            )

    for column in numeric_data_columns:
        df[column].fillna(df[column].mean(), inplace=True)

    metrics = {
        'Price-to-Earnings Ratio': 'PE Percentile',
        'Price-to-Book Ratio': 'PB Percentile',
        'Price-to-Sales Ratio': 'PS Percentile',
        'Enterprise-Value/EBITDA': 'EV/EBITDA Percentile',
        'Enterprise-Value/Gross-Profit': 'EV/GP Percentile'
    }

    for metric in metrics.keys():
        for row in df.index:
            df.loc[row, metrics[metric]] = stats.percentileofscore(df[metric], df.loc[row, metric]) / 100

    for row in df.index:
        value_percentiles = []
        for metric in metrics.keys():
            value_percentiles.append(df.loc[row, metrics[metric]])
        df.loc[row, 'RV Score'] = mean(value_percentiles)

    pd.set_option("display.max_rows", None, "display.max_columns", None)
    df.sort_values('RV Score', inplace=True, ascending=False)
    df.reset_index(inplace=True, drop=True)

    writer = pd.ExcelWriter('value_strategy.xlsx', engine='xlsxwriter')
    df.to_excel(writer, sheet_name='Value Strategy', index=False)
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
    float_format = writer.book.add_format(
        {
            'num_format': '0.00',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    percent_format = writer.book.add_format(
        {
            'num_format': '0.00%',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    column_formats = {
        'A': ['Ticker', string_format],
        'B': ['Stock Price', dollar_format],
        'C': ['Price-to-Earnings Ratio', float_format],
        'D': ['PE Percentile', percent_format],
        'E': ['Price-to-Book Ratio', float_format],
        'F': ['PB Percentile', percent_format],
        'G': ['Price-to-Sales Ratio', float_format],
        'H': ['PS Percentile', percent_format],
        'I': ['Enterprise-Value/EBITDA', float_format],
        'J': ['EV/EBITDA Percentile', percent_format],
        'K': ['Enterprise-Value/Gross-Profit', float_format],
        'L': ['EV/GP Percentile', integer_format],
        'M': ['RV Score', float_format],
        'N': ['Number of Shares to Buy', integer_format],
        'O': ['Date of Quote', string_format]
    }

    for column in column_formats.keys():
        writer.sheets['Value Strategy'].set_column(f'{column}:{column}', 25, column_formats[column][1])
        writer.sheets['Value Strategy'].write(f'{column}1', column_formats[column][0], header_format)

    writer.save()
    bad_data = []
    for item in missing_data:
        if item['stock'] not in bad_data:
            bad_data.append(item['stock'])
            print(f"Missing data {item['missing_data']} for stock {item['stock']}, filling in with mean")
    print('The following stocks had bad data: \n' + ', '.join(bad_data))
