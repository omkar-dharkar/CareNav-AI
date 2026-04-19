"""
Agent 2: Hospital Finder Agent.

Finds nearby care facilities using Google Places API (New). Browser/device
coordinates are preferred when the custom UI provides them; IP lookup is only a
fallback for local debugging or denied location access.
"""

import os
from typing import Optional, Tuple

import requests
from dotenv import load_dotenv
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from .config import config
from .prompt import HOSPITAL_FINDER_PROMPT

# Load environment variables from .env file
load_dotenv()


def get_location_from_ip() -> Tuple[Optional[float], Optional[float], Optional[str]]:
    """Auto-detect user location via IP address."""
    try:
        ipinfo_resp = requests.get("https://ipinfo.io/json", timeout=10)
        ipinfo_resp.raise_for_status()
        data = ipinfo_resp.json()

        loc = data.get("loc", "")  # format: "lat,long"
        if loc:
            latitude, longitude = map(float, loc.split(","))
            city = data.get("city", "Unknown City")
            region = data.get("region", "Unknown Region")
            location_str = f"{city}, {region}"
            return latitude, longitude, location_str

    except Exception as e:
        print(f"Failed to auto-detect location: {e}")

    return None, None, None


def _format_open_status(place: dict) -> str:
    opening_hours = place.get("regularOpeningHours") or {}
    open_now = opening_hours.get("openNow")
    if open_now is True:
        return "Open now"
    if open_now is False:
        return "Closed now"
    return "Status unknown"


def _place_name(place: dict) -> str:
    display_name = place.get("displayName") or {}
    return display_name.get("text", "").strip()


def _care_type_config(care_type: str) -> Tuple[list[str], str, str]:
    normalized = (care_type or "emergency").strip().lower().replace("-", "_").replace(" ", "_")
    configs = {
        "emergency": (
            ["hospital", "general_hospital", "medical_center"],
            "emergency departments and hospitals",
            "Call 911 first for possible life-threatening symptoms. Do not delay emergency care to check insurance.",
        ),
        "hospital": (
            ["hospital", "general_hospital", "medical_center"],
            "hospitals and medical centers",
            "For emergencies, call 911 first. For planned care, call ahead to verify services and insurance.",
        ),
        "urgent_care": (
            ["medical_clinic", "medical_center"],
            "urgent care and walk-in clinics",
            "Urgent care is for non-life-threatening issues. Call 911 for chest pain, severe breathing trouble, stroke symptoms, or major injury.",
        ),
        "primary_care": (
            ["doctor", "medical_clinic"],
            "primary care clinics and doctors",
            "Primary care is best for non-emergency follow-up and routine care.",
        ),
        "pharmacy": (
            ["pharmacy", "drugstore"],
            "pharmacies",
            "Pharmacists can answer medication questions, but call 911 for emergencies.",
        ),
        "lab": (
            ["medical_lab"],
            "medical labs",
            "Labs may require clinician orders and appointments. Call ahead before going.",
        ),
    }
    return configs.get(normalized, configs["emergency"])


def _looks_like_care_facility(place: dict, included_types: list[str]) -> bool:
    """Reduce irrelevant Places results while keeping legitimate medical facilities."""
    place_types = set(place.get("types") or [])
    primary_type = place.get("primaryType")
    if primary_type:
        place_types.add(primary_type)

    name = _place_name(place).lower()
    facility_terms = (
        "hospital",
        "medical",
        "health",
        "clinic",
        "emergency",
        "urgent",
        "care",
        "pharmacy",
        "laboratory",
        "lab",
    )
    has_facility_term = any(term in name for term in facility_terms)
    has_contact_signal = any(
        place.get(field)
        for field in ("nationalPhoneNumber", "websiteUri", "rating")
    )

    exact_facility_types = {"general_hospital", "hospital", "medical_lab", "pharmacy"}
    if place_types.intersection(exact_facility_types):
        return has_facility_term or has_contact_signal

    if place_types.intersection(included_types):
        return has_facility_term or has_contact_signal

    return has_facility_term and has_contact_signal


def _insurance_note(insurance_provider: str, care_label: str) -> str:
    insurance = (insurance_provider or "").strip()
    requested = insurance if insurance else "Medicaid, UnitedHealthcare, or any insurance plan"
    return (
        f"Insurance note: Google Places does not verify whether these {care_label} "
        f"accept {requested}. Before non-emergency care, call the facility and your insurer "
        "to confirm: 1) they accept your exact plan, 2) the specific location/provider is "
        "in-network, 3) prior authorization or referral rules, and 4) estimated out-of-pocket cost. "
        "For possible emergencies, call 911 first and do not delay care for insurance checks."
    )


def find_nearby_hospitals(
    radius: int = 5000,
    care_type: str = "emergency",
    insurance_provider: str = "",
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    location_label: str = "",
) -> str:
    """
    Find nearby care facilities using Google Places API (New).

    Args:
        radius: Search radius in meters. Defaults to 5000m, or 5km.
        care_type: Type of care to search for. Options include emergency, hospital,
            urgent_care, primary_care, pharmacy, and lab.
        insurance_provider: Optional insurance plan name the user wants to verify,
            such as Medicaid or UnitedHealthcare.
        latitude: Optional browser/device latitude from the user interface.
        longitude: Optional browser/device longitude from the user interface.
        location_label: Optional human-readable location label.

    Returns:
        Formatted list of nearby facilities with details.
    """
    try:
        lat = latitude
        lng = longitude
        location_str = (location_label or "").strip()
        location_source = "device location"

        if lat is not None and not -90 <= lat <= 90:
            lat = None
        if lng is not None and not -180 <= lng <= 180:
            lng = None

        if lat is None or lng is None:
            lat, lng, location_str = get_location_from_ip()
            location_source = "server IP fallback"

        if lat is None or lng is None:
            return (
                "Could not detect a usable location automatically. "
                "Please allow browser location access or enter a nearby city/ZIP code."
            )

        if not location_str:
            location_str = f"{lat:.4f}, {lng:.4f}"

        api_key = os.getenv("GOOGLE_PLACES_API_KEY")
        if not api_key:
            return (
                "Google Places API key not found. "
                "Please set GOOGLE_PLACES_API_KEY environment variable."
            )

        included_types, care_label, care_guidance = _care_type_config(care_type)
        places_url = "https://places.googleapis.com/v1/places:searchNearby"
        places_headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "places.displayName,"
                "places.formattedAddress,"
                "places.nationalPhoneNumber,"
                "places.rating,"
                "places.websiteUri,"
                "places.googleMapsUri,"
                "places.regularOpeningHours,"
                "places.primaryType,"
                "places.types,"
                "places.businessStatus"
            ),
        }
        places_payload = {
            "includedTypes": included_types,
            "maxResultCount": 10,
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lng,
                    },
                    "radius": radius,
                }
            },
        }

        places_response = requests.post(
            places_url,
            headers=places_headers,
            json=places_payload,
            timeout=15,
        )

        try:
            places_data = places_response.json()
        except ValueError:
            return (
                f"Google Places API returned HTTP {places_response.status_code}, "
                "but the response was not valid JSON."
            )

        if places_response.status_code >= 400:
            error = places_data.get("error", {})
            message = error.get("message", "Unknown error")
            status = error.get("status", places_response.status_code)
            return (
                f"Google Places API error ({status}): {message}\n\n"
                "Please confirm Places API (New) is enabled for this API key."
            )

        filtered_places = []
        for place in places_data.get("places", []):
            if place.get("businessStatus") == "CLOSED_PERMANENTLY":
                continue
            if not _looks_like_care_facility(place, included_types):
                continue
            filtered_places.append(place)

        facilities = []
        for i, place in enumerate(filtered_places[:8], 1):
            facility_name = _place_name(place) or "Unknown facility"
            facility_text = f"""
**{i}. {facility_name}**
Address: {place.get("formattedAddress", "Address not available")}
Phone: {place.get("nationalPhoneNumber", "Phone not available")}
Rating: {place.get("rating", "No rating")}
Website: {place.get("websiteUri", "Website not available")}
Maps: {place.get("googleMapsUri", "Maps link not available")}
Status: {_format_open_status(place)}
"""
            facilities.append(facility_text)

        if not facilities:
            return (
                f"Location used: {location_str} ({location_source})\n\n"
                f"No {care_label} found in your area. You may need to expand your search radius."
            )

        response_text = f"""Your location: {location_str}
Location source: {location_source}
Search radius: {radius / 1000} km
Search focus: {care_label}
Found {len(facilities)} nearby options:

{chr(10).join(facilities)}

EMERGENCY: For medical emergencies in the United States, call **911** immediately.

Poison exposure or possible overdose: Call Poison Help at **1-800-222-1222**. If the person is unconscious, not breathing, seizing, or in immediate danger, call 911 first.

Services note: {care_guidance}

{_insurance_note(insurance_provider, care_label)}

Note: This information is for reference only. For emergencies, call 911 first instead of driving yourself."""

        return response_text

    except Exception as e:
        return f"Error finding hospitals: {str(e)}"


# Create FunctionTool wrapper for proper ADK compatibility
find_hospitals_tool = FunctionTool(func=find_nearby_hospitals)

# Create the Hospital Finder Agent with auto-location detection
hospital_finder_agent = LlmAgent(
    name="hospital_finder",
    model=config.DEFAULT_MODEL,
    description=(
        "Medical facility locator that uses browser/device coordinates when supplied and "
        "finds nearby hospitals using Google Places API. Provides hospital "
        "information including addresses, phone numbers, ratings, and hours for U.S. users."
    ),
    instruction=HOSPITAL_FINDER_PROMPT,
    tools=[find_hospitals_tool],
)
