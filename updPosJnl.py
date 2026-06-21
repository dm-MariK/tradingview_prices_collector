#!/usr/bin/env python3
# updPosJnl.py
# --------------------
# Requirements:
# pip install tradingview-ta pandas
#
# Usage with conda:
# 1. Create a new environment named 'trading_env' with Python 3.11
#conda create -n tradingview_env python=3.11
# 2. Activate the new environment
#conda activate tradingview_env
# 3. Install the required libraries within this environment
#pip install pandas tradingview-ta
# -------------------------------------------------------------------------
# Developed by dm_MariK with a help of Gemini (AI by Google).

import argparse
#import sys
import pandas as pd
from tradingview_ta import get_multiple_analysis, Interval
import time
import numpy as np

# --- Configuration ---
import config # Import the config.py file
# Using a short interval for a price close to real-time.
TIME_INTERVAL = Interval.INTERVAL_1_MINUTE 

# --- Prepare the scripts' arguments parser --- ------------------------------------------------
def get_args():
    """Parses command-line arguments for input and output file names."""
    parser = argparse.ArgumentParser(
        description="Fetches current Trading View prices for symbols in a CSV file and calculates performance (percentage of profit or loss)."
    )
    
    # Input File: Positional Argument (sys.argv[1] equivalent)
    parser.add_argument(
        'input_file',
        type=str,
        help='The path to the input CSV file containing Symbol and Initial Price.'
    )
    
    # Output File: Positional Argument (sys.argv[2] equivalent)
    parser.add_argument(
        'output_file',
        type=str,
        help='The path to the output CSV file for the performance report.'
    )
    
    # This automatically reads from sys.argv and returns the arguments as an object
    return parser.parse_args()

# --- Function to Get Prices --- ---------------------------------------------------------------
def get_current_prices(symbol_df):
    """
    Fetches the latest close price for symbols in the DataFrame.
    """
    symbol_list = symbol_df[config.SYMBOL_COL].str.upper().tolist() #config.SYMBOL_COL='Symbol'
    results_data = []
    
    # 1. Dynamically build the SCREENS dictionary
    SCREENS = {}
    
    # Track symbols that have been categorized so we can find the remainder
    categorized_symbols = set()

    for prefix_const_name in config.PREFIXES:
        
        # Use getattr() to fetch the dictionary associated with the constant name
        # e.g., config.CRYPTO_PREFIXES
        screener_data = getattr(config, prefix_const_name)
        
        screener_name = screener_data['screener_name']
        prefixes = screener_data['prefixes']
        
        # Use list comprehension and the 'any' check to categorize symbols
        current_screener_symbols = [
            s for s in symbol_list 
            if any(prefix in s for prefix in prefixes) and s not in categorized_symbols
        ]
        
        if current_screener_symbols:
            # Add to the SCREENS dict
            SCREENS[screener_name] = current_screener_symbols
            # Update the set of categorized symbols
            categorized_symbols.update(current_screener_symbols)

    # 2. Identify and report the uncategorized symbols (good for robustness)
    uncategorized_symbols = [s for s in symbol_list if s not in categorized_symbols]
    if uncategorized_symbols:
        # --- REPORTING LOGIC ---
        print("\n" + "="*50)
        print(f"⚠️ **Warning: {len(uncategorized_symbols)} Symbols Were Uncategorized.**")
        print("These symbols did not match any defined prefix and will be skipped.")
        print("Please check your input file or update the prefixes in 'config.py'.")
        print("-" * 50)
        
        # Print the full list of symbols to stdout
        for symbol in uncategorized_symbols:
            print(f"  - {symbol}")
            
        print("="*50 + "\n")
        
    # 3. Fetch data by iterating over the SCREENS dict
    for screener, symbols in SCREENS.items():
        if not symbols:
            continue
            
        print(f"Fetching {len(symbols)} symbols from screener: {screener}...")
        
        # get_multiple_analysis retrieves the data
        analysis = get_multiple_analysis(
            screener=screener, 
            interval=TIME_INTERVAL, 
            symbols=symbols,
            timeout=10 # Set a timeout for a faster response
        )
        
        for symbol, analysis_obj in analysis.items():
            current_price = None
            if analysis_obj and analysis_obj.indicators:
                # The 'close' indicator holds the latest closing price of the current bar
                current_price = analysis_obj.indicators.get('close')
            
            results_data.append({
                config.SYMBOL_COL: symbol,               # config.SYMBOL_COL='Symbol'
                config.CURRENT_PRICE_COL: current_price, # config.CURRENT_PRICE_COL='Current Price'
            })
            
        # Wait briefly to avoid overloading the service
        time.sleep(1) 
        
    # price_df now has the uniform format required for the merge
    return pd.DataFrame(results_data)

# --- Calculation Function --- -----------------------------------------------------------------
def calculate_performance(df):
    """
    Calculates percentage change and applies the star-rating system.
    """
    # 1. Calculate Percentage Change
    df[config.PERCENT_CHANGE_COL] = (
        ( (df[config.CURRENT_PRICE_COL] - df[config.INIT_PRICE_COL]) / df[config.INIT_PRICE_COL]
        ) * 100
    ).round(2)
    
    # Handle division by zero or NaN values gracefully
    df[config.PERCENT_CHANGE_COL] = df[config.PERCENT_CHANGE_COL].replace([np.inf, -np.inf], np.nan)
    
    # 2. Apply the Star Rating System
    def apply_stars(percent_change):
        if pd.isna(percent_change):
            return ""
        
        if percent_change >= 200:
            return '***'
        elif percent_change >= 100:
            return '**'
        elif percent_change > 0:
            return '*'
        else:
            return '' # Empty string if percentage is zero or negative
    
    df['Performance Stars'] = df[config.PERCENT_CHANGE_COL].apply(apply_stars)
    
    # 3. Calculate "Value", "Current % portfolio" and "PnL"
    if config.AMOUNT_COL in df.columns: 
        # "Value"
        df[config.VALUE_COL] = df[config.AMOUNT_COL] * df[config.CURRENT_PRICE_COL]
        total_value = df[config.VALUE_COL].sum()
        # "Current % portfolio"
        df[config.PERCENT_PORTFOLIO_COL] = (df[config.VALUE_COL] / total_value) * 100
        # "PnL"
        df[config.PNL_COL] = ( 
            df[config.CURRENT_PRICE_COL] - df[config.INIT_PRICE_COL]
        ) * df[config.AMOUNT_COL]
        total_pnl = df[config.PNL_COL].sum()
        
        # Append the Summary ('TOTAL') row
        # * append one penultimate empty row (filled by "", not None or NaN)
        empty_row = [""] * len(df.columns)
        df.loc[len(df)] = empty_row
        
        # * append the 'TOTAL' row
        # Prepare dict to append to pd table, fill it with "" str lines:
        total_row = {col: "" for col in df.columns}
        # Update values of required cells:
        total_row[config.CURRENCY_COL] = 'TOTAL'
        total_row[config.VALUE_COL] = total_value
        total_row[config.PNL_COL] = total_pnl
        
        # Concatenate the 'TOTAL' row with `pd`. `ignore_index=True` resets the indexes 
        # so that there will not be any duplicates (such as multiple rows with index 0) and 
        # the numeration in the resulting table will be sequential.
        df = pd.concat([df, pd.DataFrame([total_row])], ignore_index=True)
        
    return df

# --- Main logic --- ---------------------------------------------------------------------------
def main(input_file, output_file):
    """The main logic of the script."""
    try:
        # 1. Read the input file
        print(f"Reading symbols and initial prices from {input_file}...")
        
        # 1. Read the input file
        # We read all columns, regardless of their order/number
        input_df = pd.read_csv(input_file)
        
        # Check if the required columns exist
        if (
            config.CURRENCY_COL not in input_df.columns 
            or config.SYMBOL_COL not in input_df.columns 
            or config.INIT_PRICE_COL not in input_df.columns
        ):
            #print(f"❌ Error: Input file must contain columns named '{config.SYMBOL_COL}' and '{config.INIT_PRICE_COL}'.")
            print(
                f"❌ Error: Input file must contain columns named:\n"
                f"      \"{config.CURRENCY_COL}\"\n"
                f"      \"{config.SYMBOL_COL}\"\n"
                f"      \"{config.INIT_PRICE_COL}\""
            )
            return

        # Ensure symbol is uppercase for consistent matching
        input_df[config.SYMBOL_COL] = input_df[config.SYMBOL_COL].str.upper()
    
        # Select only the required (fot t-vw request) columns and save them to the request_df
        request_df = input_df[[config.SYMBOL_COL, config.INIT_PRICE_COL]].copy()
        
#        # Rename the columns just in case you had different input names 
#        #input_df.columns = [config.OUTPUT_SYMBOL_COL, config.OUTPUT_INIT_PRICE_COL]
        
        
        # 2. Get the current prices from the tradingview
        price_df = get_current_prices(request_df)
        
        # Merge it with the original data. 
        # Ensure all initial data will be preserved and updated correctly, if required.
        # * A. remember the initial columns order
        column_order_list = list(input_df.columns)
        
        # * B. append "Current Price" to the list if it was absent
        if config.CURRENT_PRICE_COL not in column_order_list:
            column_order_list.append(config.CURRENT_PRICE_COL)
        
        # * C. Perform `merge`, removing old `CURRENT_PRICE_COL` and 
        # * selecting the only columns from the `price_df` that are really required.
        merged_df = (
            input_df
            .drop(columns=[config.CURRENT_PRICE_COL], errors='ignore')
            .merge(
                price_df[[config.SYMBOL_COL, config.CURRENT_PRICE_COL]], 
                on=config.SYMBOL_COL, # Aligns on the "Symbol" key
                how='left' # Keeps all rows from the original input_df
            )
        )
        
        # * D. rearrange columns to their original order
        merged_df = merged_df[column_order_list]
        
#        merged_df = input_df.merge(
#            price_df[[config.SYMBOL_COL, config.CURRENT_PRICE_COL]], 
#            on=config.SYMBOL_COL, # Aligns on the Symbol key # config.OUTPUT_SYMBOL_COL = 'Symbol'
#            how='left'            # Keeps all rows from the original input_df
#        )
            
        # 3. Perform calculations
        final_df = calculate_performance(merged_df)
        
#        # 4. Define and save the final output
#        output_columns = [
#            config.OUTPUT_SYMBOL_COL,     # config.OUTPUT_SYMBOL_COL = 'Symbol'
#            config.OUTPUT_INIT_PRICE_COL, # config.OUTPUT_INIT_PRICE_COL = 'Initial Price'
#            config.CURRENT_PRICE_COL,     # config.CURRENT_PRICE_COL='Current Price'
#            config.PERCENT_CHANGE_COL,    # config.PERCENT_CHANGE_COL = 'Percentage Change (%)'
#            'Performance Stars'
#        ]
#        final_df[output_columns].to_csv(output_file, index=False)
        
        # 4. Save the data table to csv 
        final_df.to_csv(output_file, index=False, na_rep='NaN')
        
        print(f"\n✅ Successfully created performance report for {len(final_df)} symbols.")
        print(f"Report saved to {output_file}")
            
    except FileNotFoundError:
        print(f"❌ Error: Input file '{input_file}' not found.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        
# --- Main Execution ---
if __name__ == "__main__":
    # Parse arguments first
    args = get_args()
    
    # Call the main logic with the parsed file paths
    main(args.input_file, args.output_file)
    
