import matplotlib
matplotlib.use('Agg')  # Set the non-interactive backend

import backtrader as bt
import yfinance as yf
import pandas as pd

def backtest_strategy(strategy_class, ticker, start_date, end_date, interval='1d', **strategy_params):
    try:
        cerebro = bt.Cerebro()
        cerebro.addsizer(bt.sizers.PercentSizer, percents=10)

        data = yf.download(ticker, start=start_date, end=end_date, interval=interval)
        if data.empty:
            print(f"No data found for {ticker} from {start_date} to {end_date}.")
            # Return a default Sharpe ratio of 0 if no data
            return None, 0, 0, 100000.0, 100000.0

        # Drop multi-level columns if needed
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.droplevel(1)

        # Determine timeframe (assuming daily since interval='1d')
        data_timeframe = bt.TimeFrame.Days

        data_feed = bt.feeds.PandasData(dataname=data, timeframe=data_timeframe)
        cerebro.adddata(data_feed)

        cerebro.addstrategy(strategy_class, **strategy_params)
        cerebro.broker.setcash(100000.0)

        # Configure Sharpe Ratio analyzer with simple parameters
        # Force it to always produce something:
        # - riskfreerate=0: no risk-free returns needed
        # - annualize=False: no annualization complexity
        # - convertrate=False: no timeframe conversion
        # - factor=1: no scaling
        # If it still fails, we fallback to try/except
        cerebro.addanalyzer(
            bt.analyzers.SharpeRatio,
            _name='sharpe',
            timeframe=data_timeframe,
            riskfreerate=0.0,
            convertrate=False,
            annualize=False,
            factor=1,
            stddev_sample=False
        )

        start_value = cerebro.broker.getvalue()
        print('Starting Portfolio Value: %.2f' % start_value)
        results = cerebro.run()
        final_value = cerebro.broker.getvalue()
        print('Final Portfolio Value: %.2f' % final_value)

        strat = results[0]

        # Safely extract Sharpe ratio
        try:
            sharpe_analysis = strat.analyzers.sharpe.get_analysis()
            sharpe_ratio = sharpe_analysis.get('sharperatio', 0)
        except Exception:
            # If extraction fails, fallback to 0
            sharpe_ratio = 0
        if not sharpe_ratio:
            sharpe_ratio = 0

        # If still no trades or no returns, sharpe_ratio might be meaningless
        # but we already defaulted it to 0
        print(f'Sharpe Ratio: {sharpe_ratio}')

        # Try plotting, fallback if it fails
        try:
            figs = cerebro.plot(returnfig=True, iplot=False, numfigs=1, plotdist=0.1,
                                subtxtsize=8, style='candle', volpushup=0.2, hlineswidth=0.7)
            fig = figs[0][0] if figs else None
        except Exception as plot_ex:
            print(f"Plotting failed: {plot_ex}")
            fig = None

        # Get number of trades if defined
        trades_completed = getattr(strat, 'num_trades', 0)

        return fig, sharpe_ratio, trades_completed, start_value, final_value
    except Exception as e:
        print(f"An error occurred: {e}")
        # Return defaults if something catastrophic happens
        return None, 0, 0, 100000.0, 100000.0