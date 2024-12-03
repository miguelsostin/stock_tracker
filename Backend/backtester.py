import matplotlib
from matplotlib import matplotlib_fname

matplotlib.use('Agg')  # Set the non-interactive backend before any other imports

import backtrader as bt

import yfinance as yf
import pandas as pd
import io

def backtest_strategy(strategy_class, ticker, start_date, end_date, interval='1d', **strategy_params):
    # Initialize Cerebro
    try:
        cerebro = bt.Cerebro()

        # Download data from Yahoo Finance
        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)

        if data.empty:
            print(f"No data found for {ticker} from {start_date} to {end_date}.")
            return

        # Ensure correct column names
        data.columns = data.columns.droplevel(1)

        # Create a Data Feed
        data_feed = bt.feeds.PandasData(dataname=data)

        # Add the data feed to Cerebro
        cerebro.adddata(data_feed)

        # Add strategy to Cerebro
        cerebro.addstrategy(strategy_class, **strategy_params)

        # Set initial cash
        cerebro.broker.setcash(100000.0)

        ## _plotskip = False for lines


        # Add analyzers if needed (e.g., Sharpe Ratio)
        cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')

        # Run the backtest
        start_value = cerebro.broker.getvalue()
        print('Starting Portfolio Value: %.2f' % start_value)
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        print('Final Portfolio Value: %.2f' % final_value)

        # Get analyzers data
        strat = results[0]
        print(strat)
        trades_completed = strat.num_trades
        sharpe_ratio = strat.analyzers.sharpe.get_analysis().get('sharperatio', None)
        print(f'Sharpe Ratio: {sharpe_ratio}')

        # Plot the results
        figs = cerebro.plot(returnfig = True, iplot = False, numfigs = 1, plotdist = 0.1, subtxtsize = 8, style = 'candle', volpushup = 0.2, hlineswidth = 0.7)
        fig = figs[0][0]
        return fig, sharpe_ratio, trades_completed, start_value, final_value
    except Exception as e:
        print(f"An error occurred: {e}")
        return


