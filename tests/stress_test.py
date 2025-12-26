import re


def gender_classifier(category: str) -> str:
    """
    Classifies gender based on whole-word matches in a category string.
    """

    category_lower = category.lower()

    male_pattern = r"\b(brother|brothers|male)\b"
    female_pattern = r"\b(sister|sisters|mother|mothers|female)\b"

    if re.search(female_pattern, category_lower):
        return "female"
    elif re.search(male_pattern, category_lower):
        return "male"
    return "unspecified"

result = gender_classifier("Teens Below 18 (female)")
print(result)