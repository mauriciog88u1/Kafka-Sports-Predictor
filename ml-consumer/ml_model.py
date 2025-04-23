import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import os

class MatchPredictor:
    def __init__(self):
        self.model = None
        self.label_encoder = LabelEncoder()
        self.feature_names = [
            'home_team_rank',
            'away_team_rank',
            'home_team_form',
            'away_team_form',
            'home_team_goals_scored',
            'away_team_goals_scored',
            'home_team_goals_conceded',
            'away_team_goals_conceded',
            'home_team_points',
            'away_team_points'
        ]
        
    def extract_features(self, match_data):
        """Extract features from match data for prediction"""
        features = {}
        
        # Get team ranks
        league_table = match_data.get("leagueTable", [])
        home_team = match_data.get("strHomeTeam", "")
        away_team = match_data.get("strAwayTeam", "")
        
        # Initialize default values
        features['home_team_rank'] = 20
        features['away_team_rank'] = 20
        features['home_team_points'] = 0
        features['away_team_points'] = 0
        features['home_team_goals_scored'] = 0
        features['away_team_goals_scored'] = 0
        features['home_team_goals_conceded'] = 0
        features['away_team_goals_conceded'] = 0
        
        # Get team stats from league table
        for team in league_table:
            if team.get("strTeam") == home_team:
                features['home_team_rank'] = int(team.get("intRank", 20))
                features['home_team_points'] = int(team.get("intPoints", 0))
                features['home_team_goals_scored'] = int(team.get("intGoalsFor", 0))
                features['home_team_goals_conceded'] = int(team.get("intGoalsAgainst", 0))
            elif team.get("strTeam") == away_team:
                features['away_team_rank'] = int(team.get("intRank", 20))
                features['away_team_points'] = int(team.get("intPoints", 0))
                features['away_team_goals_scored'] = int(team.get("intGoalsFor", 0))
                features['away_team_goals_conceded'] = int(team.get("intGoalsAgainst", 0))
        
        # Calculate team form from match history
        match_history = match_data.get("matchHistory", [])
        home_wins = 0
        away_wins = 0
        
        for match in match_history:
            if match.get("strHomeTeam") == home_team:
                if match.get("intHomeScore", 0) > match.get("intAwayScore", 0):
                    home_wins += 1
            elif match.get("strAwayTeam") == home_team:
                if match.get("intAwayScore", 0) > match.get("intHomeScore", 0):
                    home_wins += 1
                    
            if match.get("strHomeTeam") == away_team:
                if match.get("intHomeScore", 0) > match.get("intAwayScore", 0):
                    away_wins += 1
            elif match.get("strAwayTeam") == away_team:
                if match.get("intAwayScore", 0) > match.get("intHomeScore", 0):
                    away_wins += 1
        
        features['home_team_form'] = home_wins
        features['away_team_form'] = away_wins
        
        return features
    
    def train(self, training_data):
        """Train the random forest model"""
        X = []
        y = []
        
        for match in training_data:
            features = self.extract_features(match)
            X.append([features[feature] for feature in self.feature_names])
            y.append(match['result'])  # 'result' should be 'home', 'away', or 'draw'
        
        X = np.array(X)
        y = self.label_encoder.fit_transform(y)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X, y)
    
    def predict(self, match_data):
        """Predict the outcome of a match"""
        if self.model is None:
            # If model is not trained, use simple heuristic
            return self._simple_heuristic(match_data)
        
        features = self.extract_features(match_data)
        X = np.array([[features[feature] for feature in self.feature_names]])
        
        prediction = self.model.predict(X)[0]
        prediction_proba = self.model.predict_proba(X)[0]
        
        # Convert prediction back to team name
        if prediction == 0:  # Home win
            return match_data.get("strHomeTeam", "Home Team")
        elif prediction == 1:  # Away win
            return match_data.get("strAwayTeam", "Away Team")
        else:  # Draw
            return "Draw"
    
    def _simple_heuristic(self, match_data):
        """Fallback to simple heuristic if model is not trained"""
        home_team = match_data.get("strHomeTeam", "")
        away_team = match_data.get("strAwayTeam", "")
        
        if not home_team or not away_team:
            return "N/A"
        
        # Initialize scores
        home_score = 10  # Home team gets a baseline advantage
        away_score = 0
        
        # Get team form from match history
        match_history = match_data.get("matchHistory", [])
        home_wins = 0
        away_wins = 0
        
        for match in match_history:
            if match.get("strHomeTeam") == home_team:
                if match.get("intHomeScore", 0) > match.get("intAwayScore", 0):
                    home_wins += 1
            elif match.get("strAwayTeam") == home_team:
                if match.get("intAwayScore", 0) > match.get("intHomeScore", 0):
                    home_wins += 1
                    
            if match.get("strHomeTeam") == away_team:
                if match.get("intHomeScore", 0) > match.get("intAwayScore", 0):
                    away_wins += 1
            elif match.get("strAwayTeam") == away_team:
                if match.get("intAwayScore", 0) > match.get("intHomeScore", 0):
                    away_wins += 1
        
        # Add form points
        home_score += home_wins * 2
        away_score += away_wins * 2
        
        # Get league positions
        league_table = match_data.get("leagueTable", [])
        home_position = 20
        away_position = 20
        
        for team in league_table:
            if team.get("strTeam") == home_team:
                try:
                    home_position = int(team.get("intRank", 20))
                except ValueError:
                    pass
            elif team.get("strTeam") == away_team:
                try:
                    away_position = int(team.get("intRank", 20))
                except ValueError:
                    pass
        
        # Add league position points
        home_score += (21 - home_position) * 2
        away_score += (21 - away_position) * 2
        
        # Determine the outcome
        if home_score > away_score:
            return home_team
        elif away_score > home_score:
            return away_team
        else:
            return "Draw"
    
    def save_model(self, path):
        """Save the trained model to disk"""
        if self.model is not None:
            joblib.dump(self.model, path)
    
    def load_model(self, path):
        """Load a trained model from disk"""
        if os.path.exists(path):
            self.model = joblib.load(path) 