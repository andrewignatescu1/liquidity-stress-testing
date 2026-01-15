Liquidity Stress Test and Covenant Screening Model

This project is an interactive Python-based liquidity and covenant stress testing tool designed to evaluate how a public company’s financial resilience changes under adverse operating and financing conditions. The model is built to reflect how banks and credit teams think about downside risk, focusing less on optimistic projections and more on identifying what breaks first: cash, coverage, leverage, or working capital.

The program begins by prompting the user for a U.S.-listed ticker symbol and then pulls base-year financial statement items directly from the SEC’s XBRL company facts database. Using reported annual figures rather than fabricated inputs keeps the analysis anchored to reality, which is critical when the goal is to understand whether a company can withstand stress conditions and remain solvent and liquid.

After establishing the base year, the user enters covenant-style thresholds that approximate common credit agreement constraints, such as maximum net leverage, minimum interest coverage, minimum current ratio, and a minimum cash floor. The model then applies scenario-based shocks to revenue, EBITDA margin, interest rates, and working capital. These shocks are designed to represent mild and severe deterioration in operating performance as well as tightening financial conditions, which together capture the most common failure modes observed in real credit environments.

For each scenario, the model recomputes key liquidity and credit metrics including current ratio, net debt to EBITDA, EBITDA to interest coverage, free cash flow, and ending cash balance. It then evaluates whether the company passes or fails each covenant threshold and provides an overall pass/fail outcome. The outputs are structured to make risk drivers easy to interpret, allowing the user to see whether the company fails due to leverage expansion, coverage compression, working capital pressure, or a direct liquidity shortfall.

This project demonstrates the ability to use public financial disclosures, translate them into credit-relevant metrics, and conduct disciplined downside analysis under uncertainty. It reflects practical credit thinking that is directly applicable to banking, leveraged finance, credit research, and corporate treasury roles, where the central question is not how good outcomes might be, but how the company behaves when conditions deteriorate.

Author: Andrew Ignatescu
# liquidity-stress-testing
