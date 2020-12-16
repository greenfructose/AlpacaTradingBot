import alpaca_trade_api as tradeapi
import csv
import secret as s

api = tradeapi.REST(
    s.ALPACA_API_KEY,
    s.ALPACA_SECRET_KEY,
    s.ALPACA_BASE_URL
)
account = api.get_account()

# Check if our account is restricted from trading.
if account.trading_blocked:
    print('Account is currently restricted from trading.')

# Check our current balance vs. our balance at the last market close
balance_change = float(account.equity) - float(account.last_equity)
print(f'Today\'s portfolio balance change: ${balance_change}')

with open('top-buys.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        api.submit_order(row['ï»¿Ticker'], int(row['Number of Shares to Buy']), 'buy', 'market', 'day')
        print(row['ï»¿Ticker'])
        print(row['Number of Shares to Buy'])

# Check how much money we can use to open new positions.
print(f'${account.buying_power} is available as buying power.')

# Get a list of all active assets.
positions = api.list_positions()
print(f'Below are current positions:\n{positions}')
