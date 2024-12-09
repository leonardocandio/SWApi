import azure.functions as func
import logging
import requests
from database import get_db, engine
from models import Base, Film, Person, Planet, Species, Vehicle, Starship
import json
from typing import Dict, Any

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

BASE_URL = "https://swapi.dev/api"

def extract_id_from_url(url: str) -> int:
    """Extract the ID from a SWAPI URL."""
    return int(url.rstrip('/').split('/')[-1])

def fetch_all_data(endpoint: str) -> list:
    """Fetch all data from a SWAPI endpoint."""
    results = []
    url = f"{BASE_URL}/{endpoint}"
    
    while url:
        response = requests.get(url)
        data = response.json()
        results.extend(data['results'])
        url = data.get('next')
    
    return results

def process_relationships(data: Dict[str, Any], db) -> Dict[str, Any]:
    """Process and clean up relationship data."""
    processed = data.copy()
    
    # Convert URLs to IDs
    if 'homeworld' in processed and processed['homeworld']:
        processed['homeworld_id'] = extract_id_from_url(processed['homeworld'])
    
    # Remove relationship URLs as we'll handle them separately
    for key in ['films', 'people', 'characters', 'planets', 'species', 'vehicles', 'starships', 'residents', 'homeworld', 'pilots']:
        if key in processed:
            del processed[key]
    
    return processed

@app.route(route="scrape_swapi", methods=["GET", "POST"], auth_level=func.AuthLevel.ADMIN)
def scrape_swapi(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Starting SWAPI data scraping')
    
    try:
        # Initialize database
        Base.metadata.create_all(bind=engine)
        db = next(get_db())
        
        # Fetch and store planets first (as they're referenced by other entities)
        planets_data = fetch_all_data('planets')
        for planet_data in planets_data:
            planet_id = extract_id_from_url(planet_data['url'])
            processed_data = process_relationships(planet_data, db)
            planet = Planet(id=planet_id, **processed_data)
            db.merge(planet)
        db.commit()
        
        # Fetch and store people
        people_data = fetch_all_data('people')
        for person_data in people_data:
            person_id = extract_id_from_url(person_data['url'])
            processed_data = process_relationships(person_data, db)
            person = Person(id=person_id, **processed_data)
            
            # Handle relationships
            for film_url in person_data.get('films', []):
                film_id = extract_id_from_url(film_url)
                film = db.query(Film).get(film_id)
                if film:
                    person.films.append(film)
            
            db.merge(person)
        db.commit()
        
        # Fetch and store films
        films_data = fetch_all_data('films')
        for film_data in films_data:
            film_id = extract_id_from_url(film_data['url'])
            processed_data = process_relationships(film_data, db)
            film = Film(id=film_id, **processed_data)
            db.merge(film)
        db.commit()
        
        # Fetch and store species
        species_data = fetch_all_data('species')
        for species_data in species_data:
            species_id = extract_id_from_url(species_data['url'])
            processed_data = process_relationships(species_data, db)
            species = Species(id=species_id, **processed_data)
            db.merge(species)
        db.commit()
        
        # Fetch and store vehicles
        vehicles_data = fetch_all_data('vehicles')
        for vehicle_data in vehicles_data:
            vehicle_id = extract_id_from_url(vehicle_data['url'])
            processed_data = process_relationships(vehicle_data, db)
            vehicle = Vehicle(id=vehicle_id, **processed_data)
            db.merge(vehicle)
        db.commit()
        
        # Fetch and store starships
        starships_data = fetch_all_data('starships')
        for starship_data in starships_data:
            starship_id = extract_id_from_url(starship_data['url'])
            processed_data = process_relationships(starship_data, db)
            starship = Starship(id=starship_id, **processed_data)
            db.merge(starship)
        db.commit()
        
        return func.HttpResponse(
            "SWAPI data successfully scraped and stored in the database.",
            status_code=200
        )
        
    except Exception as e:
        logging.error(f"Error occurred while scraping SWAPI: {str(e)}")
        return func.HttpResponse(
            f"Error occurred while scraping SWAPI: {str(e)}",
            status_code=500
        )
    finally:
        db.close()
