def gender_classifier(category: str) -> str:
    """
    Checks the users category to see if it contains words like brothers, brother, male, female, sisters, mothers
    and if it does return the appropriate gender either male or female
    """

    category_lower = category.lower()
    if any(keyword in category_lower for keyword in ["brother", "brothers", "male"]):
        return "male"
    elif any(
        keyword in category_lower
        for keyword in ["sister", "sisters", "mother", "mothers", "female"]
    ):
        return "female"
    return "unspecified"

result = gender_classifier("Married (female)")
print(result)