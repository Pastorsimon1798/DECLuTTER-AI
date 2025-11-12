#!/usr/bin/env python3
"""
Script to populate database with REAL community resources from public sources
Uses OpenStreetMap Overpass API and other public datasets
"""
import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
from typing import List, Dict, Optional
import json

from app.database import AsyncSessionLocal
from app.models.resource import ResourceListing
from app.services.geohash_service import GeohashService


# Expanded Los Angeles area bounding box (includes surrounding counties)
LA_BOUNDS = {
    "south": 33.0,  # Extended south to include more of Orange County
    "north": 35.0,  # Extended north to include more of Ventura County
    "west": -119.0,  # Extended west
    "east": -117.0   # Extended east to include more of Inland Empire
}


async def fetch_osm_resources() -> List[Dict]:
    """Fetch real community resources from OpenStreetMap"""
    # Try multiple Overpass API servers
    overpass_servers = [
        "https://overpass-api.de/api/interpreter",
        "https://overpass.kumi.systems/api/interpreter",
        "https://lz4.overpass-api.de/api/interpreter",
    ]
    
    # Expanded query - fetch more resource types
    amenities = [
        "food_bank", "shelter", "community_centre", "clinic", "social_facility",
        "hospital", "pharmacy", "library", "school", "kindergarten",
        "place_of_worship", "charity", "public_building", "townhall"
    ]
    all_elements = []
    
    for amenity in amenities:
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="{amenity}"]({LA_BOUNDS["south"]},{LA_BOUNDS["west"]},{LA_BOUNDS["north"]},{LA_BOUNDS["east"]});
          way["amenity"="{amenity}"]({LA_BOUNDS["south"]},{LA_BOUNDS["west"]},{LA_BOUNDS["north"]},{LA_BOUNDS["east"]});
        );
        out center meta;
        """
        
        for server_url in overpass_servers:
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(server_url, data=query)
                    if response.status_code == 200:
                        data = response.json()
                        elements = data.get("elements", [])
                        all_elements.extend(elements)
                        print(f"  ✅ Fetched {len(elements)} {amenity} resources from {server_url}")
                        break  # Success, move to next amenity
                    elif response.status_code == 504:
                        print(f"  ⚠️  Timeout on {server_url} for {amenity}, trying next server...")
                        continue
                    else:
                        print(f"  ⚠️  Error {response.status_code} on {server_url} for {amenity}")
                        continue
            except Exception as e:
                print(f"  ⚠️  Error fetching {amenity} from {server_url}: {e}")
                continue
        else:
            print(f"  ❌ Failed to fetch {amenity} from all servers")
    
    return all_elements


def parse_osm_element(element: Dict) -> Optional[Dict]:
    """Parse OpenStreetMap element into resource format"""
    tags = element.get("tags", {})
    
    # Get name - try multiple fields
    name = (
        tags.get("name") or 
        tags.get("operator") or 
        tags.get("brand") or 
        tags.get("alt_name") or 
        tags.get("short_name") or 
        tags.get("official_name") or
        tags.get("ref") or
        None
    )
    
    # If still no name, try to build from address or skip
    if not name:
        # Try to use address as name if available
        addr_parts = []
        if tags.get("addr:housenumber") and tags.get("addr:street"):
            addr_parts.append(f"{tags.get('addr:housenumber')} {tags.get('addr:street')}")
        elif tags.get("addr:street"):
            addr_parts.append(tags.get("addr:street"))
        
        if addr_parts:
            name = addr_parts[0]
        else:
            # Skip resources with no identifying information
            return None
    
    # Get location
    if element.get("type") == "node":
        lat = element.get("lat")
        lon = element.get("lon")
    elif element.get("type") == "way":
        # For ways, use center if available
        if "center" in element:
            lat = element["center"].get("lat")
            lon = element["center"].get("lon")
        else:
            return None  # Skip if no center
    else:
        return None
    
    if not lat or not lon:
        return None
    
    # Determine category
    amenity = tags.get("amenity", "")
    category = "general"
    subcategory = None
    
    if amenity == "food_bank":
        category = "food"
        subcategory = "food_pantry"
    elif amenity == "shelter":
        category = "shelter"
        subcategory = "emergency_shelter"
    elif amenity == "clinic" or amenity == "hospital" or amenity == "pharmacy":
        category = "healthcare"
        if amenity == "hospital":
            subcategory = "hospital"
        elif amenity == "pharmacy":
            subcategory = "pharmacy"
        else:
            subcategory = "primary_care"
    elif amenity == "community_centre" or amenity == "community_center":
        category = "general"
        subcategory = "community_center"
    elif amenity == "library":
        category = "employment_education"
        subcategory = "library"
    elif amenity == "school" or amenity == "kindergarten":
        category = "employment_education"
        subcategory = "education"
    elif amenity == "place_of_worship":
        category = "general"
        subcategory = "place_of_worship"
    elif amenity == "charity":
        category = "general"
        subcategory = "charity"
    elif amenity == "public_building" or amenity == "townhall":
        category = "general"
        subcategory = "public_service"
    elif amenity == "social_facility":
        social_facility_type = tags.get("social_facility", "")
        if "shelter" in social_facility_type.lower():
            category = "shelter"
        elif "food" in social_facility_type.lower():
            category = "food"
        else:
            category = "general"
    
    # Build address (reuse the parts we might have used for name)
    address_parts = []
    if tags.get("addr:housenumber") and tags.get("addr:street"):
        street = f"{tags.get('addr:housenumber')} {tags.get('addr:street')}"
        # Only add to address if we didn't use it as the name
        if name != street:
            address_parts.append(street)
    elif tags.get("addr:street"):
        street = tags.get("addr:street")
        if name != street:
            address_parts.append(street)
    if tags.get("addr:city"):
        address_parts.append(tags.get("addr:city"))
    if tags.get("addr:state"):
        address_parts.append(tags.get("addr:state"))
    if tags.get("addr:postcode"):
        address_parts.append(tags.get("addr:postcode"))
    location_address = ", ".join(address_parts) if address_parts else None
    
    # Get contact info (truncate phone to 20 chars max)
    phone_raw = tags.get("phone") or tags.get("contact:phone")
    phone = phone_raw[:20] if phone_raw else None
    website = tags.get("website") or tags.get("contact:website")
    email = tags.get("email") or tags.get("contact:email")
    
    # Get description
    description = tags.get("description") or tags.get("note")
    
    # Build services list
    services = []
    if tags.get("operator"):
        services.append(f"Operated by {tags.get('operator')}")
    if tags.get("social_facility:for"):
        services.append(f"For: {tags.get('social_facility:for')}")
    
    # Accessibility
    accessibility_features = []
    if tags.get("wheelchair") == "yes":
        accessibility_features.append("Wheelchair Accessible")
    
    return {
        "external_id": f"osm_{element.get('type')}_{element.get('id')}",
        "name": name,
        "category": category,
        "subcategory": subcategory,
        "description": description,
        "location": {"lat": lat, "lon": lon},
        "location_address": location_address,
        "phone": phone,
        "email": email,
        "website": website,
        "services": services if services else None,
        "accessibility_features": accessibility_features if accessibility_features else None,
        "is_community_contributed": False,  # From OSM, not community-contributed
    }


async def fetch_211_la_resources() -> List[Dict]:
    """Fetch resources from 211 LA if available"""
    # Note: This would require API access to 211 LA
    # For now, return empty list - user can configure API key if they have access
    return []


async def clear_all_resources():
    """Delete all existing resources"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(ResourceListing))
        existing = result.scalars().all()
        
        if existing:
            print(f"🗑️  Deleting {len(existing)} existing resources...")
            await db.execute(delete(ResourceListing))
            await db.commit()
            print(f"✅ Deleted {len(existing)} resources")
        else:
            print("ℹ️  No existing resources to delete")


async def populate_real_resources(clear_existing=False):
    """Populate database with real resources from public sources"""
    if clear_existing:
        print("🧹 Clearing existing resources...")
        await clear_all_resources()
    else:
        print("➕ Adding more resources to existing database...")
    
    print("\n🌐 Fetching real community resources from OpenStreetMap...")
    osm_elements = await fetch_osm_resources()
    
    if not osm_elements:
        print("⚠️  No resources found from OpenStreetMap. Trying alternative sources...")
        return
    
    print(f"📦 Found {len(osm_elements)} resources from OpenStreetMap")
    
    async with AsyncSessionLocal() as db:
        added_count = 0
        skipped_count = 0
        
        for element in osm_elements:
            try:
                resource_data = parse_osm_element(element)
                if not resource_data:
                    skipped_count += 1
                    continue
                
                # Check if already exists
                result = await db.execute(
                    select(ResourceListing).where(
                        ResourceListing.external_id == resource_data["external_id"]
                    )
                )
                if result.scalar_one_or_none():
                    skipped_count += 1
                    continue
                
                # Extract location
                location = resource_data.pop("location")
                lat = location["lat"]
                lon = location["lon"]
                
                # Create resource
                resource = ResourceListing(
                    external_id=resource_data["external_id"],
                    name=resource_data["name"],
                    category=resource_data["category"],
                    subcategory=resource_data.get("subcategory"),
                    description=resource_data.get("description"),
                    location_address=resource_data.get("location_address"),
                    location_point=from_shape(Point(lon, lat), srid=4326),
                    location_geohash=GeohashService.encode_location(lat, lon, precision=7),
                    phone=resource_data.get("phone"),
                    email=resource_data.get("email"),
                    website=resource_data.get("website"),
                    services=resource_data.get("services", []),
                    accessibility_features=resource_data.get("accessibility_features", []),
                    is_community_contributed=resource_data.get("is_community_contributed", False),
                    cached_at=datetime.now(timezone.utc),
                    cache_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
                )
                
                db.add(resource)
                added_count += 1
                
                if added_count % 10 == 0:
                    print(f"  ✅ Processed {added_count} resources...")
                    
            except Exception as e:
                print(f"  ⚠️  Error processing resource: {e}")
                skipped_count += 1
                continue
        
        await db.commit()
        
        print(f"\n🎉 Successfully populated {added_count} real resources!")
        if skipped_count > 0:
            print(f"   (Skipped {skipped_count} duplicates or invalid entries)")


if __name__ == "__main__":
    asyncio.run(populate_real_resources())

