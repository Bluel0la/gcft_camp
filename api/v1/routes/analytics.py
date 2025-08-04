import io
import pandas as pd
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from api.db.database import get_db
from typing import List
from api.v1.models import hall, category, user, phone_number
from api.v1.schemas.analytics import HallAnalytics, CategoryAnalytics, UserCount
from fastapi.responses import StreamingResponse


analytics_route = APIRouter(prefix="/analytics", tags=["Analytics"])


@analytics_route.get("/halls", response_model=List[HallAnalytics])
def get_hall_analytics(db: Session = Depends(get_db)):
    all_halls = db.query(hall.Hall).all()
    hall_analytics = []

    for h in all_halls:
        total_beds = h.no_beds
        categories_data = []

        # Fetch all categories assigned to this hall
        categories = (
            db.query(category.Category)
            .filter(category.Category.hall_name == h.hall_name)
            .all()
        )

        for cat in categories:
            # All users assigned to this category in the hall/floor
            users_in_category = (
                db.query(user.User)
                .filter(
                    user.User.hall_name == h.hall_name,
                    user.User.floor == cat.floor_allocated,
                    user.User.category == cat.category_name,
                )
                .all()
            )

            beds_allocated = len(users_in_category)
            beds_unallocated = cat.no_beds - beds_allocated
            male_count = sum(1 for u in users_in_category if u.gender.lower() == "male")
            female_count = sum(
                1 for u in users_in_category if u.gender.lower() == "female"
            )

            categories_data.append(
                CategoryAnalytics(
                    category_name=cat.category_name,
                    floor_allocated=cat.floor_allocated,
                    total_beds=cat.no_beds,
                    beds_allocated=beds_allocated,
                    beds_unallocated=beds_unallocated,
                    male_count=male_count,
                    female_count=female_count,
                )
            )

        hall_analytics.append(
            HallAnalytics(
                hall_name=h.hall_name,
                no_floors=h.no_floors,
                total_beds=total_beds,
                categories=categories_data,
            )
        )

    return hall_analytics


@analytics_route.get("/total-users", response_model=UserCount)
def get_total_registered_users(db: Session = Depends(get_db)):
    count = db.query(user.User).count()
    return {"total_users": count}


@analytics_route.get("/export/users-excel")
def export_user_data_excel(db: Session = Depends(get_db)):
    # Step 1: Fetch all users with phone + hall
    records = (
        db.query(
            user.User,
            phone_number.PhoneNumber.phone_number,
        )
        .join(
            phone_number.PhoneNumber,
            phone_number.PhoneNumber.id == user.User.phone_number_id,
        )
        .all()
    )

    # Step 2: Structure rows
    data = []
    for u, phone in records:
        data.append(
            {
                "Full Name": u.first_name,
                "Category": u.category,
                "Gender": u.gender,
                "Age": u.age,
                "Marital Status": u.marital_status,
                "No. of Children": u.no_children,
                "Names of Children": u.names_children,
                "Country": u.country,
                "State": u.state,
                "Arrival Date": (
                    u.arrival_date.strftime("%Y-%m-%d") if u.arrival_date else ""
                ),
                "Medical Issues": u.medical_issues,
                "Local Assembly": u.local_assembly,
                "Assembly Address": u.local_assembly_address,
                "Phone Number": phone,
                "Hall Name": u.hall_name,
                "Floor": u.floor,
                "Bed Number": u.bed_number,
            }
        )

    # Step 3: Create DataFrame and Excel file in memory
    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="User Allocations")

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=User_Allocations.xlsx"},
    )
