# Portfolio Performance & Backtesting Guide
**Strategic Overview for Trend Following**

## 1. Key Performance Indicators (KPIs)

### The Sharpe Ratio (Risk-Adjusted Efficiency)
The Sharpe Ratio measures how much excess return you are receiving for the volatility you endure. For a long-term trend follower, this helps distinguish between a lucky streak and a repeatable strategy.

$$Sharpe Ratio = \frac{R_p - R_f}{\sigma_p}$$

* **Target:** A ratio > 1.0 is considered good; > 2.0 is excellent.
* **Focus:** It penalizes "choppy" returns, encouraging a smoother equity curve.

### The Calmar Ratio (The Drawdown Metric)
The Calmar Ratio is often more important for trend followers because it focuses on the **Maximum Drawdown (MDD)** rather than general volatility.

$$Calmar Ratio = \frac{\text{Annual Rate of Return}}{\text{Maximum Drawdown}}$$

* **Application:** If you are holding through pullbacks in AI or Precious Metals, this ratio tells you if the eventual "payoff" justifies the deepest dip your account took along the way.
* **Target:** A Calmar ratio > 2.0 over a long period is exceptional.

---

## 2. Backtesting Framework

To validate a **Buy & Hold Trend Following** strategy, follow this structured workflow using Python.



### Phase A: Data Acquisition
* **Source:** Use `yfinance` to pull historical data.
* **Timeline:** For macro themes (Gold, Copper, Semiconductors), use at least 10 years of data to capture multiple market cycles.

### Phase B: Logic Implementation
* **Indicators:** Apply `SMA 50` and `SMA 200`.
* **Entry:** Golden Cross (50 crosses above 200).
* **Exit:** Death Cross or a specific trailing stop percentage to lock in long-term gains.

### Phase C: Execution & Metrics
* **Tools:** Use `VectorBT` or `Backtrader` for rapid testing.
* **Output:** Calculate the Sharpe and Calmar ratios to compare the strategy's performance against a simple "Buy and Hold" of the S&P 500.

---

## 3. The "Golden Rules" of Testing
1.  **Avoid Over-Optimization:** Do not hunt for "perfect" moving average numbers. If a strategy only works with an SMA 47 but fails with an SMA 50, it is fragile.
2.  **Filter Noise:** Ignore intraday fluctuations. Backtest using **Daily or Weekly closing prices** to align with a long-term perspective.
3.  **Include Costs:** Factor in slippage and minor commission costs to ensure the backtest reflects reality.

---
*Document prepared for Eric Runkel - February 2026*