from django import forms
from data.loader import get_all_crops, get_all_states, get_all_soil_types
from data.vegetable_data import ITEM_TYPES, RANKING_MODES


class FarmAnalysisForm(forms.Form):
    state = forms.ChoiceField(
        label="State / UT",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )
    crop = forms.ChoiceField(
        label="Crop",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )
    land_size_acres = forms.FloatField(
        label="Land Size (Acres)",
        min_value=0.1,
        max_value=10000,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "e.g. 2.5",
            "step": "any",
        }),
    )
    soil_type = forms.ChoiceField(
        label="Soil Type",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )
    irrigation = forms.ChoiceField(
        label="Irrigation Availability",
        choices=[("yes", "Available"), ("no", "Not Available")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
    )
    investment_capacity = forms.FloatField(
        label="Investment Capacity (₹)",
        min_value=100,
        max_value=100_000_000,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "e.g. 50000",
            "step": "any",
        }),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        state_choices = [("", "— Select State —")] + [(s, s) for s in get_all_states()]
        crop_choices = [("", "— Select Crop —")] + [(c, c) for c in get_all_crops()]
        soil_choices = [("", "— Select Soil Type —")] + [(s, s.title()) for s in get_all_soil_types()]
        self.fields["state"].choices = state_choices
        self.fields["crop"].choices = crop_choices
        self.fields["soil_type"].choices = soil_choices


class CropCompareForm(forms.Form):
    state = forms.ChoiceField(
        label="State / UT",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )
    land_size_acres = forms.FloatField(
        label="Land Size (Acres)",
        min_value=0.1, max_value=10000,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "e.g. 2.5", "step": "any",
        }),
    )
    soil_type = forms.ChoiceField(
        label="Soil Type",
        widget=forms.Select(attrs={"class": "form-select form-select-lg"}),
    )
    investment_capacity = forms.FloatField(
        label="Investment Capacity (₹)",
        min_value=100, max_value=100_000_000,
        widget=forms.NumberInput(attrs={
            "class": "form-control form-control-lg",
            "placeholder": "e.g. 50000", "step": "any",
        }),
    )
    mode = forms.ChoiceField(
        label="Ranking Mode",
        choices=RANKING_MODES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial="balanced",
    )
    filter_type = forms.ChoiceField(
        label="Show",
        choices=[("All", "All Items"), ("Crop", "Crops Only"),
                 ("Vegetable", "Vegetables Only")],
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        initial="All",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        state_choices = [("", "— Select State —")] + [(s, s) for s in get_all_states()]
        soil_choices  = [("", "— Select Soil Type —")] + [(s, s.title()) for s in get_all_soil_types()]
        self.fields["state"].choices = state_choices
        self.fields["soil_type"].choices = soil_choices
