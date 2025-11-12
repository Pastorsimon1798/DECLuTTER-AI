#!/usr/bin/env python3
"""
Script to populate test resources for development/testing
"""
import asyncio
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.database import AsyncSessionLocal
from app.models.resource import ResourceListing
from app.services.geohash_service import GeohashService


# Sample test resources - Los Angeles area coordinates
TEST_RESOURCES = [
    {
        "name": "Community Food Pantry - Downtown LA",
        "category": "food",
        "subcategory": "food_pantry",
        "description": "Free food pantry serving the downtown community. Fresh produce, canned goods, and prepared meals available.",
        "location_address": "123 Main Street, Los Angeles, CA 90012",
        "location": {"lat": 34.0522, "lon": -118.2437},
        "phone": "+1-213-555-0101",
        "email": "info@communitypantry.org",
        "website": "https://communitypantry.org",
        "hours": {
            "monday": "9:00 AM - 5:00 PM",
            "tuesday": "9:00 AM - 5:00 PM",
            "wednesday": "9:00 AM - 5:00 PM",
            "thursday": "9:00 AM - 5:00 PM",
            "friday": "9:00 AM - 5:00 PM",
            "saturday": "10:00 AM - 2:00 PM",
            "sunday": "Closed"
        },
        "services": ["Food Distribution", "Fresh Produce", "Prepared Meals", "Nutrition Counseling"],
        "languages": ["en", "es"],
        "accessibility_features": ["Wheelchair Accessible", "Parking Available"],
        "population_tags": ["families", "seniors"],
        "is_community_contributed": True,
    },
    {
        "name": "Hope Shelter - Emergency Housing",
        "category": "shelter",
        "subcategory": "emergency_shelter",
        "description": "24/7 emergency shelter providing safe temporary housing for individuals and families experiencing homelessness.",
        "location_address": "456 Hope Avenue, Los Angeles, CA 90015",
        "location": {"lat": 34.0444, "lon": -118.2500},
        "phone": "+1-213-555-0202",
        "email": "info@hopeshelter.org",
        "website": "https://hopeshelter.org",
        "hours": {
            "monday": "24 hours",
            "tuesday": "24 hours",
            "wednesday": "24 hours",
            "thursday": "24 hours",
            "friday": "24 hours",
            "saturday": "24 hours",
            "sunday": "24 hours"
        },
        "services": ["Emergency Shelter", "Meals", "Case Management", "Hygiene Facilities"],
        "languages": ["en", "es"],
        "accessibility_features": ["Wheelchair Accessible", "ADA Compliant"],
        "population_tags": ["families", "veterans"],
        "is_community_contributed": True,
    },
    {
        "name": "Community Health Clinic",
        "category": "healthcare",
        "subcategory": "primary_care",
        "description": "Free and low-cost primary healthcare services including medical exams, vaccinations, and health screenings.",
        "location_address": "789 Health Boulevard, Los Angeles, CA 90020",
        "location": {"lat": 34.0689, "lon": -118.4452},
        "phone": "+1-213-555-0303",
        "email": "info@communityhealth.org",
        "website": "https://communityhealth.org",
        "hours": {
            "monday": "8:00 AM - 6:00 PM",
            "tuesday": "8:00 AM - 6:00 PM",
            "wednesday": "8:00 AM - 6:00 PM",
            "thursday": "8:00 AM - 6:00 PM",
            "friday": "8:00 AM - 6:00 PM",
            "saturday": "9:00 AM - 1:00 PM",
            "sunday": "Closed"
        },
        "services": ["Primary Care", "Vaccinations", "Health Screenings", "Prescription Assistance"],
        "languages": ["en", "es", "zh-CN"],
        "accessibility_features": ["Wheelchair Accessible", "Sign Language Available"],
        "population_tags": ["families", "seniors", "immigrants"],
        "is_community_contributed": True,
    },
    {
        "name": "Clothing Closet - Free Clothing",
        "category": "clothing_household",
        "subcategory": "clothing",
        "description": "Free clothing for all ages. Professional attire, casual wear, and seasonal items available.",
        "location_address": "321 Clothing Street, Los Angeles, CA 90011",
        "location": {"lat": 34.0089, "lon": -118.2583},
        "phone": "+1-213-555-0404",
        "email": "info@clothingcloset.org",
        "website": None,
        "hours": {
            "monday": "10:00 AM - 4:00 PM",
            "tuesday": "10:00 AM - 4:00 PM",
            "wednesday": "10:00 AM - 4:00 PM",
            "thursday": "10:00 AM - 4:00 PM",
            "friday": "10:00 AM - 4:00 PM",
            "saturday": "Closed",
            "sunday": "Closed"
        },
        "services": ["Free Clothing", "Professional Attire", "Seasonal Items"],
        "languages": ["en", "es"],
        "accessibility_features": ["Wheelchair Accessible"],
        "population_tags": ["families", "youth"],
        "is_community_contributed": True,
    },
    {
        "name": "Legal Aid Society",
        "category": "legal",
        "subcategory": "legal_aid",
        "description": "Free legal assistance for low-income individuals. Help with housing, immigration, family law, and more.",
        "location_address": "555 Justice Way, Los Angeles, CA 90013",
        "location": {"lat": 34.0505, "lon": -118.2542},
        "phone": "+1-213-555-0505",
        "email": "info@legalaidla.org",
        "website": "https://legalaidla.org",
        "hours": {
            "monday": "9:00 AM - 5:00 PM",
            "tuesday": "9:00 AM - 5:00 PM",
            "wednesday": "9:00 AM - 5:00 PM",
            "thursday": "9:00 AM - 5:00 PM",
            "friday": "9:00 AM - 5:00 PM",
            "saturday": "Closed",
            "sunday": "Closed"
        },
        "services": ["Legal Consultation", "Housing Law", "Immigration Services", "Family Law"],
        "languages": ["en", "es"],
        "accessibility_features": ["Wheelchair Accessible"],
        "population_tags": ["immigrants", "families"],
        "is_community_contributed": True,
    },
    {
        "name": "Financial Assistance Center",
        "category": "financial",
        "subcategory": "financial_assistance",
        "description": "Help with utility bills, rent assistance, and benefits enrollment. Financial counseling available.",
        "location_address": "777 Finance Drive, Los Angeles, CA 90014",
        "location": {"lat": 34.0417, "lon": -118.2514},
        "phone": "+1-213-555-0606",
        "email": "info@financialaid.org",
        "website": "https://financialaid.org",
        "hours": {
            "monday": "8:00 AM - 5:00 PM",
            "tuesday": "8:00 AM - 5:00 PM",
            "wednesday": "8:00 AM - 5:00 PM",
            "thursday": "8:00 AM - 5:00 PM",
            "friday": "8:00 AM - 5:00 PM",
            "saturday": "Closed",
            "sunday": "Closed"
        },
        "services": ["Utility Assistance", "Rent Assistance", "Benefits Enrollment", "Financial Counseling"],
        "languages": ["en", "es"],
        "accessibility_features": ["Wheelchair Accessible"],
        "population_tags": ["families", "seniors"],
        "is_community_contributed": True,
    },
    {
        "name": "Job Training Center",
        "category": "employment_education",
        "subcategory": "job_training",
        "description": "Free job training programs, resume help, and career counseling. Computer skills and certification programs available.",
        "location_address": "888 Career Path, Los Angeles, CA 90016",
        "location": {"lat": 34.0522, "lon": -118.3526},
        "phone": "+1-213-555-0707",
        "email": "info@jobtraining.org",
        "website": "https://jobtraining.org",
        "hours": {
            "monday": "9:00 AM - 6:00 PM",
            "tuesday": "9:00 AM - 6:00 PM",
            "wednesday": "9:00 AM - 6:00 PM",
            "thursday": "9:00 AM - 6:00 PM",
            "friday": "9:00 AM - 6:00 PM",
            "saturday": "10:00 AM - 2:00 PM",
            "sunday": "Closed"
        },
        "services": ["Job Training", "Resume Help", "Career Counseling", "Computer Skills"],
        "languages": ["en", "es"],
        "accessibility_features": ["Wheelchair Accessible"],
        "population_tags": ["youth", "immigrants"],
        "is_community_contributed": True,
    },
    {
        "name": "Community Transit Assistance",
        "category": "transportation",
        "subcategory": "transit_assistance",
        "description": "Free or discounted transit passes. Transportation assistance for medical appointments and job interviews.",
        "location_address": "999 Transit Plaza, Los Angeles, CA 90017",
        "location": {"lat": 34.0556, "lon": -118.2667},
        "phone": "+1-213-555-0808",
        "email": "info@transitassist.org",
        "website": "https://transitassist.org",
        "hours": {
            "monday": "8:00 AM - 5:00 PM",
            "tuesday": "8:00 AM - 5:00 PM",
            "wednesday": "8:00 AM - 5:00 PM",
            "thursday": "8:00 AM - 5:00 PM",
            "friday": "8:00 AM - 5:00 PM",
            "saturday": "Closed",
            "sunday": "Closed"
        },
        "services": ["Transit Passes", "Medical Transportation", "Job Interview Rides"],
        "languages": ["en", "es"],
        "accessibility_features": ["Wheelchair Accessible Vehicles"],
        "population_tags": ["seniors", "disability_accessible"],
        "is_community_contributed": True,
    },
    {
        "name": "LGBTQ+ Community Center",
        "category": "healthcare",
        "subcategory": "mental_health",
        "description": "Support services, counseling, and resources for LGBTQ+ community members. Safe space and peer support groups.",
        "location_address": "111 Pride Avenue, Los Angeles, CA 90028",
        "location": {"lat": 34.0983, "lon": -118.3267},
        "phone": "+1-213-555-0909",
        "email": "info@lgbtqcenter.org",
        "website": "https://lgbtqcenter.org",
        "hours": {
            "monday": "10:00 AM - 8:00 PM",
            "tuesday": "10:00 AM - 8:00 PM",
            "wednesday": "10:00 AM - 8:00 PM",
            "thursday": "10:00 AM - 8:00 PM",
            "friday": "10:00 AM - 8:00 PM",
            "saturday": "12:00 PM - 6:00 PM",
            "sunday": "12:00 PM - 6:00 PM"
        },
        "services": ["Counseling", "Peer Support", "HIV Testing", "Youth Programs"],
        "languages": ["en", "es"],
        "accessibility_features": ["Wheelchair Accessible", "Gender-Neutral Restrooms"],
        "population_tags": ["lgbtq", "youth"],
        "is_community_contributed": True,
    },
    {
        "name": "Veterans Resource Center",
        "category": "financial",
        "subcategory": "veterans_services",
        "description": "Comprehensive services for veterans including benefits assistance, housing help, and peer support.",
        "location_address": "222 Veterans Way, Los Angeles, CA 90025",
        "location": {"lat": 34.0522, "lon": -118.4481},
        "phone": "+1-213-555-1010",
        "email": "info@vetscenter.org",
        "website": "https://vetscenter.org",
        "hours": {
            "monday": "8:00 AM - 5:00 PM",
            "tuesday": "8:00 AM - 5:00 PM",
            "wednesday": "8:00 AM - 5:00 PM",
            "thursday": "8:00 AM - 5:00 PM",
            "friday": "8:00 AM - 5:00 PM",
            "saturday": "Closed",
            "sunday": "Closed"
        },
        "services": ["Benefits Assistance", "Housing Help", "Peer Support", "Job Placement"],
        "languages": ["en"],
        "accessibility_features": ["Wheelchair Accessible"],
        "population_tags": ["veterans"],
        "is_community_contributed": True,
    },
]


async def populate_resources():
    """Populate database with test resources"""
    async with AsyncSessionLocal() as db:
        # Check if resources already exist
        result = await db.execute(select(ResourceListing))
        existing = result.scalars().all()
        
        if existing:
            print(f"⚠️  Found {len(existing)} existing resources. Skipping population.")
            print("   To repopulate, delete existing resources first.")
            return
        
        print("🌱 Populating test resources...")
        
        for resource_data in TEST_RESOURCES:
            # Extract location
            location = resource_data.pop("location")
            lat = location["lat"]
            lon = location["lon"]
            
            # Create resource
            resource = ResourceListing(
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
                hours=resource_data.get("hours"),
                services=resource_data.get("services", []),
                languages=resource_data.get("languages", []),
                accessibility_features=resource_data.get("accessibility_features", []),
                population_tags=resource_data.get("population_tags", []),
                is_community_contributed=resource_data.get("is_community_contributed", True),
                cached_at=datetime.now(timezone.utc),
                cache_expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            
            db.add(resource)
            print(f"  ✅ Added: {resource.name}")
        
        await db.commit()
        print(f"\n🎉 Successfully populated {len(TEST_RESOURCES)} test resources!")


if __name__ == "__main__":
    asyncio.run(populate_resources())

