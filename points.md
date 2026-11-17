You are overcomplicating the explanation. You do not need to explain the entire technical architecture. You need to explain what problem the project solves, how it processes the data, and what useful information it produces.

Think of it as a five-step story. Follow the flowchart from top to bottom.

## Your 2-minute project explanation

1\. Start with the problem.

"Gold and silver ETFs trade on the stock exchange, just like shares. However, their exchange market price can sometimes move significantly above or below the actual value of their underlying holdings, which is represented by their NAV.

Normally, market makers and arbitrage mechanisms help keep these prices close. But during periods of extreme volatility, liquidity constraints or disruptions in the underlying market, this mechanism may not work efficiently. This can result in unusually large premiums or discounts.

My project aims to identify these situations early, specifically for gold and silver ETFs."

2\. Explain the data sources.

"To do this, I collect historical daily data from four main categories. NSE and BSE provide ETF trading data, including closing prices, volumes and turnover. AMFI provides official daily NAV data. Global gold and silver prices, along with USD-INR exchange rates, help capture movements in the underlying assets. Finally, I collect ETF-specific information, peer ETF data and relevant market events."

3\. Explain what happens to the data. This is the important transition.

"Once the data is collected and cleaned, I calculate the premium or discount for each ETF by comparing its exchange closing price with its official NAV.

I then engineer approximately 35–45 features from this information. These are essentially financial indicators that help describe the ETF's behaviour.

For example, I look at whether its premium has been increasing, whether trading volume has suddenly surged, whether the underlying gold or silver price has become unusually volatile, and whether other ETFs tracking the same metal are experiencing similar behaviour.

So instead of simply looking at today's premium, the system considers multiple signals together to understand whether the ETF might be approaching an unusual pricing situation."

4\. Explain the AI/ML component.

"This information is fed into a machine-learning model called LightGBM, which learns patterns from historical ETF behaviour.

The model produces two complementary predictions.

The first is a forecast of tomorrow's premium or discount, including an expected range. Essentially, it tells us how far above or below NAV the ETF might trade.

The second is a tail-risk probability. It estimates the likelihood that tomorrow's premium will move unusually far away from that ETF's own recent normal behaviour.

These are two different things: one tells us the expected pricing level, while the other tells us whether there is an unusually high risk of a dislocation."

5\. Explain what the output actually means to Mirae Asset.

"The final output is a daily risk-monitoring dashboard for gold and silver ETFs. It displays the predicted premium range, the probability of an unusual deviation, and the factors contributing to that prediction.

For example, it might flag an ETF as high risk because its premium is rising, trading activity has increased sharply, and other ETFs tracking the same metal are showing similar deviations.

The idea is to give the ETF sales team earlier visibility into potentially abnormal pricing conditions, so they can have more informed conversations with distributors and investors."

## The one thing you absolutely must understand

There are two predictions. Do not confuse them when explaining the project.

Imagine an ETF has historically traded at a premium of around 1%.

Tomorrow, your model produces these results:

Output A — Expected premium range

# +1.5% to +2.5%

The model expects the ETF to trade at a premium within this range tomorrow.

Output B — Probability of unusual deviation

# 68%

High risk

The model estimates a 68% probability that tomorrow's premium will deviate unusually far from its own recent normal.

Output A tells you where the premium might be. Output B tells you whether there is a heightened risk of abnormal behaviour.

That distinction is central to your project.

## If he asks: "So what exactly is the AI doing?"

Say this:

"The AI is learning relationships between historical market conditions and subsequent ETF premium movements. For example, it might learn that a combination of rising premiums, unusual trading activity, high underlying metal volatility and divergence across peer ETFs has historically preceded pricing dislocations. It uses these relationships to estimate tomorrow's premium range and the probability of an unusual deviation."

## If he asks: "How do you know whether your model actually works?"

Say:

"I use historical walk-forward backtesting. Essentially, I train the model on past data and test it on subsequent periods that it has never seen. I also specifically examine historical stress events, particularly the October 2025 silver ETF premium episode and the January–February 2026 precious-metal market crash. I compare the model against simpler statistical baselines to establish whether machine learning actually adds predictive value."

## Finally, remember these three things

1. You are not predicting whether gold or silver prices will rise or fall. You are predicting unusual pricing behaviour in ETFs relative to their NAV.
2. You are not building a trading bot. This is an early-warning and risk-monitoring system, not an investment recommendation.
3. You are not claiming to eliminate premiums or guarantee predictions. You are trying to identify potential dislocations earlier and provide evidence explaining why the system raised a warning.

There are two separate concepts here: the median forecast and the 90% prediction interval. I'll explain them using an example of a hypothetical Mirae Silver ETF.

## 1. What does "Median forecast: +2.7%" actually mean?

First, remember what the model is predicting: tomorrow's premium or discount relative to the ETF's official NAV.

Suppose the ETF's NAV tomorrow is ₹100. If it trades at ₹102.70, its premium is 2.7%.

Now, your model doesn't produce just one prediction. It uses five separate quantile models to estimate five points in the possible distribution of tomorrow's premium:

| Model output          | Predicted premium |
| --------------------- | ----------------- |
| 5th percentile (Q5)   | +1.2%             |
| 25th percentile (Q25) | +2.0%             |
| 50th percentile (Q50) | +2.7%             |
| 75th percentile (Q75) | +3.5%             |
| 95th percentile (Q95) | +4.8%             |

What is the median?

The median is the middle value when values are arranged from lowest to highest.

For example, if five students score 40, 50, 60, 70 and 80 marks, the median score is 60. There are two scores below it and two above it.

In your project, however, the +2.7% is not the median of five randomly collected historical premiums. It is the 50th-percentile forecast of tomorrow's premium, generated by the model.

It means that, according to the model's estimated distribution, approximately half of the possible outcomes are below +2.7%, and half are above it.

In simpler language, +2.7% is the model's central estimate of tomorrow's premium.

## 2. What does the 90% prediction interval mean?

The model's 90% prediction interval is:

PREDICTED PREMIUM RANGE

# +1.2% to +4.8%

5th percentile

95th percentile

The model estimates that the central 90% of the outcome distribution lies between these two values.

Imagine the model could somehow simulate tomorrow's market 1,000 times under the conditions it has observed today.

It might estimate that:

- In roughly 50 simulations, the premium is below +1.2%.
- In roughly 900 simulations, the premium falls between +1.2% and +4.8%.
- In roughly 50 simulations, the premium is above +4.8%.

That is the intuition behind the 90% interval. The actual model does not literally run 1,000 simulations; it estimates the 5th and 95th percentiles using quantile regression, then applies a calibration step called Conformalized Quantile Regression (CQR).

So how do the two numbers work together?

The median forecast of +2.7% is the central estimate. The interval of +1.2% to +4.8% communicates uncertainty around that estimate.

One important qualification: a 90% prediction interval does not mean there is a 90% chance that the median forecast is correct. It means the interval is designed, and empirically calibrated, to contain the actual next-day premium approximately 90% of the time over the relevant evaluation data. It is not a guarantee for every individual day.

## 3. What exactly are you doing with the October 2025 event?

The October event is your historical event study. You are using a real episode of unusual silver ETF pricing to examine whether your system could have identified the developing situation.

Here is the background: during October 2025, silver ETFs reportedly traded at premiums of around 5–10% relative to their intraday indicative value (iNAV). There were also restrictions on fresh investments in some silver ETF Fund of Funds because of difficulties sourcing physical silver.

Your project is asking a specific question:

"If my early-warning system had existed at that time, would it have raised warnings as the unusual pricing conditions developed?"

To investigate this, you would:

First, reconstruct what was happening. Collect the historical exchange prices and official AMFI NAVs for the relevant silver ETFs. Calculate each day's premium or discount.

For example:

| Date  | Closing price | Official NAV | Premium |
| ----- | ------------- | ------------ | ------- |
| Day 1 | ₹105          | ₹100         | +5%     |
| Day 2 | ₹107          | ₹100         | +7%     |
| Day 3 | ₹109          | ₹100         | +9%     |

These numbers are illustrative, not actual historical observations.

Second, replay the model day by day. Imagine the model existed on Day 1. Give it only the information that would have been available on Day 1, and ask it to predict Day 2. Then compare its prediction with what actually happened on Day 2.

Repeat this for the entire event period. You can then examine whether it raised a Watch or High warning before or during the unusual premium expansion.

Third, assess how well it performed. Did it identify the growing deviation? How early did it raise a warning? Did it miss the event? Did it raise unnecessary warnings?

There is an important distinction in your project: the October reports described premiums relative to iNAV, but your historical model is trained and evaluated against official NAV because that is the historical valuation series you can use consistently. Therefore, you must reconstruct and evaluate the actual closing-price-versus-official-NAV deviation. You cannot simply take the reported 5–10% iNAV premium figures and treat them as the model's ground-truth results. The two comparisons can differ because their valuation timings differ.&#x20;

In one sentence: October is your test of whether the model could have detected a real historical episode of unusual ETF pricing.

## 4. What exactly are you doing with the January–February 2026 event?

This is your stress test.

Think of it this way: October tests your model against an unusual premium episode. January–February tests it against a much more extreme and chaotic market environment.

In late January and early February 2026, precious-metal prices experienced extreme volatility. Silver saw a particularly sharp global price decline. During the special Indian trading session on 1 February, several silver ETFs hit their lower price circuits.

There was an additional complication: the exchange's price limits were initially being calculated using an older NAV reference (T-2), which did not adequately reflect the latest underlying market movements. The exchange subsequently issued a special circular changing the reference to T-1.

What is a price circuit?

Exchanges impose price limits to restrict how far a security can move during a trading session. If an ETF hits its lower circuit, it cannot fall below that permitted price during that session. Sellers may be willing to sell, but there may be insufficient buyers to execute their orders.

This can prevent the ETF's market price from adjusting freely to changing underlying values.

### What does stress testing mean in your project?

Imagine you have built a car. You don't just test whether it drives normally on a smooth road. You also test what happens under extreme conditions: heavy braking, rough roads and sudden obstacles.

Your January–February exercise does something similar with your model.

You deliberately expose it to historical market conditions that are much more extreme than ordinary trading days and examine how it behaves.

Specifically, you want to investigate:

1\. Does the model recognise deteriorating conditions? Do its predictions and tail-risk probabilities respond when metal prices become extremely volatile and ETF premiums or discounts behave abnormally?

2\. Does it remain reliable? Does the model still produce meaningful forecasts, or does its accuracy deteriorate substantially during extreme market conditions?

3\. Can it distinguish market stress from trading restrictions? If an ETF hits a lower circuit, its market price may not be able to adjust freely. You need to identify those days rather than treating their observed prices as ordinary market outcomes.

4\. Does it produce misleading warnings? You want to understand whether the system generates useful warnings or becomes excessively alarmed during extreme volatility.

### One very important limitation

You are not claiming that your model can predict a 30% silver crash or forecast when an ETF will hit a lower circuit.

Your project predicts unusual ETF premium/discount behaviour. It does not forecast global commodity crashes or simulate exchange price-band mechanisms.

The circuit-lock days will be explicitly identified and treated carefully in your analysis. You should not silently remove them, but neither should you claim that the model successfully predicted the circuit events.

In one sentence: January–February is your test of how robustly the model behaves when financial markets experience extreme volatility and normal ETF price-adjustment mechanisms become constrained.

## 5. The difference between your two historical exercises

|                         | October 2025                                                      | January–February 2026                                                       |
| ----------------------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Purpose                 | Historical event study                                            | Extreme-market stress test                                                  |
| What happened?          | Unusually large silver ETF premiums                               | Precious-metal crash and ETF circuit locks                                  |
| What you examine        | Could the model have detected the developing premium dislocation? | How does the model behave under extreme volatility and constrained trading? |
| Main concern            | Early identification                                              | Robustness and limitations                                                  |
| What you must not claim | That it predicted the reported iNAV premium figures               | That it predicted the crash or circuit locks                                |

## 6. If nakul asks why you chose these two events

You can say:

" I deliberately selected two different historical market situations. October 2025 represents a premium-dislocation episode, where silver ETFs traded at unusually high premiums amid physical silver sourcing constraints. January–February 2026 represents an extreme volatility episode, where precious-metal prices crashed and several ETFs experienced lower-circuit restrictions.

The first helps me evaluate whether the system can identify unusual premium behaviour. The second helps me understand how robust the model is under extreme market conditions, including situations where exchange trading restrictions interfere with normal price discovery.

Together, they allow me to examine both the predictive usefulness and the limitations of the system."

The distinction to remember: October asks could we have seen the pricing problem developing? January–February asks how does our system behave when the market becomes exceptionally stressed?

That is the purpose of both exercises.

Yes. That is essentially the project, with one important distinction: you are predicting both the expected size of the premium/discount and the probability of an unusually large deviation.

These are two separate predictions:

- Prediction 1 — How much? The model forecasts tomorrow's premium or discount relative to NAV. For example, it might predict a median premium of +2.7%, with a 90% prediction interval of +1.2% to +4.8%.
- Prediction 2 — How unusual or risky? The model estimates the probability that tomorrow's premium will move unusually far away from that ETF's own recent normal. For example, it might assign a 68% probability and classify the ETF as High Risk.

The 68% does not mean a 68% chance of a 2.7% premium, nor does it tell you the size of the deviation. The first output gives you the expected pricing level and its range; the second gives you the probability of a tail event.

A useful way to remember it:

Output A: Where might the ETF trade? Output B: How likely is it to behave abnormally?

## 1. What are the 30–45 features?

A feature is simply a measurable piece of information that the machine-learning model uses to make its predictions.

Think of the model as an analyst examining an ETF. Instead of giving it just today's premium and asking it to predict tomorrow's behaviour, you give it around 35–45 different indicators describing what is happening to that ETF and its surrounding market.

Your technical specification groups these into five categories. Here is what they mean in practical terms.

1\. Premium and discount behaviour

Historical pricing

These features describe how the ETF's market price has behaved relative to its NAV.

Examples:

- Today's premium or discount.
- Premium 1, 3 or 5 trading days ago.
- Average and median premium over the last 5, 20 and 60 days.
- How volatile its premium has been recently.
- How quickly its premium has been increasing or decreasing.

2\. Trading activity and liquidity

Market activity

These features help identify unusual trading behaviour.

Examples:

- Today's trading volume compared with its 20-day average.
- Turnover (total monetary value of units traded).
- Number of trades.
- Daily price range (high versus low).
- Whether the ETF has experienced unusually low trading activity or a stale price.

3\. Underlying gold/silver behaviour

Commodity markets

These features capture what is happening to the asset the ETF actually tracks.

Examples:

- Gold or silver price movement over the last 1, 3 and 5 days.
- Recent gold/silver price volatility.
- Large overnight price movements.
- Sharp declines from recent price highs.
- Differences between the underlying metal's movement and the ETF's NAV movement.

4\. Peer ETF behaviour

Market comparison

You compare an ETF against other ETFs tracking the same metal.

Examples:

- Average premium of other silver ETFs.
- Difference between this ETF's premium and the peer-group average.
- How widely premiums vary across competing ETFs.
- Percentage of peer ETFs experiencing unusually high premiums or discounts.

5\. Market and regulatory context

External conditions

These features capture relevant circumstances that might influence ETF pricing.

Examples:

- Whether the ETF tracks gold or silver.
- Which AMC manages it.
- How long the ETF has been listed.
- Proximity to events such as Dhanteras, Diwali or Akshaya Tritiya.
- Whether a relevant FoF investment restriction is active.
- Which regulatory or price-band regime applies.

The exact number of features in each category will depend on the final implementation. The specification targets approximately 35–45 features in total.

The important thing to understand: You are not manually telling the AI that a particular combination of signals means trouble. You are giving it historical examples and these features, allowing it to learn which combinations have historically been associated with unusual premium/discount movements.

For instance, it might learn that a sudden increase in premium, combined with a sharp rise in trading turnover and high silver volatility, is a warning pattern.

## 2. How does this make money or create monetary value for Mirae Asset?

This is an important question because nakul is likely to be more interested in the business value than the technical implementation.

Your project is not directly generating trading profits. It is a risk-monitoring and decision-support tool. Its monetary value comes from potentially improving how Mirae manages, distributes and communicates its ETF products.

Consider four stakeholders.

### A. Mirae Asset as an AMC

The biggest potential benefit is protecting the reputation and competitiveness of its ETF products.

Imagine Mirae's Silver ETF begins trading at a 7% premium while its underlying silver holdings have not increased by anything close to that amount.

An investor buying at that price is effectively paying considerably more than the underlying value of the fund's holdings.

If the premium subsequently collapses, that investor could suffer a loss even if silver itself has barely moved.

An early-warning system could help Mirae identify deteriorating pricing conditions and investigate them earlier.

Potential business benefits include:

- Better visibility into abnormal pricing conditions affecting its ETFs.
- Earlier investigation of possible liquidity or market-making problems.
- Better communication with distributors and investors.
- Reduced risk of reputational damage from investors experiencing unexpected premium collapses.
- Potentially better investor confidence and long-term product retention.

It does not guarantee that Mirae can eliminate the premium or prevent a market disruption.

### B. ETF Sales Department and Distributors

This is particularly relevant to the department you are pitching to.

Imagine a distributor calls a Mirae sales representative and asks:

"Why is your Silver ETF trading at a 5% premium? Should I recommend it to my clients?"

Without a monitoring system, the representative may have to manually investigate market prices, NAV, trading activity and competing ETFs.

With your system, the sales representative could have access to:

- The ETF's current and predicted premium range.
- Whether the premium is behaving unusually.
- Whether competing silver ETFs are experiencing similar conditions.
- The main factors contributing to the warning.

This gives the sales team more information to handle distributor queries and investor conversations.

It could also help them identify situations where they should exercise caution rather than aggressively promote an ETF when its market price is unusually disconnected from NAV.

### C. Investors and ETF Unit Holders

This is the investor-protection angle.

Suppose an investor wants to invest ₹1 lakh in a silver ETF.

If the ETF is trading at a 5% premium, the investor is paying approximately ₹1.05 lakh for underlying assets worth ₹1 lakh, ignoring transaction costs and other differences.

If that premium subsequently disappears, the investor can lose money even if the underlying silver price remains unchanged.

A warning system could help distributors and investors become more aware of these conditions before making investment decisions.

This could improve transparency and reduce the likelihood of investors unknowingly buying at unusually elevated premiums.

### D. Mirae Asset's Shareholders

For the AMC's shareholders, the potential benefits are indirect.

Better investor confidence, fewer reputational problems, improved product competitiveness and stronger distributor relationships could contribute to better long-term business performance.

That could support AUM retention, product growth and ultimately revenue generation.

However, you should not claim that this project directly increases shareholder returns. Its contribution would be through improved risk awareness and business decision-making.

The strongest business argument to make to nakul:

"The objective is not to generate trading profits. It is to give the ETF sales and product teams earlier visibility into abnormal pricing conditions, so they can investigate potential problems, communicate more effectively with distributors and help investors make better-informed decisions."

## 3. September 2026 SEBI guidelines: What changed?

First, a small correction: the relevant SEBI circular was issued on 15 June 2026, with implementation subsequently scheduled for 7 September 2026 following an extension in August. The NSE issued its implementation circular on 1 September.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.sebi.gov.in&sz=32)

sebi.gov.in+2

The changes are particularly relevant to your project because they concern how Gold and Silver ETFs are allowed to trade during periods of volatility.

There are three major things to understand.

### Change 1: The reference price used to calculate price limits

Previously, ETF price bands were generally calculated using the ETF's NAV from two trading days earlier, known as T-2 NAV.

The new framework uses the ETF's previous trading day's closing market price, calculated using the Volume Weighted Average Price (VWAP) during the final 30 minutes of trading, as the base price.

Why?

Because an ETF's NAV from two days ago may be considerably outdated when gold or silver prices move sharply.

Using a more recent market-price reference helps keep the trading limits more relevant to prevailing market conditions.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.compliedai.com&sz=32)

SEBI circular+1

### Change 2: Dynamic price bands for Gold and Silver ETFs

Previously, ETFs generally had a fixed ±20% price band, with certain exceptions.

Under the new framework, Gold and Silver ETFs start with a dynamic ±6% price band.

If the price approaches the threshold (the framework specifies 5.90% as the trigger), a cooling-off period applies. After the applicable period, the exchange can widen the price band by another 3 percentage points.

The cooling-off period is generally 15 minutes, reduced to 5 minutes during the final 30 minutes of the trading session. Further widening may be permitted in stages under specified conditions when international commodity movements are sufficiently large.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.compliedai.com&sz=32)

SEBI circular+1

For example, imagine an ETF has a base price of ₹100.

Illustrative price-band progression

Initial band

## ₹94–₹106

After one 3-percentage-point expansion

## ₹91–₹109

Illustrative only. Actual exchange operation depends on the applicable triggers and circular provisions.

This is called a dynamic price band because the permitted trading range can expand as the market moves.

### Change 3: Pre-open call auction for Gold and Silver ETFs

Gold and Silver ETFs are now included in the pre-open session.

Why is this useful?

Gold and silver trade internationally, including when Indian stock exchanges are closed.

For example, international silver prices may move sharply overnight. When the Indian market opens, there may be a significant difference between yesterday's ETF closing price and the latest underlying metal value.

A pre-open call auction allows buy and sell orders to be collected and matched to help determine an opening price before continuous trading begins.

This can improve the opening price-discovery process.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://www.compliedai.com&sz=32)

NSE circular+1

## 4. What exactly are T-1 and T-2? And what happened in February 2026?

This is easier than it sounds.

- T = the trading day you are currently talking about.
- T-1 = the immediately preceding trading day.
- T-2 = two trading days before the current trading day.

For example, assuming there are no intervening holidays:

| Trading day | Meaning |
| ----------- | ------- |
| Thursday    | T-2     |
| Friday      | T-1     |
| Monday      | T       |

Now imagine silver prices fall sharply over the weekend.

On Monday morning, the ETF's actual underlying value may be considerably lower than it was on Friday.

But if the exchange calculates the ETF's permitted price range using Thursday's NAV (T-2), it is using an older valuation.

This can create a problem: the exchange's permitted trading range may not reflect the latest market conditions.

That is broadly what happened during the February 2026 precious-metal volatility episode.

The NSE subsequently issued a circular changing the reference for Gold and Silver ETF price bands to T-1 NAV for the relevant trading session.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://nsearchives.nseindia.com&sz=32)

nsearchives.nseindia.com+1

Now connect this to the September framework.

There are actually two distinct changes:

|                 | February 2026 emergency adjustment                        | September 2026 framework                                |
| --------------- | --------------------------------------------------------- | ------------------------------------------------------- |
| Reference price | T-1 NAV                                                   | T-1 closing market price (last 30-min VWAP)             |
| Purpose         | Address exceptional volatility and stale reference values | Establish a revised general ETF trading framework       |
| Price bands     | Existing ±20% band applied to revised reference           | Dynamic ±6% for Gold/Silver ETFs, with staged expansion |

This distinction is important. The September framework does not simply make the February temporary adjustment permanent. It changes both the reference-price methodology and the price-band structure.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://nsearchives.nseindia.com&sz=32)

nsearchives.nseindia.com+2

## 5. What should you say if nakul asks how SEBI's changes relate to your project?

You can say:

"Recent SEBI changes have made ETF price discovery and price-band mechanisms particularly relevant, especially for commodity ETFs. The revised framework uses a more recent reference price, introduces dynamic price bands for Gold and Silver ETFs, and allows pre-open price discovery.

My project is complementary to these regulatory mechanisms. SEBI's framework governs how ETFs are allowed to trade, whereas my system attempts to identify when an ETF's market price may be behaving unusually relative to its underlying NAV.

The regulatory changes also make it important to account for different price-band regimes when analysing historical data. I therefore include regulatory regime information in the model and explicitly identify circuit-constrained trading days during historical testing."
