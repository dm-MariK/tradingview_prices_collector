# config.py
# ---------

# --- DataFrame Columns' Names ---
# Expected Columns' Names for the input and output files, respectively:
# "Currency","Symbol","Where","Amount","Initial Price"
# "Currency","Symbol","Where","Amount","Initial Price","Current Price","Percentage Change (%)","Performance Stars",|"Value","Current % portfolio","PnL"

# Define the expected column names in the input file
# (will be copied to the output file as is)
CURRENCY_COL = 'Currency'
SYMBOL_COL = 'Symbol'
WHERE_COL = 'Where'
AMOUNT_COL = 'Amount'
INIT_PRICE_COL = 'Initial Price'
# Define the column names to be added to the output file
CURRENT_PRICE_COL = 'Current Price'
PERCENT_CHANGE_COL = 'Percentage Change (%)'
STARS_COL = 'Performance Stars'
#|The following columns will be added only if AMOUNT_COL is present in the input file
VALUE_COL = 'Value'
PERCENT_PORTFOLIO_COL = 'Current % portfolio'
PNL_COL = 'PnL'
# -------------------------------------------------------------------------------------------------

# --- Master List of Screener Constants (These must match the variable names below) ---
PREFIXES = [
    'CRYPTO_PREFIXES' #, 
    #'AMERICA_PREFIXES', 
    #'EUROPE_PREFIXES'  # Example of another screener category
]

# --- Screener-Specific Symbol Prefixes ---
# The keys used here will be used in the SCREENS dict (e.g., 'crypto', 'america').
# NOTE: The variable names must exactly match the strings in the PREFIXES list above.
# NOTE #2: Using the colon as the prefix name terminator, as in 'BINANCE:', provides a clean and 
# unambiguous delimiter because TradingView symbols generally follow the pattern: 
#           'SCRENER_PREFIX:TICKER' (for example, 'BINANCE:BTCUSDT').
# TradingView Screener: 'crypto'
CRYPTO_PREFIXES = {
    'screener_name': 'crypto',
    'prefixes': ['BYBIT:', 'BINANCE:', 'KUCOIN:', 'OKX:', 'MEXC:', 'HTX:']
}

# TradingView Screener: 'america'
#AMERICA_PREFIXES = {
    #'screener_name': 'america',
    #'prefixes': ['NASDAQ:', 'NYSE:', 'AMEX:']
#}

# TradingView Screener: 'europe' (Example)
#EUROPE_PREFIXES = {
    #'screener_name': 'europe',
    #'prefixes': ['LSE:', 'FWB:', 'EPA:']
#}
