import azure.functions as func
import logging
import json
from database import get_db
from models import Film, Person, Planet, Species, Vehicle, Starship
from sqlalchemy.exc import SQLAlchemyError
import traceback
from sqlalchemy import select
from sqlalchemy import func as sql_func
from sqlalchemy import Float

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


def get_model_class(route):
    route_to_model = {
        "films": Film,
        "people": Person,
        "planets": Planet,
        "species": Species,
        "vehicles": Vehicle,
        "starships": Starship,
    }
    return route_to_model.get(route)


def to_dict(obj, include_relationships=False):
    """
    Convert SQLAlchemy model instance to dictionary.
    Args:
        obj: SQLAlchemy model instance
        include_relationships: If True, includes full relationship data. If False, only includes IDs.
    """
    if not hasattr(obj, "__table__"):
        return obj

    # Get all column values
    result = {column.key: getattr(obj, column.key) for column in obj.__table__.columns}

    if not include_relationships:
        # Only include IDs for relationships
        for relationship in obj.__mapper__.relationships:
            related_objs = getattr(obj, relationship.key)
            if isinstance(related_objs, list):
                result[f"{relationship.key}_ids"] = (
                    [related_obj.id for related_obj in related_objs]
                    if related_objs
                    else []
                )
            elif related_objs is not None:
                result[f"{relationship.key}_id"] = related_objs.id
    else:
        # Include full relationship data
        for relationship in obj.__mapper__.relationships:
            related_objs = getattr(obj, relationship.key)
            if isinstance(related_objs, list):
                result[relationship.key] = (
                    [to_dict(related_obj, False) for related_obj in related_objs]
                    if related_objs
                    else []
                )
            elif related_objs is not None:
                result[relationship.key] = to_dict(related_objs, False)

    return result


@app.route(route="{route}", methods=["GET"])
def get_all(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get("route")
        include_relationships = (
            req.params.get("include_relationships", "").lower() == "true"
        )
        model_class = get_model_class(route)

        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404,
            )

        db = next(get_db())
        stmt = select(model_class)
        items = db.execute(stmt).scalars().all()

        return func.HttpResponse(
            body=json.dumps([to_dict(item, include_relationships) for item in items]),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e) + " " + str(traceback.format_exc())}),
            mimetype="application/json",
            status_code=500,
        )


@app.route(route="statistics/{route}", methods=["GET"])
def get_statistics(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get('route')
        model_class = get_model_class(route)
        
        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404
            )

        db = next(get_db())
        
        # Base statistics
        total_count = db.query(model_class).count()
        stats = {"total_count": total_count}
        
        # Helper function to safely convert string to float
        def safe_float(value):
            try:
                if value in ["unknown", "n/a", "none", None, ""]:
                    return None
                return float(value.replace(",", ""))
            except (ValueError, AttributeError):
                return None

        # Helper function to calculate average excluding None values
        def calculate_average(values):
            valid_values = [v for v in values if v is not None]
            return sum(valid_values) / len(valid_values) if valid_values else None

        # Model-specific statistics
        if route == "films":
            # Get all films
            films = db.query(model_class).all()
            
            # Episode statistics
            episodes = [safe_float(film.episode_id) for film in films]
            valid_episodes = [ep for ep in episodes if ep is not None]
            
            # Release date statistics (format: YYYY-MM-DD)
            release_years = [int(film.release_date.split('-')[0]) for film in films if film.release_date]
            
            # Character count statistics
            character_counts = [len(film.characters) for film in films]
            planet_counts = [len(film.planets) for film in films]
            species_counts = [len(film.species) for film in films]
            vehicle_counts = [len(film.vehicles) for film in films]
            starship_counts = [len(film.starships) for film in films]
            
            # Director and producer statistics
            directors = [film.director for film in films if film.director]
            producers = [p.strip() for film in films if film.producer 
                        for p in film.producer.split(',')]
            
            stats.update({
                "episode_stats": {
                    "total_episodes": len(valid_episodes),
                    "earliest_episode": min(valid_episodes) if valid_episodes else None,
                    "latest_episode": max(valid_episodes) if valid_episodes else None
                },
                "release_stats": {
                    "earliest_year": min(release_years) if release_years else None,
                    "latest_year": max(release_years) if release_years else None,
                    "years_span": max(release_years) - min(release_years) if release_years else None
                },
                "content_stats": {
                    "characters": {
                        "max_count": max(character_counts),
                        "min_count": min(character_counts),
                        "avg_count": round(sum(character_counts) / len(character_counts), 2),
                        "total_unique": len(set(char.id for film in films for char in film.characters))
                    },
                    "planets": {
                        "max_count": max(planet_counts),
                        "min_count": min(planet_counts),
                        "avg_count": round(sum(planet_counts) / len(planet_counts), 2),
                        "total_unique": len(set(planet.id for film in films for planet in film.planets))
                    },
                    "species": {
                        "max_count": max(species_counts),
                        "min_count": min(species_counts),
                        "avg_count": round(sum(species_counts) / len(species_counts), 2),
                        "total_unique": len(set(species.id for film in films for species in film.species))
                    },
                    "vehicles": {
                        "max_count": max(vehicle_counts),
                        "min_count": min(vehicle_counts),
                        "avg_count": round(sum(vehicle_counts) / len(vehicle_counts), 2),
                        "total_unique": len(set(vehicle.id for film in films for vehicle in film.vehicles))
                    },
                    "starships": {
                        "max_count": max(starship_counts),
                        "min_count": min(starship_counts),
                        "avg_count": round(sum(starship_counts) / len(starship_counts), 2),
                        "total_unique": len(set(starship.id for film in films for starship in film.starships))
                    }
                },
                "production_stats": {
                    "unique_directors": len(set(directors)),
                    "directors": list(set(directors)),
                    "unique_producers": len(set(producers)),
                    "producers": list(set(producers))
                },
                "films_by_content": {
                    "most_characters": {
                        "title": max(films, key=lambda x: len(x.characters)).title,
                        "count": max(character_counts)
                    },
                    "most_planets": {
                        "title": max(films, key=lambda x: len(x.planets)).title,
                        "count": max(planet_counts)
                    },
                    "most_species": {
                        "title": max(films, key=lambda x: len(x.species)).title,
                        "count": max(species_counts)
                    },
                    "most_vehicles": {
                        "title": max(films, key=lambda x: len(x.vehicles)).title,
                        "count": max(vehicle_counts)
                    },
                    "most_starships": {
                        "title": max(films, key=lambda x: len(x.starships)).title,
                        "count": max(starship_counts)
                    }
                }
            })

        elif route == "people":
            # Get all people
            people = db.query(model_class).all()
            
            # Height statistics
            heights = [safe_float(person.height) for person in people]
            valid_heights = [h for h in heights if h is not None]
            
            # Mass statistics
            masses = [safe_float(person.mass) for person in people]
            valid_masses = [m for m in masses if m is not None]
            
            # Gender statistics
            genders = [person.gender for person in people if person.gender not in ["unknown", "n/a", "none", None, ""]]
            gender_distribution = {gender: genders.count(gender) for gender in set(genders)}
            
            stats.update({
                "height_stats": {
                    "tallest_person": {
                        "name": max(people, key=lambda x: safe_float(x.height) or 0).name,
                        "height": max(valid_heights) if valid_heights else None
                    },
                    "shortest_person": {
                        "name": min(people, key=lambda x: safe_float(x.height) or float('inf')).name,
                        "height": min(valid_heights) if valid_heights else None
                    },
                    "average_height": round(calculate_average(valid_heights), 2) if valid_heights else None,
                    "height_data_availability": f"{len(valid_heights)}/{total_count} records"
                },
                "mass_stats": {
                    "heaviest_person": {
                        "name": max(people, key=lambda x: safe_float(x.mass) or 0).name,
                        "mass": max(valid_masses) if valid_masses else None
                    },
                    "lightest_person": {
                        "name": min(people, key=lambda x: safe_float(x.mass) or float('inf')).name,
                        "mass": min(valid_masses) if valid_masses else None
                    },
                    "average_mass": round(calculate_average(valid_masses), 2) if valid_masses else None,
                    "mass_data_availability": f"{len(valid_masses)}/{total_count} records"
                },
                "gender_stats": {
                    "distribution": gender_distribution,
                    "most_common": max(gender_distribution.items(), key=lambda x: x[1])[0] if gender_distribution else None
                }
            })

        elif route == "planets":
            # Get all planets
            planets = db.query(model_class).all()
            
            # Diameter statistics
            diameters = [safe_float(planet.diameter) for planet in planets]
            valid_diameters = [d for d in diameters if d is not None]
            
            # Population statistics
            populations = [safe_float(planet.population) for planet in planets]
            valid_populations = [p for p in populations if p is not None]
            
            # Climate and terrain analysis
            climates = [climate.strip() for planet in planets 
                       for climate in planet.climate.split(",") 
                       if planet.climate not in ["unknown", "n/a", "none", None, ""]]
            terrains = [terrain.strip() for planet in planets 
                       for terrain in planet.terrain.split(",") 
                       if planet.terrain not in ["unknown", "n/a", "none", None, ""]]
            
            stats.update({
                "size_stats": {
                    "largest_planet": {
                        "name": max(planets, key=lambda x: safe_float(x.diameter) or 0).name,
                        "diameter": max(valid_diameters) if valid_diameters else None
                    },
                    "smallest_planet": {
                        "name": min(planets, key=lambda x: safe_float(x.diameter) or float('inf')).name,
                        "diameter": min(valid_diameters) if valid_diameters else None
                    },
                    "average_diameter": round(calculate_average(valid_diameters), 2) if valid_diameters else None
                },
                "population_stats": {
                    "most_populated": {
                        "name": max(planets, key=lambda x: safe_float(x.population) or 0).name,
                        "population": max(valid_populations) if valid_populations else None
                    },
                    "least_populated": {
                        "name": min(planets, key=lambda x: safe_float(x.population) or float('inf')).name,
                        "population": min(valid_populations) if valid_populations else None
                    },
                    "average_population": round(calculate_average(valid_populations), 2) if valid_populations else None
                },
                "environment_stats": {
                    "unique_climates": len(set(climates)),
                    "most_common_climate": max(set(climates), key=climates.count) if climates else None,
                    "unique_terrains": len(set(terrains)),
                    "most_common_terrain": max(set(terrains), key=terrains.count) if terrains else None
                }
            })

        elif route == "starships":
            # Get all starships
            starships = db.query(model_class).all()
            
            # Speed statistics
            speeds = [safe_float(ship.max_atmosphering_speed) for ship in starships]
            valid_speeds = [s for s in speeds if s is not None]
            
            # Capacity statistics
            cargo_capacities = [safe_float(ship.cargo_capacity) for ship in starships]
            valid_cargo = [c for c in cargo_capacities if c is not None]
            
            # Cost statistics
            costs = [safe_float(ship.cost_in_credits) for ship in starships]
            valid_costs = [c for c in costs if c is not None]
            
            # Length statistics
            lengths = [safe_float(ship.length) for ship in starships]
            valid_lengths = [l for l in lengths if l is not None]
            
            # Crew and passenger statistics
            crews = [safe_float(ship.crew) for ship in starships]
            valid_crews = [c for c in crews if c is not None]
            passengers = [safe_float(ship.passengers) for ship in starships]
            valid_passengers = [p for p in passengers if p is not None]
            
            # Hyperdrive and MGLT statistics
            hyperdrives = [safe_float(ship.hyperdrive_rating) for ship in starships]
            valid_hyperdrives = [h for h in hyperdrives if h is not None]
            mglts = [safe_float(ship.MGLT) for ship in starships]
            valid_mglts = [m for m in mglts if m is not None]
            
            # Manufacturer and class analysis
            manufacturers = [m.strip() for ship in starships if ship.manufacturer 
                            for m in ship.manufacturer.split(',')]
            starship_classes = [ship.starship_class for ship in starships 
                               if ship.starship_class not in ["unknown", "n/a", "none", None, ""]]
            
            stats.update({
                "speed_stats": {
                    "fastest_ship": {
                        "name": max(starships, key=lambda x: safe_float(x.max_atmosphering_speed) or 0).name,
                        "speed": max(valid_speeds) if valid_speeds else None
                    },
                    "slowest_ship": {
                        "name": min(starships, key=lambda x: safe_float(x.max_atmosphering_speed) or float('inf')).name,
                        "speed": min(valid_speeds) if valid_speeds else None
                    },
                    "average_speed": round(calculate_average(valid_speeds), 2) if valid_speeds else None
                },
                "cargo_stats": {
                    "largest_cargo": {
                        "name": max(starships, key=lambda x: safe_float(x.cargo_capacity) or 0).name,
                        "capacity": max(valid_cargo) if valid_cargo else None
                    },
                    "smallest_cargo": {
                        "name": min(starships, key=lambda x: safe_float(x.cargo_capacity) or float('inf')).name,
                        "capacity": min(valid_cargo) if valid_cargo else None
                    },
                    "average_cargo": round(calculate_average(valid_cargo), 2) if valid_cargo else None
                },
                "cost_stats": {
                    "most_expensive": {
                        "name": max(starships, key=lambda x: safe_float(x.cost_in_credits) or 0).name,
                        "cost": max(valid_costs) if valid_costs else None
                    },
                    "least_expensive": {
                        "name": min(starships, key=lambda x: safe_float(x.cost_in_credits) or float('inf')).name,
                        "cost": min(valid_costs) if valid_costs else None
                    },
                    "average_cost": round(calculate_average(valid_costs), 2) if valid_costs else None
                },
                "size_stats": {
                    "longest_ship": {
                        "name": max(starships, key=lambda x: safe_float(x.length) or 0).name,
                        "length": max(valid_lengths) if valid_lengths else None
                    },
                    "shortest_ship": {
                        "name": min(starships, key=lambda x: safe_float(x.length) or float('inf')).name,
                        "length": min(valid_lengths) if valid_lengths else None
                    },
                    "average_length": round(calculate_average(valid_lengths), 2) if valid_lengths else None
                },
                "crew_stats": {
                    "largest_crew": {
                        "name": max(starships, key=lambda x: safe_float(x.crew) or 0).name,
                        "crew": max(valid_crews) if valid_crews else None
                    },
                    "smallest_crew": {
                        "name": min(starships, key=lambda x: safe_float(x.crew) or float('inf')).name,
                        "crew": min(valid_crews) if valid_crews else None
                    },
                    "average_crew": round(calculate_average(valid_crews), 2) if valid_crews else None
                },
                "passenger_stats": {
                    "highest_capacity": {
                        "name": max(starships, key=lambda x: safe_float(x.passengers) or 0).name,
                        "passengers": max(valid_passengers) if valid_passengers else None
                    },
                    "lowest_capacity": {
                        "name": min(starships, key=lambda x: safe_float(x.passengers) or float('inf')).name,
                        "passengers": min(valid_passengers) if valid_passengers else None
                    },
                    "average_capacity": round(calculate_average(valid_passengers), 2) if valid_passengers else None
                },
                "performance_stats": {
                    "hyperdrive": {
                        "fastest": {
                            "name": min(starships, key=lambda x: safe_float(x.hyperdrive_rating) or float('inf')).name,
                            "rating": min(valid_hyperdrives) if valid_hyperdrives else None
                        },
                        "slowest": {
                            "name": max(starships, key=lambda x: safe_float(x.hyperdrive_rating) or 0).name,
                            "rating": max(valid_hyperdrives) if valid_hyperdrives else None
                        },
                        "average_rating": round(calculate_average(valid_hyperdrives), 2) if valid_hyperdrives else None
                    },
                    "MGLT": {
                        "fastest": {
                            "name": max(starships, key=lambda x: safe_float(x.MGLT) or 0).name,
                            "mglt": max(valid_mglts) if valid_mglts else None
                        },
                        "slowest": {
                            "name": min(starships, key=lambda x: safe_float(x.MGLT) or float('inf')).name,
                            "mglt": min(valid_mglts) if valid_mglts else None
                        },
                        "average_mglt": round(calculate_average(valid_mglts), 2) if valid_mglts else None
                    }
                },
                "manufacturer_stats": {
                    "unique_manufacturers": len(set(manufacturers)),
                    "most_common": max(set(manufacturers), key=manufacturers.count) if manufacturers else None,
                    "distribution": {m: manufacturers.count(m) for m in set(manufacturers)} if manufacturers else {}
                },
                "class_stats": {
                    "unique_classes": len(set(starship_classes)),
                    "most_common": max(set(starship_classes), key=starship_classes.count) if starship_classes else None,
                    "distribution": {c: starship_classes.count(c) for c in set(starship_classes)} if starship_classes else {}
                },
                "pilot_stats": {
                    "most_pilots": {
                        "name": max(starships, key=lambda x: len(x.pilots)).name,
                        "count": max(len(ship.pilots) for ship in starships)
                    },
                    "total_unique_pilots": len(set(pilot.id for ship in starships for pilot in ship.pilots))
                }
            })

        elif route == "vehicles":
            # Get all vehicles
            vehicles = db.query(model_class).all()
            
            # Speed statistics
            speeds = [safe_float(vehicle.max_atmosphering_speed) for vehicle in vehicles]
            valid_speeds = [s for s in speeds if s is not None]
            
            # Passenger statistics
            passengers = [safe_float(vehicle.passengers) for vehicle in vehicles]
            valid_passengers = [p for p in passengers if p is not None]
            
            # Cost statistics
            costs = [safe_float(vehicle.cost_in_credits) for vehicle in vehicles]
            valid_costs = [c for c in costs if c is not None]
            
            # Length statistics
            lengths = [safe_float(vehicle.length) for vehicle in vehicles]
            valid_lengths = [l for l in lengths if l is not None]
            
            # Crew statistics
            crews = [safe_float(vehicle.crew) for vehicle in vehicles]
            valid_crews = [c for c in crews if c is not None]
            
            # Manufacturer and class analysis
            manufacturers = [m.strip() for vehicle in vehicles if vehicle.manufacturer 
                            for m in vehicle.manufacturer.split(',')]
            vehicle_classes = [vehicle.vehicle_class for vehicle in vehicles 
                              if vehicle.vehicle_class not in ["unknown", "n/a", "none", None, ""]]
            
            stats.update({
                "speed_stats": {
                    "fastest_vehicle": {
                        "name": max(vehicles, key=lambda x: safe_float(x.max_atmosphering_speed) or 0).name,
                        "speed": max(valid_speeds) if valid_speeds else None
                    },
                    "slowest_vehicle": {
                        "name": min(vehicles, key=lambda x: safe_float(x.max_atmosphering_speed) or float('inf')).name,
                        "speed": min(valid_speeds) if valid_speeds else None
                    },
                    "average_speed": round(calculate_average(valid_speeds), 2) if valid_speeds else None
                },
                "passenger_stats": {
                    "highest_capacity": {
                        "name": max(vehicles, key=lambda x: safe_float(x.passengers) or 0).name,
                        "passengers": max(valid_passengers) if valid_passengers else None
                    },
                    "lowest_capacity": {
                        "name": min(vehicles, key=lambda x: safe_float(x.passengers) or float('inf')).name,
                        "passengers": min(valid_passengers) if valid_passengers else None
                    },
                    "average_capacity": round(calculate_average(valid_passengers), 2) if valid_passengers else None
                },
                "cost_stats": {
                    "most_expensive": {
                        "name": max(vehicles, key=lambda x: safe_float(x.cost_in_credits) or 0).name,
                        "cost": max(valid_costs) if valid_costs else None
                    },
                    "least_expensive": {
                        "name": min(vehicles, key=lambda x: safe_float(x.cost_in_credits) or float('inf')).name,
                        "cost": min(valid_costs) if valid_costs else None
                    },
                    "average_cost": round(calculate_average(valid_costs), 2) if valid_costs else None
                },
                "size_stats": {
                    "longest_vehicle": {
                        "name": max(vehicles, key=lambda x: safe_float(x.length) or 0).name,
                        "length": max(valid_lengths) if valid_lengths else None
                    },
                    "shortest_vehicle": {
                        "name": min(vehicles, key=lambda x: safe_float(x.length) or float('inf')).name,
                        "length": min(valid_lengths) if valid_lengths else None
                    },
                    "average_length": round(calculate_average(valid_lengths), 2) if valid_lengths else None
                },
                "crew_stats": {
                    "largest_crew": {
                        "name": max(vehicles, key=lambda x: safe_float(x.crew) or 0).name,
                        "crew": max(valid_crews) if valid_crews else None
                    },
                    "smallest_crew": {
                        "name": min(vehicles, key=lambda x: safe_float(x.crew) or float('inf')).name,
                        "crew": min(valid_crews) if valid_crews else None
                    },
                    "average_crew": round(calculate_average(valid_crews), 2) if valid_crews else None
                },
                "manufacturer_stats": {
                    "unique_manufacturers": len(set(manufacturers)),
                    "most_common": max(set(manufacturers), key=manufacturers.count) if manufacturers else None,
                    "distribution": {m: manufacturers.count(m) for m in set(manufacturers)} if manufacturers else {}
                },
                "class_stats": {
                    "unique_classes": len(set(vehicle_classes)),
                    "most_common": max(set(vehicle_classes), key=vehicle_classes.count) if vehicle_classes else None,
                    "distribution": {c: vehicle_classes.count(c) for c in set(vehicle_classes)} if vehicle_classes else {}
                },
                "pilot_stats": {
                    "most_pilots": {
                        "name": max(vehicles, key=lambda x: len(x.pilots)).name,
                        "count": max(len(vehicle.pilots) for vehicle in vehicles)
                    },
                    "total_unique_pilots": len(set(pilot.id for vehicle in vehicles for pilot in vehicle.pilots))
                }
            })

        elif route == "species":
            # Get all species
            species_list = db.query(model_class).all()
            
            # Height statistics
            heights = [safe_float(species.average_height) for species in species_list]
            valid_heights = [h for h in heights if h is not None]
            
            # Lifespan statistics
            lifespans = [safe_float(species.average_lifespan) for species in species_list]
            valid_lifespans = [l for l in lifespans if l is not None]
            
            # Classification and designation analysis
            classifications = [species.classification for species in species_list 
                              if species.classification not in ["unknown", "n/a", "none", None, ""]]
            designations = [species.designation for species in species_list 
                           if species.designation not in ["unknown", "n/a", "none", None, ""]]
            
            # Color analysis
            def parse_colors(color_str):
                if not color_str or color_str in ["unknown", "n/a", "none", None, ""]:
                    return []
                return [c.strip() for c in color_str.split(',')]

            all_skin_colors = [color for species in species_list 
                              for color in parse_colors(species.skin_colors)]
            all_hair_colors = [color for species in species_list 
                              for color in parse_colors(species.hair_colors)]
            all_eye_colors = [color for species in species_list 
                              for color in parse_colors(species.eye_colors)]
            
            # Language analysis
            languages = [species.language for species in species_list 
                        if species.language not in ["unknown", "n/a", "none", None, ""]]
            
            # Population analysis
            species_with_homeworld = [species for species in species_list if species.homeworld]
            
            stats.update({
                "height_stats": {
                    "tallest_species": {
                        "name": max(species_list, key=lambda x: safe_float(x.average_height) or 0).name,
                        "height": max(valid_heights) if valid_heights else None
                    },
                    "shortest_species": {
                        "name": min(species_list, key=lambda x: safe_float(x.average_height) or float('inf')).name,
                        "height": min(valid_heights) if valid_heights else None
                    },
                    "average_height": round(calculate_average(valid_heights), 2) if valid_heights else None
                },
                "lifespan_stats": {
                    "longest_lived": {
                        "name": max(species_list, key=lambda x: safe_float(x.average_lifespan) or 0).name,
                        "lifespan": max(valid_lifespans) if valid_lifespans else None
                    },
                    "shortest_lived": {
                        "name": min(species_list, key=lambda x: safe_float(x.average_lifespan) or float('inf')).name,
                        "lifespan": min(valid_lifespans) if valid_lifespans else None
                    },
                    "average_lifespan": round(calculate_average(valid_lifespans), 2) if valid_lifespans else None
                },
                "classification_stats": {
                    "unique_classifications": len(set(classifications)),
                    "most_common": max(set(classifications), key=classifications.count) if classifications else None,
                    "distribution": {c: classifications.count(c) for c in set(classifications)} if classifications else {}
                },
                "designation_stats": {
                    "unique_designations": len(set(designations)),
                    "distribution": {d: designations.count(d) for d in set(designations)} if designations else {}
                },
                "appearance_stats": {
                    "skin_colors": {
                        "unique_colors": len(set(all_skin_colors)),
                        "most_common": max(set(all_skin_colors), key=all_skin_colors.count) if all_skin_colors else None,
                        "all_colors": list(set(all_skin_colors)) if all_skin_colors else []
                    },
                    "hair_colors": {
                        "unique_colors": len(set(all_hair_colors)),
                        "most_common": max(set(all_hair_colors), key=all_hair_colors.count) if all_hair_colors else None,
                        "all_colors": list(set(all_hair_colors)) if all_hair_colors else []
                    },
                    "eye_colors": {
                        "unique_colors": len(set(all_eye_colors)),
                        "most_common": max(set(all_eye_colors), key=all_eye_colors.count) if all_eye_colors else None,
                        "all_colors": list(set(all_eye_colors)) if all_eye_colors else []
                    }
                },
                "language_stats": {
                    "unique_languages": len(set(languages)),
                    "most_common": max(set(languages), key=languages.count) if languages else None,
                    "all_languages": list(set(languages)) if languages else []
                },
                "homeworld_stats": {
                    "species_with_homeworld": len(species_with_homeworld),
                    "species_without_homeworld": total_count - len(species_with_homeworld),
                    "homeworld_distribution": {
                        species.homeworld.name: len([s for s in species_list if s.homeworld and s.homeworld.name == species.homeworld.name])
                        for species in species_with_homeworld
                    } if species_with_homeworld else {}
                },
                "population_stats": {
                    "most_populated_species": {
                        "name": max(species_list, key=lambda x: len(x.people)).name,
                        "count": max(len(species.people) for species in species_list)
                    },
                    "average_population": round(sum(len(species.people) for species in species_list) / len(species_list), 2)
                }
            })

        return func.HttpResponse(
            body=json.dumps(stats),
            mimetype="application/json",
            status_code=200
        )
    except SQLAlchemyError as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Database error", "details": str(e)}),
            mimetype="application/json",
            status_code=400
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )


@app.route(route="{route:regex(films|people|planets|species|vehicles|starships)}/{id}", methods=["GET"])
def get_by_id(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get("route")
        id = req.route_params.get("id")
        include_relationships = (
            req.params.get("include_relationships", "").lower() == "true"
        )
        model_class = get_model_class(route)

        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404,
            )

        db = next(get_db())
        stmt = select(model_class).where(model_class.id == id)
        item = db.execute(stmt).scalar_one_or_none()

        if not item:
            return func.HttpResponse(
                body=json.dumps({"error": "Not found"}),
                mimetype="application/json",
                status_code=404,
            )

        return func.HttpResponse(
            body=json.dumps(to_dict(item, include_relationships)),
            mimetype="application/json",
            status_code=200,
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


@app.route(route="{route}", methods=["POST"])
def create(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get("route")
        model_class = get_model_class(route)

        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404,
            )

        data = req.get_json()
        db = next(get_db())

        new_item = model_class(**data)
        db.add(new_item)
        db.commit()
        db.refresh(new_item)

        return func.HttpResponse(
            body=json.dumps(to_dict(new_item)),
            mimetype="application/json",
            status_code=201,
        )
    except SQLAlchemyError as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Database error", "details": str(e)}),
            mimetype="application/json",
            status_code=400,
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


@app.route(route="{route}/{id}", methods=["PUT"])
def update(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get("route")
        id = req.route_params.get("id")
        model_class = get_model_class(route)

        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404,
            )

        db = next(get_db())
        item = db.query(model_class).filter(model_class.id == id).first()

        if not item:
            return func.HttpResponse(
                body=json.dumps({"error": "Not found"}),
                mimetype="application/json",
                status_code=404,
            )

        data = req.get_json()
        for key, value in data.items():
            setattr(item, key, value)

        db.commit()
        db.refresh(item)

        return func.HttpResponse(
            body=json.dumps(to_dict(item)), mimetype="application/json", status_code=200
        )
    except SQLAlchemyError as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Database error", "details": str(e)}),
            mimetype="application/json",
            status_code=400,
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )


@app.route(route="{route}/{id}", methods=["DELETE"])
def delete(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get("route")
        id = req.route_params.get("id")
        model_class = get_model_class(route)

        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404,
            )

        db = next(get_db())
        item = db.query(model_class).filter(model_class.id == id).first()

        if not item:
            return func.HttpResponse(
                body=json.dumps({"error": "Not found"}),
                mimetype="application/json",
                status_code=404,
            )

        db.delete(item)
        db.commit()

        return func.HttpResponse(status_code=204)
    except SQLAlchemyError as e:
        return func.HttpResponse(
            body=json.dumps({"error": "Database error", "details": str(e)}),
            mimetype="application/json",
            status_code=400,
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500,
        )
