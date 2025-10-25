from rest_framework import serializers
from .models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Convert Decimal fields to float with specified decimal places
        if representation.get('exchange_rate') is not None:
            representation['exchange_rate'] = round(float(representation['exchange_rate']), 2)
        if representation.get('estimated_gdp') is not None:
            representation['estimated_gdp'] = round(float(representation['estimated_gdp']), 1)
        return representation

    def validate(self, data):
        errors = {}
        if not data.get('name'):
            errors['name'] = 'is required'
        if not data.get('population'):
            errors['population'] = 'is required'
        if not data.get('currency_code'):
            errors['currency_code'] = 'is required'
        if errors:
            raise serializers.ValidationError({'error': 'Validation failed', 'details': errors})
        return data
