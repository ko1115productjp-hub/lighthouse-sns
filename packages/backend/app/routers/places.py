"""Google Places API endpoints."""

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Any
import httpx

from app.utils.google_places import google_places_service

router = APIRouter(prefix="/places", tags=["Places"])


class PlaceSearchRequest(BaseModel):
    """Request schema for place search."""

    query: str = Field(..., min_length=1, max_length=200, description="Search query")
    location: dict[str, float] | None = Field(
        None,
        description="Optional location bias (e.g., {'lat': 35.6812, 'lng': 139.7671})",
    )
    radius: int = Field(
        50000, ge=100, le=50000, description="Search radius in meters (100m - 50km)"
    )


class PlaceSearchResult(BaseModel):
    """Response schema for place search result."""

    place_id: str
    name: str
    address: str
    lat: float | None = None
    lng: float | None = None
    rating: float | None = None
    types: list[str] = Field(default_factory=list)


class PlaceDetailsResponse(BaseModel):
    """Response schema for detailed place information."""

    place_id: str
    name: str
    address: str
    lat: float | None = None
    lng: float | None = None
    rating: float | None = None
    user_ratings_total: int | None = None
    types: list[str] = Field(default_factory=list)
    website: str | None = None
    phone_number: str | None = None
    google_maps_url: str | None = None
    price_level: str | None = None
    opening_hours: list[str] = Field(default_factory=list)
    photos: list[str] = Field(default_factory=list)


@router.post("/search", response_model=list[PlaceSearchResult])
async def search_places(request: PlaceSearchRequest) -> list[PlaceSearchResult]:
    """
    Search for places using Google Places API Text Search.

    Args:
        request: Search request parameters

    Returns:
        List of matching places

    Raises:
        HTTPException: If API call fails
    """
    try:
        results = await google_places_service.search_places(
            query=request.query,
            location=request.location,
            radius=request.radius,
        )

        return [PlaceSearchResult(**place) for place in results]

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search places: {str(e)}",
        )


@router.get("/{place_id}", response_model=PlaceDetailsResponse)
async def get_place_details(place_id: str) -> PlaceDetailsResponse:
    """
    Get detailed information about a specific place.

    Args:
        place_id: Google Place ID

    Returns:
        Detailed place information

    Raises:
        HTTPException: If place not found or API call fails
    """
    try:
        details = await google_places_service.get_place_details(place_id)
        return PlaceDetailsResponse(**details)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Place not found",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch place details: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch place details: {str(e)}",
        )
