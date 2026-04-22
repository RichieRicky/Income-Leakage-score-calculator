def calculate_score(value):
    if value < 1:
        score = 70 * (value / 1)
        rating = "Unsatisfactory"

    elif value <= 5:
        score = 71 + (value - 1) * (90 - 71) / (5 - 1)
        rating = "Needs Improvement"

    elif value <= 20:
        score = 91 + (value - 6) * (105 - 91) / (20 - 6)
        rating = "Met Expectations"

    elif value <= 100:
        score = 106 + (value - 21) * (124 - 106) / (100 - 21)
        rating = "Exceeds Expectations"

    else:
        # Calculate score but cap at 200%
        score = 125 + (value - 100) * (200 - 125) / (200 - 100)
        score = min(score, 200)
        rating = "Exceptional"

    return round(score, 2), rating


# ---- User input ----
try:
    value = float(input("Enter score value in millions: "))
    score, rating = calculate_score(value)
    print(f"\nResult:")
    print(f"Rating: {rating}")
    print(f"Percentage Score: {score}%")

except ValueError:
    print("Please enter a valid numeric value.")