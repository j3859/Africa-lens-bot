import sys
sys.path.insert(0, r"C:\Users\muchk\Desktop\fb bot1")

from utils.database import Database

db = Database()

# New sources to add
new_sources = [
    # EGYPT (3)
    {
        "name": "Egypt Today",
        "url": "https://www.egypttoday.com",
        "source_type": "scrape",
        "country": "Egypt",
        "country_code": "EG",
        "language": "english",
        "niche": "politics",
        "priority": 1,
        "is_active": True
    },
    {
        "name": "Ahram Online",
        "url": "https://english.ahram.org.eg",
        "source_type": "scrape",
        "country": "Egypt",
        "country_code": "EG",
        "language": "english",
        "niche": "politics",
        "priority": 1,
        "is_active": True
    },
    {
        "name": "Egypt Independent",
        "url": "https://egyptindependent.com",
        "source_type": "scrape",
        "country": "Egypt",
        "country_code": "EG",
        "language": "english",
        "niche": "politics",
        "priority": 1,
        "is_active": True
    },
    
    # ALGERIA (3)
    {
        "name": "TSA Algerie",
        "url": "https://www.tsa-algerie.com",
        "source_type": "scrape",
        "country": "Algeria",
        "country_code": "DZ",
        "language": "french",
        "niche": "politics",
        "priority": 1,
        "is_active": True
    },
    {
        "name": "Algerie 360",
        "url": "https://www.algerie360.com",
        "source_type": "scrape",
        "country": "Algeria",
        "country_code": "DZ",
        "language": "french",
        "niche": "politics",
        "priority": 1,
        "is_active": True
    },
    {
        "name": "Algeria Press Service",
        "url": "https://www.aps.dz/en",
        "source_type": "scrape",
        "country": "Algeria",
        "country_code": "DZ",
        "language": "english",
        "niche": "politics",
        "priority": 1,
        "is_active": True
    },
    
    # KENYA (2 more)
    {
        "name": "The Star Kenya",
        "url": "https://www.the-star.co.ke",
        "source_type": "scrape",
        "country": "Kenya",
        "country_code": "KE",
        "language": "english",
        "niche": "politics",
        "priority": 1,
        "is_active": True
    },
    {
        "name": "Citizen Digital",
        "url": "https://www.citizen.digital",
        "source_type": "scrape",
        "country": "Kenya",
        "country_code": "KE",
        "language": "english",
        "niche": "politics",
        "priority": 1,
        "is_active": True
    },
    
    # TANZANIA (neighbor)
    {
        "name": "The Citizen Tanzania",
        "url": "https://www.thecitizen.co.tz",
        "source_type": "scrape",
        "country": "Tanzania",
        "country_code": "TZ",
        "language": "english",
        "niche": "politics",
        "priority": 2,
        "is_active": True
    },
    
    # TUNISIA (neighbor for Algeria/Morocco)
    {
        "name": "Tunisie Numerique",
        "url": "https://www.tunisienumerique.com",
        "source_type": "scrape",
        "country": "Tunisia",
        "country_code": "TN",
        "language": "french",
        "niche": "politics",
        "priority": 2,
        "is_active": True
    },
    
    # BOTSWANA (neighbor for South Africa)
    {
        "name": "Mmegi Botswana",
        "url": "https://www.mmegi.bw",
        "source_type": "scrape",
        "country": "Botswana",
        "country_code": "BW",
        "language": "english",
        "niche": "politics",
        "priority": 2,
        "is_active": True
    },
    
    # CAMEROON (neighbor for Nigeria)
    {
        "name": "Cameroon Tribune",
        "url": "https://www.cameroon-tribune.cm",
        "source_type": "scrape",
        "country": "Cameroon",
        "country_code": "CM",
        "language": "french",
        "niche": "politics",
        "priority": 2,
        "is_active": True
    },
]

print("="*60)
print("ADDING NEW SOURCES TO DATABASE")
print("="*60)

added = 0
skipped = 0

for source in new_sources:
    try:
        # Check if source already exists
        existing = db.client.table("sources").select("id").eq("name", source["name"]).execute()
        
        if existing.data and len(existing.data) > 0:
            print(f"  ⏭️  {source['name']} - Already exists")
            skipped += 1
        else:
            db.client.table("sources").insert(source).execute()
            print(f"  ✅ {source['name']} ({source['country']}) - Added")
            added += 1
            
    except Exception as e:
        print(f"  ❌ {source['name']} - Error: {e}")

print(f"\n{'='*60}")
print(f"Added: {added} | Skipped: {skipped}")
print(f"{'='*60}")

# Show total sources by country
print("\nSOURCES BY COUNTRY:")
result = db.client.table("sources").select("country").eq("is_active", True).execute()
countries = {}
for s in result.data:
    c = s["country"]
    countries[c] = countries.get(c, 0) + 1

for country, count in sorted(countries.items(), key=lambda x: -x[1]):
    print(f"  {country}: {count}")