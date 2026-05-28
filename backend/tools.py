import os
from datetime import datetime
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder
from kerykeion import AstrologicalSubject
from langchain_core.tools import tool

# ── Tool 1: Geocode Place ────────────────────────────────────
@tool
def geocode_place(place_name: str) -> dict:
    """Convert a place name to latitude, longitude and timezone."""
    try:
        geolocator = Nominatim(user_agent="astroagent")
        location = geolocator.geocode(place_name)
        if not location:
            return {"error": f"Could not find location: {place_name}"}

        tf = TimezoneFinder()
        timezone = tf.timezone_at(lat=location.latitude, lng=location.longitude)

        return {
            "place": place_name,
            "latitude": round(location.latitude, 4),
            "longitude": round(location.longitude, 4),
            "timezone": timezone
        }
    except Exception as e:
        return {"error": str(e)}


# ── Tool 2: Compute Birth Chart ──────────────────────────────
@tool
def compute_birth_chart(
    name: str,
    birth_date: str,
    birth_time: str,
    birth_place: str
) -> dict:
    """
    Compute a real birth chart using Swiss Ephemeris.
    birth_date format: YYYY-MM-DD
    birth_time format: HH:MM
    birth_place: city name e.g. 'Mumbai'
    """
    try:
        try:
            dt = datetime.strptime(birth_date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Use YYYY-MM-DD"}

        try:
            tm = datetime.strptime(birth_time, "%H:%M")
        except ValueError:
            return {"error": "Invalid time format. Use HH:MM"}

        geo = geocode_place.invoke({"place_name": birth_place})
        if "error" in geo:
            return geo

        subject = AstrologicalSubject(
            name=name,
            year=dt.year,
            month=dt.month,
            day=dt.day,
            hour=tm.hour,
            minute=tm.minute,
            city=birth_place,
            lat=geo["latitude"],
            lng=geo["longitude"],
            tz_str=geo["timezone"]
        )

        planets = {
            "Sun": f"{subject.sun.sign} at {round(subject.sun.position, 2)}°",
            "Moon": f"{subject.moon.sign} at {round(subject.moon.position, 2)}°",
            "Mercury": f"{subject.mercury.sign} at {round(subject.mercury.position, 2)}°",
            "Venus": f"{subject.venus.sign} at {round(subject.venus.position, 2)}°",
            "Mars": f"{subject.mars.sign} at {round(subject.mars.position, 2)}°",
            "Jupiter": f"{subject.jupiter.sign} at {round(subject.jupiter.position, 2)}°",
            "Saturn": f"{subject.saturn.sign} at {round(subject.saturn.position, 2)}°",
            "Ascendant": f"{subject.first_house.sign} at {round(subject.first_house.position, 2)}°",
        }

        return {
            "name": name,
            "birth_date": birth_date,
            "birth_time": birth_time,
            "birth_place": birth_place,
            "planets": planets
        }

    except Exception as e:
        return {"error": str(e)}


# ── Tool 3: Get Daily Transits ───────────────────────────────
@tool
def get_daily_transits(birth_date: str, birth_time: str, birth_place: str) -> dict:
    """Get today's planetary transits. If birth details are unknown, use birth_date='2000-01-01', birth_time='12:00', birth_place='Mumbai' as defaults."""
    try:
        now = datetime.now()

        geo = geocode_place.invoke({"place_name": birth_place})
        if "error" in geo:
            return geo

        today = AstrologicalSubject(
            name="Today",
            year=now.year,
            month=now.month,
            day=now.day,
            hour=now.hour,
            minute=now.minute,
            city=birth_place,
            lat=geo["latitude"],
            lng=geo["longitude"],
            tz_str=geo["timezone"]
        )

        transits = {
            "Sun": f"{today.sun.sign} at {round(today.sun.position, 2)}°",
            "Moon": f"{today.moon.sign} at {round(today.moon.position, 2)}°",
            "Mercury": f"{today.mercury.sign} at {round(today.mercury.position, 2)}°",
            "Venus": f"{today.venus.sign} at {round(today.venus.position, 2)}°",
            "Mars": f"{today.mars.sign} at {round(today.mars.position, 2)}°",
            "Jupiter": f"{today.jupiter.sign} at {round(today.jupiter.position, 2)}°",
            "Saturn": f"{today.saturn.sign} at {round(today.saturn.position, 2)}°",
        }

        return {
            "date": now.strftime("%Y-%m-%d"),
            "transits": transits
        }

    except Exception as e:
        return {"error": str(e)}


# ── Tool 4: Knowledge Lookup ─────────────────────────────────
@tool
def knowledge_lookup(query: str) -> str:
    """Look up astrology knowledge. Use for any question about zodiac signs, planets, houses, or astrological concepts. Input should be a simple text query like 'venus' or 'scorpio' or 'moon meaning'."""
    knowledge = {
        "aries": "Aries is the first sign, ruled by Mars. It represents energy, courage, and new beginnings. People with strong Aries placements are bold, pioneering, and action-oriented.",
        "taurus": "Taurus is ruled by Venus. It represents stability, material comfort, and sensuality. Taurus placements bring patience, persistence, and love of beauty.",
        "gemini": "Gemini is ruled by Mercury. It represents communication, curiosity, and adaptability. Gemini placements bring quick thinking and love of learning.",
        "cancer": "Cancer is ruled by the Moon. It represents emotion, home, and nurturing. Cancer placements bring deep sensitivity and strong intuition.",
        "leo": "Leo is ruled by the Sun. It represents creativity, leadership, and self-expression. Leo placements bring warmth, generosity, and confidence.",
        "virgo": "Virgo is ruled by Mercury. It represents analysis, service, and perfectionism. Virgo placements bring attention to detail and a desire to help.",
        "libra": "Libra is ruled by Venus. It represents balance, harmony, and relationships. Libra placements bring diplomacy, grace, and a strong sense of justice.",
        "scorpio": "Scorpio is ruled by Pluto and Mars. It represents transformation, depth, and intensity. Scorpio placements bring passion, mystery, and resilience.",
        "sagittarius": "Sagittarius is ruled by Jupiter. It represents expansion, philosophy, and adventure. Sagittarius placements bring optimism, freedom-seeking, and wisdom.",
        "capricorn": "Capricorn is ruled by Saturn. It represents discipline, ambition, and structure. Capricorn placements bring determination and long-term thinking.",
        "aquarius": "Aquarius is ruled by Uranus. It represents innovation, community, and humanitarianism. Aquarius placements bring originality and vision.",
        "pisces": "Pisces is ruled by Neptune. It represents imagination, compassion, and spirituality. Pisces placements bring empathy, creativity, and deep intuition.",
        "sun": "The Sun in astrology represents your core identity, ego, and life purpose. It shows how you shine and express yourself in the world.",
        "moon": "The Moon represents your emotions, instincts, and subconscious. It shows your emotional needs and how you nurture yourself and others.",
        "ascendant": "The Ascendant or Rising sign represents your outward personality and how others first perceive you. It is the mask you wear to the world.",
        "mercury": "Mercury represents communication, thinking, and learning style. It shows how you process and share information.",
        "venus": "Venus represents love, beauty, and values. It shows what you find attractive and how you relate to others in love.",
        "mars": "Mars represents energy, drive, and action. It shows how you pursue your desires and handle anger and conflict.",
        "jupiter": "Jupiter represents expansion, luck, and wisdom. It shows where you find growth, abundance, and opportunity in life.",
        "saturn": "Saturn represents discipline, karma, and life lessons. It shows where you face challenges that ultimately lead to mastery.",
    }

    query_lower = query.lower()
    for key, value in knowledge.items():
        if key in query_lower:
            return value

    return "Astrology is an ancient system of understanding cosmic influences on human life. Each planet and sign carries unique energy that shapes our personalities and life experiences. For specific interpretations, please ask about a particular planet, sign, or placement."


# ── Export all tools ─────────────────────────────────────────
tools = [geocode_place, compute_birth_chart, get_daily_transits, knowledge_lookup]