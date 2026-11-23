from django import forms
from apps.permits.models import PermitType
from .models import BoothTier


class BoothTierForm(forms.ModelForm):
    class Meta:
        model = BoothTier
        fields = ("name", "booth_category", "max_width_m", "max_depth_m",
                  "power_watts", "fee", "slots_total", "guidelines", "required_permits")
        labels = {"max_width_m": "Max width (m)", "max_depth_m": "Max depth (m)",
                  "power_watts": "Power provided (watts)", "fee": "Booth fee (PHP)",
                  "slots_total": "Number of slots", "required_permits": "Vendor documents required"}
        help_texts = {"power_watts": "0 means no power provided."}
        widgets = {"guidelines": forms.Textarea(attrs={"rows": 3}),
                   "required_permits": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["required_permits"].queryset = PermitType.objects.filter(scope="VENDOR").order_by("name")
        self.fields["required_permits"].required = False

    def clean(self):
        cleaned = super().clean()
        for name in ("max_width_m", "max_depth_m"):
            if cleaned.get(name) is not None and cleaned[name] <= 0:
                self.add_error(name, "Must be greater than zero.")
        if cleaned.get("slots_total") is not None and cleaned["slots_total"] < 1:
            self.add_error("slots_total", "Offer at least one slot.")
        return cleaned