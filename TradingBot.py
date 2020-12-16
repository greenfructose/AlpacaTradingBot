import alpaca_trade_api as tradeapi
import csv
import secret as s
import hq_quantitative_momentum as hqm
import robust_value as rv
import value_weighted_by_momentum as vwm


api = tradeapi.REST(
    s.ALPACA_API_KEY,
    s.ALPACA_SECRET_KEY,
    s.ALPACA_BASE_URL
)
account = api.get_account()


def order_buy():
    with open('top-buys.csv', 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            api.submit_order(row['ï»¿Ticker'], int(row['Number of Shares to Buy']), 'buy', 'market', 'day')
            print(row['ï»¿Ticker'])
            print(row['Number of Shares to Buy'])


def take_profit():
    profit = 0.0
    for position in positions:
        if float(position.unrealized_plpc) > 10.0:
            print(f'{position.symbol} has gained {position.unrealized_plpc}% Taking profit.')
            profit = profit + float(position.unrealized_pl)
            api.close_position(position.symbol)
            print(f'Profit taken: ${profit}')


def stop_loss():
    loss = 0.0
    for position in positions:
        if float(position.unrealized_plpc) < -1.5:
            print(f'{position.symbol} has lost {position.unrealized_plpc}%. Initiating stoploss.')
            loss = loss + float(position.unrealized_pl)
            api.close_position(position.symbol)
            print(f'Loss taken: {loss}')


# Check if our account is restricted from trading.
if account.trading_blocked:
    print('Account is currently restricted from trading.')

# Check our current balance vs. our balance at the last market close
balance_change = float(account.equity) - float(account.last_equity)
print(f'Today\'s portfolio balance change: ${balance_change}')

# Check how much money we can use to open new positions.
print(f'${account.buying_power} is available as buying power.')

# Get a list of all active assets.
positions = api.list_positions()
print(f'Below are current positions:\n{positions}')

# Get current scores and evaluate number of shares to buy.
# below are commented out for testing
# rv.robust_value()
# hqm.hq_quantitative_momentum()
vwm.value_weighted_by_momentum(int(float(account.buying_power)))
