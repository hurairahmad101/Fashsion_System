-- ===============================
-- GlamourGPT Database Schema
-- Database: fashion_db
-- ===============================

-- USERS TABLE
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    email VARCHAR(150) UNIQUE,
    body_type VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CHAT HISTORY (AI AGENT MEMORY)
CREATE TABLE chat_history (
    chat_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    user_query TEXT,
    ai_response TEXT,
    model_used VARCHAR(50) DEFAULT 'mistral',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- OUTFIT RECOMMENDATIONS
CREATE TABLE outfit_recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    body_type VARCHAR(50),
    weather VARCHAR(50),
    occasion VARCHAR(100),
    recommended_items TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ACCESSORY SUGGESTIONS
CREATE TABLE accessory_suggestions (
    accessory_id SERIAL PRIMARY KEY,
    recommendation_id INT REFERENCES outfit_recommendations(recommendation_id) ON DELETE CASCADE,
    accessories TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- FABRIC & COLOR ANALYSIS
CREATE TABLE fabric_analysis (
    analysis_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    fabric_type VARCHAR(100),
    dominant_color VARCHAR(100),
    suggested_use VARCHAR(100),
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VIRTUAL TRY-ON RESULTS
CREATE TABLE virtual_tryon (
    tryon_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    body_detected BOOLEAN,
    tryon_result TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EVENTS (EVENT PLANNER)
CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    user_id INT REFERENCES users(user_id) ON DELETE CASCADE,
    event_name VARCHAR(150),
    event_date DATE,
    location VARCHAR(100),
    weather_forecast VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- EVENT-BASED STYLE SUGGESTIONS
CREATE TABLE event_style_suggestions (
    suggestion_id SERIAL PRIMARY KEY,
    event_id INT REFERENCES events(event_id) ON DELETE CASCADE,
    outfit_style TEXT,
    color_palette TEXT,
    celebrity_inspiration TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- CELEBRITY FASHION TRENDS (FOR POWER BI)
CREATE TABLE celebrity_trends (
    trend_id SERIAL PRIMARY KEY,
    celebrity_name VARCHAR(100),
    outfit_type VARCHAR(100),
    dominant_colors VARCHAR(100),
    trend_score INT,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- SYSTEM LOGS (OPTIONAL – GOOD FOR FYP)
CREATE TABLE system_logs (
    log_id SERIAL PRIMARY KEY,
    module_name VARCHAR(100),
    action TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
