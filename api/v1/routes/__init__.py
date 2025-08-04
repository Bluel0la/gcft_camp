from fastapi import APIRouter

# from api.v1.routes.authentication import users
from api.v1.routes.analytics import analytics_route
from api.v1.routes.hall_allocation import hall_route
from api.v1.routes.category_allocation import category_route
from api.v1.routes.hall_registration import registration_route

api_version_one = APIRouter(prefix="/api/v1")
api_version_one.include_router(analytics_route)
api_version_one.include_router(hall_route)
api_version_one.include_router(category_route)
api_version_one.include_router(registration_route)