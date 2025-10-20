# 🎯 Prediction System Design - Prode App

## 📋 **System Overview**

The Prediction System is the core functionality of the Prode App, allowing users to predict football match outcomes. Predictions are **global per user** - meaning a single prediction applies across all tournaments the user participates in.

### **Key Principles:**
- **One prediction per user per match** - Users cannot have multiple predictions for the same match
- **Global predictions** - Same prediction counts for all tournaments
- **Time-locked predictions** - Cannot predict after match starts
- **Flexible scoring** - Supports goals and penalties
- **Privacy-aware** - Only show predictions from shared tournaments

---

## 🗄️ **Database Schema**

### **Core Tables:**

#### **`predictions`**
```sql
CREATE TABLE predictions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    goals_home INTEGER NOT NULL CHECK (goals_home >= 0),
    goals_away INTEGER NOT NULL CHECK (goals_away >= 0),
    penalties_home INTEGER CHECK (penalties_home >= 0),
    penalties_away INTEGER CHECK (penalties_away >= 0),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, match_id)
);
```

#### **`matches`**
```sql
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    round_id INTEGER NOT NULL REFERENCES rounds(id),
    home_team_id INTEGER NOT NULL REFERENCES teams(id),
    away_team_id INTEGER NOT NULL REFERENCES teams(id),
    start_time TIMESTAMP NOT NULL,
    finished BOOLEAN DEFAULT FALSE,
    result_goals_home INTEGER,
    result_goals_away INTEGER,
    result_penalties_home INTEGER,
    result_penalties_away INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

#### **`teams`**
```sql
CREATE TABLE teams (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    country_id INTEGER NOT NULL REFERENCES countries(id),
    league_id INTEGER NOT NULL REFERENCES leagues(id),
    logo_url VARCHAR(500)
);
```

### **Relationships:**
```
User (1) --- (∞) Prediction (∞) --- (1) Match (∞) --- (1) Round (∞) --- (1) League
                    ↓
                Tournament (∞) --- (∞) User
```

---

## 🔧 **Core Business Logic**

### **Prediction Rules:**

1. **Uniqueness**: One prediction per user per match
2. **Time Lock**: Cannot predict after `match.start_time`
3. **Update Allowed**: Can update predictions before match starts
4. **Delete Allowed**: Can delete predictions before match starts
5. **Global Scope**: Same prediction applies to all tournaments

### **Validation Logic:**

```python
def validate_prediction_creation(user_id, match_id, goals_home, goals_away):
    # Check match exists
    match = get_match(match_id)
    if not match:
        raise ValueError("Match not found")
    
    # Check match not locked
    if match.is_locked():
        raise ValueError("Cannot predict for started/finished match")
    
    # Check no existing prediction
    if prediction_exists(user_id, match_id):
        raise ValueError("Prediction already exists")
    
    # Validate goals
    if goals_home < 0 or goals_away < 0:
        raise ValueError("Goals must be non-negative")
```

### **Scoring System:**

```python
def calculate_score(prediction, match_result):
    score = 0
    
    # Exact score bonus
    if (prediction.goals_home == match_result.goals_home and 
        prediction.goals_away == match_result.goals_away):
        score += EXACT_SCORE_POINTS
    
    # Correct winner
    elif get_winner(prediction) == get_winner(match_result):
        score += CORRECT_WINNER_POINTS
    
    # Penalty bonus
    if (prediction.penalties_home == match_result.penalties_home and
        prediction.penalties_away == match_result.penalties_away):
        score += PENALTY_BONUS_POINTS
    
    return score
```

---

## 🚀 **API Endpoints**

### **User Endpoints:**

#### **POST** `/predictions`
Create or update a prediction
```json
{
    "match_id": 123,
    "goals_home": 2,
    "goals_away": 1,
    "penalties_home": 4,
    "penalties_away": 3
}
```

#### **GET** `/predictions`
Get user's predictions with optional filters
- `?round_id=5` - Filter by round
- `?league_id=2` - Filter by league  
- `?match_id=123` - Get specific match prediction

#### **DELETE** `/predictions/{match_id}`
Delete a prediction (before match starts)

#### **GET** `/predictions/stats`
Get user's prediction statistics

#### **GET** `/predictions/match/{match_id}`
Get all predictions for a match (from shared tournaments)

### **Admin Endpoints:**

#### **GET** `/admin/predictions/match/{match_id}`
Get all predictions for a match (admin only)

#### **POST** `/admin/predictions/score`
Calculate scores for a match
```json
{
    "match_id": 123,
    "exact_score_points": 10,
    "correct_winner_points": 5,
    "penalty_bonus_points": 3
}
```

---

## 📊 **Use Cases**

### **Primary Use Cases:**

1. **Create Prediction**
   - User selects a match
   - Enters predicted score
   - Optionally adds penalty prediction
   - System validates and stores

2. **Update Prediction**
   - User modifies existing prediction
   - System checks match not started
   - Updates timestamp

3. **View Predictions**
   - User sees all their predictions
   - Can filter by round/league
   - Shows match details and results

4. **Delete Prediction**
   - User removes prediction
   - Only allowed before match starts

5. **View Match Predictions**
   - See other users' predictions
   - Only from shared tournaments
   - Privacy-aware display

### **Admin Use Cases:**

1. **Score Calculation**
   - Admin triggers scoring for finished match
   - System calculates all user scores
   - Stores or returns results

2. **Prediction Analytics**
   - View all predictions for a match
   - Generate statistics
   - Export data

### **Future Use Cases:**

1. **AI Predictions**
   - Premium feature
   - AI-generated predictions
   - Optional override

2. **Prediction History**
   - Past predictions and results
   - Performance tracking
   - Trend analysis

3. **Advanced Statistics**
   - Accuracy per league
   - Most common outcomes
   - User rankings

---

## 🔒 **Security & Privacy**

### **Access Control:**

- **Own Predictions**: Users can only see/modify their own predictions
- **Shared Tournaments**: Can see other users' predictions only if in shared tournament
- **Admin Access**: Admins can see all predictions
- **Time-based**: Cannot modify after match starts

### **Data Validation:**

- **Input Validation**: Pydantic schemas validate all inputs
- **Business Rules**: Server-side validation of business logic
- **SQL Injection**: Parameterized queries prevent SQL injection
- **XSS Protection**: Input sanitization and output encoding

---

## ⚡ **Performance Considerations**

### **Database Optimization:**

- **Indexes**: `(user_id, match_id)` for fast lookups
- **Foreign Keys**: Proper relationships with cascade deletes
- **Query Optimization**: Efficient joins and filters
- **Connection Pooling**: Async SQLAlchemy with connection pooling

### **Caching Strategy:**

- **Recent Predictions**: Cache frequently accessed predictions
- **Match Data**: Cache match information
- **User Stats**: Cache calculated statistics
- **Valkey Integration**: Redis-like caching for hot data

### **Scalability:**

- **Async Operations**: Non-blocking I/O for better performance
- **Database Sharding**: Partition by user_id or league_id
- **CDN**: Static content delivery
- **Load Balancing**: Multiple server instances

---

## 🧪 **Testing Strategy**

### **Unit Tests:**
- Model validation
- Business logic functions
- Service layer methods
- Error handling

### **Integration Tests:**
- API endpoint testing
- Database operations
- Authentication flows
- Permission checks

### **End-to-End Tests:**
- Complete user workflows
- Tournament integration
- Score calculation
- Admin operations

---

## 📈 **Monitoring & Analytics**

### **Key Metrics:**
- Prediction creation rate
- User engagement
- Accuracy trends
- System performance

### **Logging:**
- Structured logging with JSON format
- Error tracking and alerting
- User action auditing
- Performance monitoring

### **Analytics:**
- Prediction accuracy by user
- Most predicted outcomes
- League-specific trends
- User behavior patterns

---

## 🔮 **Future Enhancements**

### **Phase 2 Features:**
- Real-time notifications
- Mobile app integration
- Social features (sharing predictions)
- Advanced statistics dashboard

### **Phase 3 Features:**
- Machine learning predictions
- Live match updates
- Betting integration
- Advanced tournament formats

### **Phase 4 Features:**
- Multi-sport support
- International leagues
- Advanced analytics
- AI-powered insights

---

## 📚 **Implementation Status**

- [x] Database models (Prediction, Match, Team)
- [x] Service layer (PredictionPostgres)
- [x] API endpoints (CRUD operations)
- [x] Authentication integration
- [x] Input validation (Pydantic schemas)
- [x] Error handling and logging
- [x] Admin endpoints
- [x] Score calculation logic
- [ ] Unit tests
- [ ] Integration tests
- [ ] Performance optimization
- [ ] Caching implementation
- [ ] Documentation completion

**The Prediction System is ready for implementation and testing!** 🎉
