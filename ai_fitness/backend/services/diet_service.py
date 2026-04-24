"""
backend/services/diet_service.py
"""
from __future__ import annotations
from typing import Dict, List, Tuple
from models import DietRequest, DietResponse

_ACTIVITY_MULTIPLIERS: Dict[str, float] = {
    "sedentary": 1.2, "light": 1.375, "moderate": 1.55,
    "active": 1.725, "very_active": 1.9,
}

_FOODS_TO_EAT: Dict[Tuple[str, str], List[str]] = {
    ("Underweight", "gain"):      ["Whole milk", "Nut butters", "Brown rice", "Eggs", "Avocado", "Oats", "Banana", "Chicken thigh"],
    ("Normal weight", "maintain"):["Grilled chicken", "Salmon", "Quinoa", "Vegetables", "Greek yogurt", "Berries", "Almonds", "Sweet potato"],
    ("Normal weight", "lose"):    ["Lean chicken breast", "Broccoli", "Spinach", "Lentils", "Egg whites", "Green tea", "Cucumber"],
    ("Normal weight", "gain"):    ["Whole eggs", "Oats", "Milk", "Brown rice", "Tuna", "Cottage cheese"],
    ("Overweight", "lose"):       ["Leafy greens", "Grilled fish", "Lentils", "Chickpeas", "Berries", "Green tea", "Cucumber", "Tofu"],
    ("Overweight", "maintain"):   ["Lean protein", "Vegetables", "Whole grains", "Low-fat dairy", "Legumes"],
    ("Obese", "lose"):            ["Non-starchy vegetables", "Grilled chicken breast", "Egg whites", "Water", "Green tea", "Legumes", "Berries"],
}

_FOODS_TO_AVOID: Dict[Tuple[str, str], List[str]] = {
    ("Underweight", "gain"):      ["Diet sodas", "Excessive coffee", "Very low-calorie foods"],
    ("Normal weight", "maintain"):["Processed snacks", "Excessive sugar", "Fast food"],
    ("Normal weight", "lose"):    ["Fried food", "Sugary drinks", "Refined carbs", "Alcohol"],
    ("Normal weight", "gain"):    ["Low-calorie diet foods", "Excessive cardio without eating"],
    ("Overweight", "lose"):       ["Fried food", "Sugary beverages", "White bread", "Fast food", "Alcohol", "Chips"],
    ("Overweight", "maintain"):   ["Refined sugar", "Processed snacks", "Excessive sodium"],
    ("Obese", "lose"):            ["All fried food", "Sugary drinks", "Candy", "White rice", "Processed meats", "Alcohol", "Fast food"],
}

_RECOMMENDATIONS: Dict[Tuple[str, str], List[str]] = {
    ("Underweight", "gain"):      ["Eat 5-6 meals a day with calorie-dense whole foods.", "Add a post-workout protein shake.", "Prioritise compound lifts to build lean mass."],
    ("Normal weight", "maintain"):["Maintain balanced macros with a variety of whole foods.", "Stay hydrated with 2-3 litres of water daily.", "Time protein intake around workouts for best recovery."],
    ("Normal weight", "lose"):    ["Create a moderate 300-400 kcal deficit per day.", "Eat protein-rich meals to preserve muscle while losing fat.", "Avoid liquid calories."],
    ("Normal weight", "gain"):    ["Add 300-500 kcal above TDEE consistently.", "Pair resistance training with adequate protein (1.6-2.2 g/kg)."],
    ("Overweight", "lose"):       ["Aim for a sustainable 500 kcal/day deficit.", "Prioritise high-fibre, high-protein meals to control hunger.", "Replace refined carbs with vegetables and legumes.", "Walk at least 8,000 steps daily."],
    ("Overweight", "maintain"):   ["Focus on food quality rather than restriction.", "Reduce ultra-processed food intake."],
    ("Obese", "lose"):            ["A 500-750 kcal/day deficit is safe and sustainable.", "Consider consulting a registered dietitian.", "Start with low-impact exercise (swimming, walking).", "Cut sugary drinks immediately.", "Track food intake to maintain awareness."],
}


def _bmi_category(bmi: float) -> str:
    if bmi < 18.5: return "Underweight"
    if bmi < 25.0: return "Normal weight"
    if bmi < 30.0: return "Overweight"
    return "Obese"


def _bmr(weight_kg: float, height_cm: float, age: int, gender: str) -> float:
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + 5 if gender.lower() == "male" else base - 161


def _target_calories(tdee: float, goal: str) -> float:
    if goal == "lose": return max(1200.0, tdee - 500.0)
    if goal == "gain": return tdee + 400.0
    return tdee


def _macros(target_kcal: float) -> Tuple[float, float, float]:
    return (
        round(target_kcal * 0.30 / 4, 1),
        round(target_kcal * 0.45 / 4, 1),
        round(target_kcal * 0.25 / 9, 1),
    )


def _fallback(d: dict, key: tuple, default: list) -> list:
    return d.get(key, d.get((key[0], "maintain"), default))


def compute_diet(req: DietRequest) -> DietResponse:
    height_m    = req.height_cm / 100.0
    bmi         = round(req.weight_kg / (height_m ** 2), 1)
    category    = _bmi_category(bmi)
    bmr         = round(_bmr(req.weight_kg, req.height_cm, req.age, req.gender), 1)
    multiplier  = _ACTIVITY_MULTIPLIERS.get(req.activity_level, 1.55)
    tdee        = round(bmr * multiplier, 1)
    target_kcal = round(_target_calories(tdee, req.goal), 1)
    protein_g, carbs_g, fat_g = _macros(target_kcal)
    key = (category, req.goal)

    return DietResponse(
        user_id=req.user_id, bmi=bmi, bmi_category=category, bmr=bmr,
        tdee=tdee, target_calories=target_kcal, protein_g=protein_g,
        carbs_g=carbs_g, fat_g=fat_g,
        recommendations=_fallback(_RECOMMENDATIONS, key, ["Eat balanced, whole-food meals."]),
        foods_to_eat   =_fallback(_FOODS_TO_EAT,    key, ["Lean protein", "Vegetables", "Whole grains"]),
        foods_to_avoid =_fallback(_FOODS_TO_AVOID,  key, ["Fried food", "Sugary drinks"]),
    )
