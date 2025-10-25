from rest_framework import serializers
from .models import Country

class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = '__all__'

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
