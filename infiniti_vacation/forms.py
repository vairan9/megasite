from django import forms


class ReservationRequestForm(forms.Form):
    guest_name = forms.CharField(label="Imie i nazwisko", max_length=120)
    guest_email = forms.EmailField(label="E-mail")
    guest_phone = forms.CharField(label="Telefon", max_length=40)
    note = forms.CharField(
        label="Uwagi do pobytu",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

