from typing import Tuple


class PredictionPointsService:
    """Service encapsulating prediction scoring rules.

    Scoring rules implemented:
      - exact score (predicted home and away exactly): default 3 points
      - correct winner (predicted winner same as actual, but not exact): default 1 point
      - wrong outcome: 0 points

    This service is intentionally small and pure so it can be used from
    other services (cron, endpoints, tests) without DB dependencies.
    """

    def __init__(self, exact_points: int = 3, correct_winner_points: int = 1):
        self.exact_points = exact_points
        self.correct_winner_points = correct_winner_points

    def _get_winner(self, goals_home: int, goals_away: int) -> str:
        if goals_home > goals_away:
            return "home"
        elif goals_away > goals_home:
            return "away"
        else:
            return "draw"

    def score_prediction(
        self,
        pred_goals_home: int,
        pred_goals_away: int,
        fixture_goals_home: int,
        fixture_goals_away: int,
    ) -> Tuple[int, str]:
        """Return (points, reason)

        reason is one of: 'exact', 'winner', 'wrong'
        """
        # Normalize None -> 0 to avoid TypeErrors if upstream passes None
        try:
            pg_h = 0 if pred_goals_home is None else int(pred_goals_home)
            pg_a = 0 if pred_goals_away is None else int(pred_goals_away)
            fg_h = 0 if fixture_goals_home is None else int(fixture_goals_home)
            fg_a = 0 if fixture_goals_away is None else int(fixture_goals_away)
        except (TypeError, ValueError):
            # If values are not integers, treat as wrong prediction
            return 0, "wrong"

        if pg_h == fg_h and pg_a == fg_a:
            return self.exact_points, "exact"

        pred_winner = self._get_winner(pg_h, pg_a)
        actual_winner = self._get_winner(fg_h, fg_a)

        if pred_winner == actual_winner:
            return self.correct_winner_points, "winner"

        return 0, "wrong"
