import pandas as pd
import numpy as np
from statistics import mean
from scipy import stats
import datetime as dt
from dry import sharesToBuy


def value_weighted_by_momentum():
    stocks = pd.read_csv('sp_500_stocks.csv')
    ms_df = pd.read_excel('momentum_strategy.xlsx', engine='openpyxl')
    vs_df = pd.read_excel('value_strategy.xlsx', engine='openpyxl')
    vs_df.set_index('Ticker', inplace=True, drop=True)
    ms_df.set_index('Ticker', inplace=True, drop=True)

    columns = [
        'Ticker',
        'Price',
        'HQM Score',
        'RV Score',
        'HQM by RV Score',
        'HQM by RV Percentile',
        'Number of Shares to Buy',
        'Date of HQM Quote',
        'Date of RV Quote',
        'Date of HQM by RV Quote'
    ]

    vs_by_ms_df = pd.DataFrame(columns=columns)
    vs_by_ms_df.set_index('Ticker', inplace=True)

    for symbol in list(stocks['Ticker']):

        vs_by_ms_df = vs_by_ms_df.append(
            pd.Series(
                [
                    symbol,
                    vs_df.loc[symbol].at['Stock Price'],
                    ms_df.loc[symbol].at['HQM Score'],
                    vs_df.loc[symbol].at['RV Score'],
                    mean([ms_df.loc[symbol].at['HQM Score'], vs_df.loc[symbol].at['RV Score']]),
                    'N/A',
                    0,
                    ms_df.loc[symbol].at['Date of Quote'],
                    vs_df.loc[symbol].at['Date of Quote'],
                    dt.date.today().strftime("%m/%d/%Y")
                ],
                index=columns
            ),
            ignore_index=True
        )
    metrics = {
        'HQM by RV Score': 'HQM by RV Percentile',
    }

    for metric in metrics.keys():
        for row in vs_by_ms_df.index:
            vs_by_ms_df.loc[row, metrics[metric]] = stats.percentileofscore(vs_by_ms_df[metric], vs_by_ms_df.loc[row, metric])/100

    pd.set_option("display.max_rows", 10, "display.max_columns", None)
    vs_by_ms_df.sort_values('HQM by RV Score', inplace=True, ascending=False)
    vs_by_ms_df.reset_index(inplace=True, drop=True)
    vs_by_ms_df = vs_by_ms_df[columns]
    vs_by_ms_df = vs_by_ms_df[:10]
    vs_by_ms_df = sharesToBuy(vs_by_ms_df)
    writer = pd.ExcelWriter('value_by_momentum_strategy.xlsx', engine='xlsxwriter')
    vs_by_ms_df.to_excel(writer, sheet_name='Value by Momentum Strategy', index=False)
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
            'num_format': '0.0%',
            'font_color': font_color,
            'bg_color': background_color,
            'border': 1
        }
    )
    column_formats = {
        'A': ['Ticker', string_format],
        'B': ['Stock Price', dollar_format],
        'C': ['HQM Score', float_format],
        'D': ['RV Score', float_format],
        'E': ['HQM by RV Score', float_format],
        'F': ['HQM by RV Percentile', percent_format],
        'G': ['Number of Shares to Buy', integer_format],
        'H': ['Date of HQM Quote', string_format],
        'I': ['Date of RV Quote', string_format],
        'J': ['Date of HQM by RV Quote', string_format]
    }

    for column in column_formats.keys():
        writer.sheets['Value by Momentum Strategy'].set_column(f'{column}:{column}', 25, column_formats[column][1])
        writer.sheets['Value by Momentum Strategy'].write(f'{column}1', column_formats[column][0], header_format)

    writer.save()