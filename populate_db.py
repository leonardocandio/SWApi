import requests
from database import get_db, create_tables
from models import Film, Person, Planet, Species, Vehicle, Starship
from sqlalchemy.exc import IntegrityError


def get_id_from_url(url):
    """Extract ID from SWAPI URL"""
    return int(url.split('/')[-2])


def get_all_data(endpoint):
    """Fetch all data from a SWAPI endpoint with pagination handling"""
    results = []
    url = f"https://swapi.py4e.com/api/{endpoint}/"
    
    while url:
        print(f"Fetching {url}")
        response = requests.get(url)
        data = response.json()
        results.extend(data["results"])
        url = data["next"]
    
    return results


def populate_db():
    # First ensure tables exist
    create_tables(drop=True)

    db = next(get_db())

    try:
        # Get all data from SWAPI
        print("Fetching data from SWAPI...")
        all_planets = get_all_data("planets")
        all_films = get_all_data("films")
        all_species = get_all_data("species")
        all_people = get_all_data("people")
        all_vehicles = get_all_data("vehicles")
        all_starships = get_all_data("starships")

        # Populate planets first since they're referenced by other models
        print("Populating planets...")
        for planet_data in all_planets:
            try:
                planet_id = get_id_from_url(planet_data["url"])
                if not db.get(Planet, planet_id):
                    planet = Planet(
                        id=planet_id,
                        name=planet_data["name"],
                        rotation_period=planet_data["rotation_period"],
                        orbital_period=planet_data["orbital_period"],
                        diameter=planet_data["diameter"],
                        climate=planet_data["climate"],
                        gravity=planet_data["gravity"],
                        terrain=planet_data["terrain"],
                        surface_water=planet_data["surface_water"],
                        population=planet_data["population"],
                        created=planet_data["created"],
                        edited=planet_data["edited"],
                        url=planet_data["url"]
                    )
                    db.add(planet)
                    db.flush()
            except Exception as e:
                print(f"Error adding planet {planet_data['name']}: {str(e)}")
                continue

        db.commit()

        # Populate films
        print("Populating films...")
        for film_data in all_films:
            film = Film(
                id=get_id_from_url(film_data["url"]),
                title=film_data["title"],
                episode_id=film_data["episode_id"],
                opening_crawl=film_data["opening_crawl"],
                director=film_data["director"],
                producer=film_data["producer"],
                release_date=film_data["release_date"],
                created=film_data["created"],
                edited=film_data["edited"],
                url=film_data["url"]
            )
            db.merge(film)
        db.commit()

        # Populate species
        print("Populating species...")
        for species_data in all_species:
            homeworld_id = None
            if species_data["homeworld"]:
                homeworld_id = get_id_from_url(species_data["homeworld"])

            species_obj = Species(
                id=get_id_from_url(species_data["url"]),
                name=species_data["name"],
                classification=species_data["classification"],
                designation=species_data["designation"],
                average_height=species_data["average_height"],
                skin_colors=species_data["skin_colors"],
                hair_colors=species_data["hair_colors"],
                eye_colors=species_data["eye_colors"],
                average_lifespan=species_data["average_lifespan"],
                homeworld_id=homeworld_id,
                language=species_data["language"],
                created=species_data["created"],
                edited=species_data["edited"],
                url=species_data["url"]
            )
            db.merge(species_obj)
        db.commit()

        # Populate people
        print("Populating people...")
        for person_data in all_people:
            homeworld_id = None
            if person_data["homeworld"]:
                homeworld_id = get_id_from_url(person_data["homeworld"])

            person = Person(
                id=get_id_from_url(person_data["url"]),
                name=person_data["name"],
                height=person_data["height"],
                mass=person_data["mass"],
                hair_color=person_data["hair_color"],
                skin_color=person_data["skin_color"],
                eye_color=person_data["eye_color"],
                birth_year=person_data["birth_year"],
                gender=person_data["gender"],
                homeworld_id=homeworld_id,
                created=person_data["created"],
                edited=person_data["edited"],
                url=person_data["url"]
            )
            db.merge(person)
        db.commit()

        # Populate vehicles
        print("Populating vehicles...")
        for vehicle_data in all_vehicles:
            vehicle = Vehicle(
                id=get_id_from_url(vehicle_data["url"]),
                name=vehicle_data["name"],
                model=vehicle_data["model"],
                manufacturer=vehicle_data["manufacturer"],
                cost_in_credits=vehicle_data["cost_in_credits"],
                length=vehicle_data["length"],
                max_atmosphering_speed=vehicle_data["max_atmosphering_speed"],
                crew=vehicle_data["crew"],
                passengers=vehicle_data["passengers"],
                cargo_capacity=vehicle_data["cargo_capacity"],
                consumables=vehicle_data["consumables"],
                vehicle_class=vehicle_data["vehicle_class"],
                created=vehicle_data["created"],
                edited=vehicle_data["edited"],
                url=vehicle_data["url"]
            )
            db.merge(vehicle)
        db.commit()

        # Populate starships
        print("Populating starships...")
        for starship_data in all_starships:
            starship = Starship(
                id=get_id_from_url(starship_data["url"]),
                name=starship_data["name"],
                model=starship_data["model"],
                manufacturer=starship_data["manufacturer"],
                cost_in_credits=starship_data["cost_in_credits"],
                length=starship_data["length"],
                max_atmosphering_speed=starship_data["max_atmosphering_speed"],
                crew=starship_data["crew"],
                passengers=starship_data["passengers"],
                cargo_capacity=starship_data["cargo_capacity"],
                consumables=starship_data["consumables"],
                hyperdrive_rating=starship_data["hyperdrive_rating"],
                MGLT=starship_data["MGLT"],
                starship_class=starship_data["starship_class"],
                created=starship_data["created"],
                edited=starship_data["edited"],
                url=starship_data["url"]
            )
            db.merge(starship)
        db.commit()

        # Handle many-to-many relationships
        print("Setting up relationships...")
        
        # Film relationships
        for film_data in all_films:
            film_id = get_id_from_url(film_data["url"])
            film = db.get(Film, film_id)
            
            if not film:
                print(f"Warning: Film with ID {film_id} not found in database")
                continue

            print(f"Processing relationships for film: {film.title}")

            try:
                # Characters (people)
                for char_url in film_data["characters"]:
                    char_id = get_id_from_url(char_url)
                    character = db.query(Person).get(char_id)
                    if character and character not in film.characters:
                        film.characters.append(character)

                # Planets
                for planet_url in film_data["planets"]:
                    planet_id = get_id_from_url(planet_url)
                    planet = db.query(Planet).get(planet_id)
                    if planet and planet not in film.planets:
                        film.planets.append(planet)

                # Species
                for species_url in film_data["species"]:
                    species_id = get_id_from_url(species_url)
                    species_obj = db.query(Species).get(species_id)
                    if species_obj and species_obj not in film.species:
                        film.species.append(species_obj)

                # Vehicles
                for vehicle_url in film_data["vehicles"]:
                    vehicle_id = get_id_from_url(vehicle_url)
                    vehicle = db.query(Vehicle).get(vehicle_id)
                    if vehicle and vehicle not in film.vehicles:
                        film.vehicles.append(vehicle)

                # Starships
                for starship_url in film_data["starships"]:
                    starship_id = get_id_from_url(starship_url)
                    starship = db.query(Starship).get(starship_id)
                    if starship and starship not in film.starships:
                        film.starships.append(starship)

                db.flush()  # Flush after each film's relationships
            except Exception as e:
                print(f"Error processing relationships for film {film_id}: {str(e)}")
                continue

        # Person relationships
        for person_data in all_people:
            person_id = get_id_from_url(person_data["url"])
            person = db.get(Person, person_id)
            
            if not person:
                print(f"Warning: Person with ID {person_id} not found in database")
                continue

            print(f"Processing relationships for person: {person.name}")

            try:
                # Species
                for species_url in person_data["species"]:
                    species_id = get_id_from_url(species_url)
                    species_obj = db.get(Species, species_id)
                    if species_obj and species_obj not in person.species:
                        person.species.append(species_obj)
                        db.merge(person)

                # Vehicles
                for vehicle_url in person_data["vehicles"]:
                    vehicle_id = get_id_from_url(vehicle_url)
                    vehicle = db.get(Vehicle, vehicle_id)
                    if vehicle and vehicle not in person.vehicles:
                        person.vehicles.append(vehicle)
                        db.merge(person)

                # Starships
                for starship_url in person_data["starships"]:
                    starship_id = get_id_from_url(starship_url)
                    starship = db.get(Starship, starship_id)
                    if starship and starship not in person.starships:
                        person.starships.append(starship)
                        db.merge(person)

                db.commit()  # Add a commit after each person's relationships are set
            except Exception as e:
                print(f"Error processing relationships for person {person_id}: {str(e)}")
                continue

        db.commit()
        print("Database populated successfully!")

    except Exception as e:
        print(f"Error populating database: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    populate_db()
