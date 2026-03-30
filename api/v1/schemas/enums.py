from enum import Enum


class AgeRangeEnum(str, Enum):
    age_10_17 = "10-17"
    age_18_25 = "18-25"
    age_26_35 = "26-35"
    age_36_45 = "36-45"
    age_46_55 = "46-55"
    age_56_65 = "56-65"
    age_66_70 = "66-70"
    age_71_plus = "71+"


class RegistrationTypeEnum(str, Enum):
    attendance_only = "attendance_only"
    with_accommodation = "with_accommodation"


class ActiveStatusEnum(str, Enum):
    active = "active"
    inactive = "inactive"
    relocated = "relocated"


class RegistrationStatusEnum(str, Enum):
    open = "open"
    closed = "closed"
    suspended = "suspended"


class MealType(str, Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
