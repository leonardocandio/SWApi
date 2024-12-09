import requests
from database import SessionLocal, create_tables
from models import Film, Person, Planet, Species, Vehicle, Starship
from sqlalchemy.exc import IntegrityError


def get_all_data(endpoint):
    results = []
    url = f"https://swapi.py4e.com/api/{endpoint}/"

    while url:
        response = requests.get(url)
        data = response.json()
        results.extend(data["results"])
        url = data["next"]

    return results


def populate_db():
    # First ensure tables exist
    create_tables(drop=True)

    db = SessionLocal()

    try:
        # Get all data from SWAPI
        print("Fetching data from SWAPI...")
        films = get_all_data("films")
        people = get_all_data("people")
        planets = get_all_data("planets")
        species = get_all_data("species")
        vehicles = get_all_data("vehicles")
        starships = get_all_data("starships")

        # Populate planets first
        print("Populating planets...")
        for planet_data in planets:
            try:
                planet_id = int(planet_data["url"].split("/")[-2])
                if not db.query(Planet).get(planet_id):
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
                        url=planet_data["url"],
                    )
                    db.add(planet)
                    db.flush()
            except Exception as e:
                print(f"Error adding planet {planet_data['name']}: {str(e)}")
                continue

        db.commit()

        # Populate films
        for film_data in films:
            film = Film(
                id=int(film_data["url"].split("/")[-2]),
                title=film_data["title"],
                episode_id=film_data["episode_id"],
                opening_crawl=film_data["opening_crawl"],
                director=film_data["director"],
                producer=film_data["producer"],
                release_date=film_data["release_date"],
                created=film_data["created"],
                edited=film_data["edited"],
                url=film_data["url"],
            )
            db.merge(film)

        # Populate species
        for species_data in species:
            homeworld_id = None
            if species_data["homeworld"]:
                homeworld_id = int(species_data["homeworld"].split("/")[-2])

            species_obj = Species(
                id=int(species_data["url"].split("/")[-2]),
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
                url=species_data["url"],
            )
            db.merge(species_obj)

        # Populate people
        for person_data in people:
            homeworld_id = None
            if person_data["homeworld"]:
                homeworld_id = int(person_data["homeworld"].split("/")[-2])

            person = Person(
                id=int(person_data["url"].split("/")[-2]),
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
                url=person_data["url"],
            )
            db.merge(person)

        # Populate vehicles
        for vehicle_data in vehicles:
            vehicle = Vehicle(
                id=int(vehicle_data["url"].split("/")[-2]),
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
                url=vehicle_data["url"],
            )
            db.merge(vehicle)

        # Populate starships
        for starship_data in starships:
            starship = Starship(
                id=int(starship_data["url"].split("/")[-2]),
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
                url=starship_data["url"],
            )
            db.merge(starship)

        # Handle many-to-many relationships
        for film_data in films:
            film_id = int(film_data["url"].split("/")[-2])
            film = db.query(Film).get(film_id)

            # Characters
            for char_url in film_data["characters"]:
                char_id = int(char_url.split("/")[-2])
                character = db.query(Person).get(char_id)
                if character:
                    film.characters.append(character)

            # Species
            for species_url in film_data["species"]:
                species_id = int(species_url.split("/")[-2])
                species_obj = db.query(Species).get(species_id)
                if species_obj:
                    film.species.append(species_obj)

            # Vehicles
            for vehicle_url in film_data["vehicles"]:
                vehicle_id = int(vehicle_url.split("/")[-2])
                vehicle = db.query(Vehicle).get(vehicle_id)
                if vehicle:
                    film.vehicles.append(vehicle)

            # Starships
            for starship_url in film_data["starships"]:
                starship_id = int(starship_url.split("/")[-2])
                starship = db.query(Starship).get(starship_id)
                if starship:
                    film.starships.append(starship)

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
