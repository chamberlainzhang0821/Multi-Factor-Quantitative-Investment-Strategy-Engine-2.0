import pandas as pd

class SignalEngine:
    def __init__(
        self, 
        top_n=2, 
        score_threshold=1.5,
        min_amount_quantile=0.30,
        exclude_gem=True,
        exclude_star=True,
        require_main_force=True
    ):
        """
        Configures the signal generation rules including liquidity, 
        board constraints, and composite alpha scores.
        """
        self.top_n = top_n
        self.score_threshold = score_threshold
        self.min_amount_quantile = min_amount_quantile
        self.exclude_gem = exclude_gem
        self.exclude_star = exclude_star
        self.require_main_force = require_main_force

    def generate_daily_buy_list(self, current_date, factor_df):
        """
        Filters stocks based on liquidity, board constraints, main force confirmation,
        and finally selects the top N candidates by composite alpha score.
        """
        # Fetch today's cross-section
        df_today = factor_df[factor_df['date'] == current_date].copy()
        
        # Guard against empty data or missing core columns
        required_cols = ['alpha_score', 'amount', 'ts_code']
        if df_today.empty or not all(col in df_today.columns for col in required_cols):
            return []
            
        # ---------------------------------------------------------
        # 1. Liquidity Filter (Cross-sectional dynamic quantile)
        # ---------------------------------------------------------
        cutoff = df_today["amount"].quantile(self.min_amount_quantile)
        df_today = df_today[df_today["amount"] > cutoff]

        # ---------------------------------------------------------
        # 2. Board Exclusions (GEM & STAR)
        # ---------------------------------------------------------
        if self.exclude_gem:
            df_today = df_today[~df_today["ts_code"].str.startswith(("300", "301"))]
            
        if self.exclude_star:
            df_today = df_today[~df_today["ts_code"].str.startswith(("688", "689"))]

        # ---------------------------------------------------------
        # 3. Main Force Confirmation
        # ---------------------------------------------------------
        if self.require_main_force and 'main_force_score' in df_today.columns:
            df_today = df_today[df_today["main_force_score"] > 0]

        # ---------------------------------------------------------
        # 4. Final Alpha Score Filter & Sorting
        # ---------------------------------------------------------
        # Filter high-conviction signals
        qualified = df_today[df_today['alpha_score'] >= self.score_threshold]
        
        # Sort descending by the composite score
        qualified = qualified.sort_values('alpha_score', ascending=False)
        
        return qualified['ts_code'].head(self.top_n).tolist()