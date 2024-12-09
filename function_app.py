import azure.functions as func
import logging
import json
from database import get_db
from models import Film, Person, Planet, Species, Vehicle, Starship
from sqlalchemy.exc import SQLAlchemyError
import traceback
from sqlalchemy import select

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

def get_model_class(route):
    route_to_model = {
        'films': Film,
        'people': Person,
        'planets': Planet,
        'species': Species,
        'vehicles': Vehicle,
        'starships': Starship
    }
    return route_to_model.get(route)

def to_dict(obj, include_relationships=False):
    """
    Convert SQLAlchemy model instance to dictionary.
    Args:
        obj: SQLAlchemy model instance
        include_relationships: If True, includes full relationship data. If False, only includes IDs.
    """
    if not hasattr(obj, '__table__'):
        return obj

    # Get all column values
    result = {column.key: getattr(obj, column.key)
             for column in obj.__table__.columns}
    
    if not include_relationships:
        # Only include IDs for relationships
        for relationship in obj.__mapper__.relationships:
            related_objs = getattr(obj, relationship.key)
            if isinstance(related_objs, list):
                result[f"{relationship.key}_ids"] = [
                    related_obj.id for related_obj in related_objs
                ] if related_objs else []
            elif related_objs is not None:
                result[f"{relationship.key}_id"] = related_objs.id
    else:
        # Include full relationship data
        for relationship in obj.__mapper__.relationships:
            related_objs = getattr(obj, relationship.key)
            if isinstance(related_objs, list):
                result[relationship.key] = [
                    to_dict(related_obj, False) for related_obj in related_objs
                ] if related_objs else []
            elif related_objs is not None:
                result[relationship.key] = to_dict(related_objs, False)

    return result

@app.route(route="{route}", methods=["GET"])
def get_all(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get('route')
        include_relationships = req.params.get('include_relationships', '').lower() == 'true'
        model_class = get_model_class(route)
        
        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404
            )

        db = next(get_db())
        stmt = select(model_class)
        items = db.execute(stmt).scalars().all()

        return func.HttpResponse(
            body=json.dumps([to_dict(item, include_relationships) for item in items]),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e) + " " + str(traceback.format_exc())}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="{route}/{id}", methods=["GET"])
def get_by_id(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get('route')
        id = req.route_params.get('id')
        include_relationships = req.params.get('include_relationships', '').lower() == 'true'
        model_class = get_model_class(route)
        
        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404
            )

        db = next(get_db())
        stmt = select(model_class).where(model_class.id == id)
        item = db.execute(stmt).scalar_one_or_none()
        
        if not item:
            return func.HttpResponse(
                body=json.dumps({"error": "Not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        return func.HttpResponse(
            body=json.dumps(to_dict(item, include_relationships)),
            mimetype="application/json",
            status_code=200
        )
    except Exception as e:
        return func.HttpResponse(
            body=json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )

@app.route(route="{route}", methods=["POST"])
def create(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get('route')
        model_class = get_model_class(route)
        
        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404
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
            status_code=201
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

@app.route(route="{route}/{id}", methods=["PUT"])
def update(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get('route')
        id = req.route_params.get('id')
        model_class = get_model_class(route)
        
        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404
            )

        db = next(get_db())
        item = db.query(model_class).filter(model_class.id == id).first()
        
        if not item:
            return func.HttpResponse(
                body=json.dumps({"error": "Not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        data = req.get_json()
        for key, value in data.items():
            setattr(item, key, value)
            
        db.commit()
        db.refresh(item)
        
        return func.HttpResponse(
            body=json.dumps(to_dict(item)),
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

@app.route(route="{route}/{id}", methods=["DELETE"])
def delete(req: func.HttpRequest) -> func.HttpResponse:
    try:
        route = req.route_params.get('route')
        id = req.route_params.get('id')
        model_class = get_model_class(route)
        
        if not model_class:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid route"}),
                mimetype="application/json",
                status_code=404
            )

        db = next(get_db())
        item = db.query(model_class).filter(model_class.id == id).first()
        
        if not item:
            return func.HttpResponse(
                body=json.dumps({"error": "Not found"}),
                mimetype="application/json",
                status_code=404
            )
        
        db.delete(item)
        db.commit()
        
        return func.HttpResponse(status_code=204)
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


