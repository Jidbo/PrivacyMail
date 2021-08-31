from django import forms
from django_countries.widgets import CountrySelectWidget
from identity.models import Service
from mailfetcher.models import Thirdparty


class ServiceMetadataForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ('country_of_origin', 'sector')
        widgets = {'country_of_origin': CountrySelectWidget(layout='{widget}')}


class EmbedMetadataForm(forms.ModelForm):
    class Meta:
        model = Thirdparty
        fields = ('country_of_origin', 'sector')
        widgets = {'country_of_origin': CountrySelectWidget(layout='{widget}')}
