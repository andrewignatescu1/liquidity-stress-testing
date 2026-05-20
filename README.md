Liquidity Stress Test and Covenant Screening Model

A Python tool that tests how well a public company would hold up if things go wrong financially. It looks at what would break first under pressure, whether that is running out of cash, not earning enough to cover interest payments, taking on too much debt relative to earnings, or struggling to pay short term bills.

The user enters the stock ticker of any U.S. public company, and the program automatically pulls that company's most recent financial data from the SEC, which is the government database where public companies are required to report their financials. The user then sets the limits a lender would typically care about, such as the maximum amount of debt the company can carry, the minimum amount of earnings needed to cover interest, and the minimum cash balance that should stay on hand.

The model then runs the company's numbers through different bad case scenarios, like a drop in sales, shrinking profit margins, rising interest rates, and cash getting tied up in inventory or unpaid customer bills. Each scenario represents the kind of pressure companies actually face during downturns.

For every scenario, the model recalculates the key financial health metrics and checks whether the company would still meet the lender style limits set earlier. The output shows whether the company passes or fails and makes it easy to see exactly where it breaks, whether that is too much debt, not enough earnings, weak short term liquidity, or simply running out of cash.

The tool is a simplified version of how banks and credit analysts evaluate companies before lending money. It is not a full credit analysis, but it captures the core idea of testing a company against bad conditions rather than assuming everything will go well.


