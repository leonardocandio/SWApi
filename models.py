from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Table, Float, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

# Association tables
film_people = Table('film_people', Base.metadata,
    Column('film_id', Integer, ForeignKey('dbo.films.id', ondelete='CASCADE')),
    Column('person_id', Integer, ForeignKey('dbo.people.id', ondelete='CASCADE')),
    schema='dbo'
)

film_planets = Table('film_planets', Base.metadata,
    Column('film_id', Integer, ForeignKey('dbo.films.id', ondelete='CASCADE')),
    Column('planet_id', Integer, ForeignKey('dbo.planets.id', ondelete='CASCADE')),
    schema='dbo'
)

film_species = Table('film_species', Base.metadata,
    Column('film_id', Integer, ForeignKey('dbo.films.id', ondelete='CASCADE')),
    Column('species_id', Integer, ForeignKey('dbo.species.id', ondelete='CASCADE')),
    schema='dbo'
)

film_vehicles = Table('film_vehicles', Base.metadata,
    Column('film_id', Integer, ForeignKey('dbo.films.id', ondelete='CASCADE')),
    Column('vehicle_id', Integer, ForeignKey('dbo.vehicles.id', ondelete='CASCADE')),
    schema='dbo'
)

film_starships = Table('film_starships', Base.metadata,
    Column('film_id', Integer, ForeignKey('dbo.films.id', ondelete='CASCADE')),
    Column('starship_id', Integer, ForeignKey('dbo.starships.id', ondelete='CASCADE')),
    schema='dbo'
)

person_species = Table('person_species', Base.metadata,
    Column('person_id', Integer, ForeignKey('dbo.people.id', ondelete='CASCADE')),
    Column('species_id', Integer, ForeignKey('dbo.species.id', ondelete='CASCADE')),
    schema='dbo'
)

person_vehicles = Table('person_vehicles', Base.metadata,
    Column('person_id', Integer, ForeignKey('dbo.people.id', ondelete='CASCADE')),
    Column('vehicle_id', Integer, ForeignKey('dbo.vehicles.id', ondelete='CASCADE')),
    schema='dbo'
)

person_starships = Table('person_starships', Base.metadata,
    Column('person_id', Integer, ForeignKey('dbo.people.id', ondelete='CASCADE')),
    Column('starship_id', Integer, ForeignKey('dbo.starships.id', ondelete='CASCADE')),
    schema='dbo'
)

class Film(Base):
    __tablename__ = 'films'
    __table_args__ = {'schema': 'dbo'}
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    episode_id = Column(Integer)
    opening_crawl = Column(Text)
    director = Column(String(100))
    producer = Column(String(200))
    release_date = Column(String(50))
    created = Column(String(50))
    edited = Column(String(50))
    url = Column(String(200))

    # Relationships
    characters = relationship("Person", secondary=film_people, back_populates="films")
    planets = relationship("Planet", secondary=film_planets, back_populates="films")
    species = relationship("Species", secondary=film_species, back_populates="films")
    vehicles = relationship("Vehicle", secondary=film_vehicles, back_populates="films")
    starships = relationship("Starship", secondary=film_starships, back_populates="films")

class Person(Base):
    __tablename__ = 'people'
    __table_args__ = {'schema': 'dbo'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    height = Column(String(20))
    mass = Column(String(20))
    hair_color = Column(String(50))
    skin_color = Column(String(50))
    eye_color = Column(String(50))
    birth_year = Column(String(20))
    gender = Column(String(20))
    homeworld_id = Column(Integer, ForeignKey('dbo.planets.id', ondelete='SET NULL'))
    created = Column(String(50))
    edited = Column(String(50))
    url = Column(String(200))

    # Relationships
    homeworld = relationship("Planet", back_populates="residents")
    films = relationship("Film", secondary=film_people, back_populates="characters")
    species = relationship("Species", secondary=person_species, back_populates="people")
    vehicles = relationship("Vehicle", secondary=person_vehicles, back_populates="pilots")
    starships = relationship("Starship", secondary=person_starships, back_populates="pilots")

class Planet(Base):
    __tablename__ = 'planets'
    __table_args__ = {'schema': 'dbo'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    rotation_period = Column(String(20))
    orbital_period = Column(String(20))
    diameter = Column(String(20))
    climate = Column(String(100))
    gravity = Column(String(50))
    terrain = Column(String(100))
    surface_water = Column(String(20))
    population = Column(String(50))
    created = Column(String(50))
    edited = Column(String(50))
    url = Column(String(200))
    
    # Relationships
    residents = relationship("Person", back_populates="homeworld")
    films = relationship("Film", secondary=film_planets, back_populates="planets")
    native_species = relationship("Species", back_populates="homeworld")

class Species(Base):
    __tablename__ = 'species'
    __table_args__ = {'schema': 'dbo'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    classification = Column(String(100))
    designation = Column(String(100))
    average_height = Column(String(20))
    skin_colors = Column(String(200))
    hair_colors = Column(String(200))
    eye_colors = Column(String(200))
    average_lifespan = Column(String(20))
    homeworld_id = Column(Integer, ForeignKey('dbo.planets.id', ondelete='SET NULL'))
    language = Column(String(100))
    created = Column(String(50))
    edited = Column(String(50))
    url = Column(String(200))
    
    # Relationships
    homeworld = relationship("Planet", back_populates="native_species")
    people = relationship("Person", secondary=person_species, back_populates="species")
    films = relationship("Film", secondary=film_species, back_populates="species")

class Vehicle(Base):
    __tablename__ = 'vehicles'
    __table_args__ = {'schema': 'dbo'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    model = Column(String(100))
    manufacturer = Column(String(200))
    cost_in_credits = Column(String(50))
    length = Column(String(50))
    max_atmosphering_speed = Column(String(50))
    crew = Column(String(50))
    passengers = Column(String(50))
    cargo_capacity = Column(String(50))
    consumables = Column(String(50))
    vehicle_class = Column(String(100))
    created = Column(String(50))
    edited = Column(String(50))
    url = Column(String(200))
    
    # Relationships
    pilots = relationship("Person", secondary=person_vehicles, back_populates="vehicles")
    films = relationship("Film", secondary=film_vehicles, back_populates="vehicles")

class Starship(Base):
    __tablename__ = 'starships'
    __table_args__ = {'schema': 'dbo'}
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    model = Column(String(100))
    manufacturer = Column(String(200))
    cost_in_credits = Column(String(50))
    length = Column(String(50))
    max_atmosphering_speed = Column(String(50))
    crew = Column(String(50))
    passengers = Column(String(50))
    cargo_capacity = Column(String(50))
    consumables = Column(String(50))
    hyperdrive_rating = Column(String(50))
    MGLT = Column(String(50))
    starship_class = Column(String(100))
    created = Column(String(50))
    edited = Column(String(50))
    url = Column(String(200))
    
    # Relationships
    pilots = relationship("Person", secondary=person_starships, back_populates="starships")
    films = relationship("Film", secondary=film_starships, back_populates="starships")