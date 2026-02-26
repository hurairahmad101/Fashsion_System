from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    ForeignKey,
    TIMESTAMP
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from backend.database import Base


# =========================
# USERS
# =========================
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(150), unique=True, index=True)
    body_type = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    recommendations = relationship("OutfitRecommendation", back_populates="user")
    fabrics = relationship("FabricAnalysis", back_populates="user")
    tryons = relationship("VirtualTryOn", back_populates="user")
    events = relationship("Event", back_populates="user")


# =========================
# CHAT HISTORY (AI AGENT MEMORY)
# =========================
class ChatHistory(Base):
    __tablename__ = "chat_history"

    chat_id = Column(Integer, primary_key=True, index=True)
    user_query = Column(Text)
    ai_response = Column(Text)
    model_used = Column(String(50), default="mistral")
    created_at = Column(TIMESTAMP, server_default=func.now())


# =========================
# OUTFIT RECOMMENDATIONS
# =========================
class OutfitRecommendation(Base):
    __tablename__ = "outfit_recommendations"

    recommendation_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    body_type = Column(String(50))
    weather = Column(String(50))
    occasion = Column(String(100))
    recommended_items = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="recommendations")
    accessories = relationship(
        "AccessorySuggestion",
        back_populates="recommendation",
        cascade="all, delete"
    )


# =========================
# ACCESSORY SUGGESTIONS
# =========================
class AccessorySuggestion(Base):
    __tablename__ = "accessory_suggestions"

    accessory_id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(
        Integer,
        ForeignKey("outfit_recommendations.recommendation_id", ondelete="CASCADE")
    )
    accessories = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    recommendation = relationship("OutfitRecommendation", back_populates="accessories")


# =========================
# FABRIC & COLOR ANALYSIS
# =========================
class FabricAnalysis(Base):
    __tablename__ = "fabric_analysis"

    analysis_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    fabric_type = Column(String(100))
    dominant_color = Column(String(100))
    suggested_use = Column(String(100))
    image_path = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="fabrics")


# =========================
# VIRTUAL TRY-ON
# =========================
class VirtualTryOn(Base):
    __tablename__ = "virtual_tryon"

    tryon_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    body_detected = Column(Boolean)
    tryon_result = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="tryons")


# =========================
# EVENTS
# =========================
class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"))
    event_name = Column(String(150))
    event_date = Column(Date)
    location = Column(String(100))
    weather_forecast = Column(String(50))
    created_at = Column(TIMESTAMP, server_default=func.now())

    user = relationship("User", back_populates="events")
    styles = relationship(
        "EventStyleSuggestion",
        back_populates="event",
        cascade="all, delete"
    )


# =========================
# EVENT STYLE SUGGESTIONS
# =========================
class EventStyleSuggestion(Base):
    __tablename__ = "event_style_suggestions"

    suggestion_id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.event_id", ondelete="CASCADE"))
    outfit_style = Column(Text)
    color_palette = Column(Text)
    celebrity_inspiration = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

    event = relationship("Event", back_populates="styles")


# =========================
# CELEBRITY FASHION TRENDS
# =========================
class CelebrityTrend(Base):
    __tablename__ = "celebrity_trends"

    trend_id = Column(Integer, primary_key=True, index=True)
    celebrity_name = Column(String(100))
    outfit_type = Column(String(100))
    dominant_colors = Column(String(100))
    trend_score = Column(Integer)
    collected_at = Column(TIMESTAMP, server_default=func.now())


# =========================
# SYSTEM LOGS
# =========================
class SystemLog(Base):
    __tablename__ = "system_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    module_name = Column(String(100))
    action = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
