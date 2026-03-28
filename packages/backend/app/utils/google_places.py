"""Google Places API integration utilities."""

import httpx
from typing import Any
from app.config import settings


class GooglePlacesService:
    """Service for interacting with Google Places API (New)."""

    BASE_URL = "https://places.googleapis.com/v1"

    def __init__(self, api_key: str | None = None):
        """Initialize the Google Places service.

        Args:
            api_key: Google Places API key (defaults to settings.GOOGLE_PLACES_API_KEY)
        """
        self.api_key = api_key or settings.GOOGLE_PLACES_API_KEY
        if not self.api_key:
            raise ValueError("Google Places API key is required")

    async def search_places(
        self,
        query: str,
        location: dict[str, float] | None = None,
        radius: int = 50000,
        language: str = "ja",
    ) -> list[dict[str, Any]]:
        """Search for places using Text Search.

        Args:
            query: Search query (e.g., "カフェ 渋谷")
            location: Optional location restriction {"lat": 35.6812, "lng": 139.7671}
            radius: Search radius in meters (default 50000m = 50km)
            language: Language code (default "ja" for Japanese)

        Returns:
            List of place results with basic info
        """
        url = f"{self.BASE_URL}/places:searchText"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress,places.location,places.rating,places.types",
        }

        body = {
            "textQuery": query,
            "languageCode": language,
        }

        # Default to Tokyo if no location specified
        if location is None:
            location = {"lat": 35.6812, "lng": 139.7671}  # Tokyo Station

        # Use locationBias for geographic filtering (locationRestriction not supported for Text Search)
        body["locationBias"] = {
            "circle": {
                "center": {
                    "latitude": location["lat"],
                    "longitude": location["lng"],
                },
                "radius": radius,
            }
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        # Transform response to simplified format
        places = []
        for place in data.get("places", []):
            places.append({
                "place_id": place.get("id", ""),
                "name": place.get("displayName", {}).get("text", ""),
                "address": place.get("formattedAddress", ""),
                "lat": place.get("location", {}).get("latitude"),
                "lng": place.get("location", {}).get("longitude"),
                "rating": place.get("rating"),
                "types": place.get("types", []),
            })

        return places

    async def get_place_details(self, place_id: str, language: str = "ja") -> dict[str, Any]:
        """Get detailed information about a specific place.

        Args:
            place_id: Google Place ID (from search results)
            language: Language code (default "ja" for Japanese)

        Returns:
            Detailed place information
        """
        url = f"{self.BASE_URL}/places/{place_id}"

        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": (
                "id,displayName,formattedAddress,location,rating,"
                "userRatingCount,types,websiteUri,photos,nationalPhoneNumber,"
                "internationalPhoneNumber,googleMapsUri,priceLevel,regularOpeningHours"
            ),
            "X-Goog-FieldMask-Language": language,
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            data = response.json()

        # Extract photo URLs if available
        photos = []
        if "photos" in data:
            for photo in data["photos"][:5]:  # Limit to 5 photos
                photo_name = photo.get("name", "")
                if photo_name:
                    # Photo URL format: https://places.googleapis.com/v1/{photo_name}/media?key={API_KEY}&maxHeightPx=400&maxWidthPx=400
                    photo_url = f"https://places.googleapis.com/v1/{photo_name}/media?key={self.api_key}&maxHeightPx=400&maxWidthPx=400"
                    photos.append(photo_url)

        # Transform to simplified format
        place_details = {
            "place_id": data.get("id", ""),
            "name": data.get("displayName", {}).get("text", ""),
            "address": data.get("formattedAddress", ""),
            "lat": data.get("location", {}).get("latitude"),
            "lng": data.get("location", {}).get("longitude"),
            "rating": data.get("rating"),
            "user_ratings_total": data.get("userRatingCount"),
            "types": data.get("types", []),
            "website": data.get("websiteUri"),
            "phone_number": data.get("nationalPhoneNumber") or data.get("internationalPhoneNumber"),
            "google_maps_url": data.get("googleMapsUri"),
            "price_level": data.get("priceLevel"),
            "opening_hours": data.get("regularOpeningHours", {}).get("weekdayDescriptions", []),
            "photos": photos,
        }

        return place_details


# Singleton instance
google_places_service = GooglePlacesService()
