from django import forms
from .models import Child, Ingredient, UserProfile

class AddChildForm(forms.ModelForm):
    class Meta:
        model = Child
        fields = ['name', 'dob', 'likes_ingredients', 'dislikes_ingredients', 'allergies']
        widgets = {
            'dob': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'likes_ingredients': forms.SelectMultiple(
                attrs={'class': 'form-control searchable-dropdown', 'data-placeholder': 'Search and select ingredients'}
            ),
            'dislikes_ingredients': forms.SelectMultiple(
                attrs={'class': 'form-control searchable-dropdown', 'data-placeholder': 'Search and select ingredients'}
            ),
        }
        labels = {
            'name': "Munchkin's Name",
            'dob': 'Date of Birth',
            'likes_ingredients': 'Likes Ingredients',
            'dislikes_ingredients': 'Dislikes Ingredients',
            'allergies': 'Allergies (Optional)',
        }

#class UserPreferencesForm(forms.Form):
 #   MEAL_VARIETY_CHOICES = UserProfile.MEAL_VARIETY_CHOICES
  #  FAVORITE_RECIPE_FREQUENCY_CHOICES = UserProfile.FAVORITE_RECIPE_FREQUENCY_CHOICES

    # Individual fields for each meal type
   # meal_variety_breakfast = forms.ChoiceField(choices=MEAL_VARIETY_CHOICES, required=False, label="Breakfast Variety")
    #meal_variety_lunch = forms.ChoiceField(choices=MEAL_VARIETY_CHOICES, required=False, label="Lunch Variety")
    #meal_variety_dinner = forms.ChoiceField(choices=MEAL_VARIETY_CHOICES, required=False, label="Dinner Variety")
    #meal_variety_snack = forms.ChoiceField(choices=MEAL_VARIETY_CHOICES, required=False, label="Snack Variety")

    # Regular field for favorite recipe frequency
    #favorite_recipe_frequency = forms.ChoiceField(
    #    choices=FAVORITE_RECIPE_FREQUENCY_CHOICES, required=False, label="Favorite Recipe Frequency"
    #)

    #def save(self, user_profile):
        # Map individual fields to the JSONField
     #   user_profile.meal_variety = {
      #      "breakfast": self.cleaned_data.get("meal_variety_breakfast", "medium"),
       #     "lunch": self.cleaned_data.get("meal_variety_lunch", "medium"),
        #    "dinner": self.cleaned_data.get("meal_variety_dinner", "medium"),
         #   "snack": self.cleaned_data.get("meal_variety_snack", "medium"),
        #}
        # Save the favorite recipe frequency
        #user_profile.favorite_recipe_frequency = self.cleaned_data.get("favorite_recipe_frequency", "frequent")
        #user_profile.save()

class WithinWeekPreferencesForm(forms.Form):
    MEAL_VARIETY_CHOICES = [
        ("no", "No Variety"),  # Add the "No Variety" option
        ("low", "Low Variety"),
        ("medium", "Medium Variety"),  # Default remains "Medium Variety"
        ("high", "High Variety"),
    ]

    meal_variety_breakfast = forms.ChoiceField(choices=MEAL_VARIETY_CHOICES, required=False, label="Breakfast Variety")
    meal_variety_lunch = forms.ChoiceField(choices=MEAL_VARIETY_CHOICES, required=False, label="Lunch Variety")
    meal_variety_dinner = forms.ChoiceField(choices=MEAL_VARIETY_CHOICES, required=False, label="Dinner Variety")
    meal_variety_snack = forms.ChoiceField(choices=MEAL_VARIETY_CHOICES, required=False, label="Snack Variety")

    def save(self, user_profile):
        # Ensure default is "medium" if the user doesn't explicitly select a value
        user_profile.within_week_preferences = {
            "breakfast": self.cleaned_data.get("meal_variety_breakfast", "medium"),
            "lunch": self.cleaned_data.get("meal_variety_lunch", "medium"),
            "dinner": self.cleaned_data.get("meal_variety_dinner", "medium"),
            "snack": self.cleaned_data.get("meal_variety_snack", "medium"),
        }
        user_profile.save()



class AcrossWeekPreferencesForm(forms.Form):
    VARIETY_CHOICES = [
        ("low", "Low Variety"),
        ("medium", "Medium Variety"),
        ("high", "High Variety"),
    ]

    meal_variety_breakfast = forms.ChoiceField(choices=VARIETY_CHOICES, required=False, label="Breakfast Variety")
    meal_variety_lunch = forms.ChoiceField(choices=VARIETY_CHOICES, required=False, label="Lunch Variety")
    meal_variety_dinner = forms.ChoiceField(choices=VARIETY_CHOICES, required=False, label="Dinner Variety")
    meal_variety_snack = forms.ChoiceField(choices=VARIETY_CHOICES, required=False, label="Snack Variety")

    def save(self, user_profile):
        user_profile.across_week_preferences = {
            "breakfast": self.cleaned_data.get("meal_variety_breakfast", "medium"),
            "lunch": self.cleaned_data.get("meal_variety_lunch", "medium"),
            "dinner": self.cleaned_data.get("meal_variety_dinner", "medium"),
            "snack": self.cleaned_data.get("meal_variety_snack", "medium"),
        }
        user_profile.save()

