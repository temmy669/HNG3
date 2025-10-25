from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse
import requests
import random
from PIL import Image, ImageDraw, ImageFont
import os
from datetime import datetime
from .models import Country
from .serializers import CountrySerializer
from django.conf import settings

class RefreshCountriesView(APIView):
    def post(self, request):
        try:
            # Fetch countries data
            countries_response = requests.get(settings.COUNTRY_DATA_API, timeout=10)
            countries_response.raise_for_status()
            countries_data = countries_response.json()

            # Fetch exchange rates
            rates_response = requests.get(settings.EXCHANGE_RATE_API, timeout=10)
            rates_response.raise_for_status()
            rates_data = rates_response.json()
            exchange_rates = rates_data.get('rates', {})

            with transaction.atomic():
                countries_to_create = []
                countries_to_update = []

                for country in countries_data:
                    name = country.get('name')
                    if not name:
                        continue

                    capital = country.get('capital')
                    region = country.get('region')
                    population = country.get('population')
                    flag_url = country.get('flag')

                    currencies = country.get('currencies', [])
                    currency_code = None
                    if currencies:
                        currency_code = currencies[0].get('code')

                    exchange_rate = None
                    estimated_gdp = None
                    if currency_code and currency_code in exchange_rates:
                        exchange_rate = exchange_rates[currency_code]
                        random_multiplier = random.randint(1000, 2000)
                        estimated_gdp = (population * random_multiplier) / exchange_rate

                    country_obj, created = Country.objects.get_or_create(
                        name__iexact=name,
                        defaults={
                            'name': name,
                            'capital': capital,
                            'region': region,
                            'population': population,
                            'currency_code': currency_code,
                            'exchange_rate': exchange_rate,
                            'estimated_gdp': estimated_gdp,
                            'flag_url': flag_url,
                        }
                    )

                    if not created:
                        country_obj.capital = capital
                        country_obj.region = region
                        country_obj.population = population
                        country_obj.currency_code = currency_code
                        country_obj.exchange_rate = exchange_rate
                        country_obj.estimated_gdp = estimated_gdp
                        country_obj.flag_url = flag_url
                        countries_to_update.append(country_obj)

                if countries_to_update:
                    Country.objects.bulk_update(countries_to_update, ['capital', 'region', 'population', 'currency_code', 'exchange_rate', 'estimated_gdp', 'flag_url'])

            # Generate summary image
            self.generate_summary_image()

            return Response({'message': 'Countries refreshed successfully'}, status=status.HTTP_200_OK)

        except requests.RequestException as e:
            # Determine which API failed based on the exception context
            if 'restcountries' in str(e):
                api_name = 'restcountries.com'
            elif 'open.er-api' in str(e):
                api_name = 'open.er-api.com'
            else:
                api_name = 'open.er-api.com'  # Default fallback
            return Response({'error': 'External data source unavailable', 'details': f'Could not fetch data from {api_name}'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    def generate_summary_image(self):
        total_countries = Country.objects.count()
        top_countries = Country.objects.filter(estimated_gdp__isnull=False).order_by('-estimated_gdp')[:5]
        last_refresh = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')

        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)

        try:
            font = ImageFont.truetype("arial.ttf", 20)
        except:
            font = ImageFont.load_default()

        draw.text((10, 10), f"Total Countries: {total_countries}", fill='black', font=font)
        draw.text((10, 40), f"Last Refresh: {last_refresh}", fill='black', font=font)

        y = 80
        draw.text((10, y), "Top 5 Countries by Estimated GDP:", fill='black', font=font)
        y += 30
        for country in top_countries:
            draw.text((10, y), f"{country.name}: {country.estimated_gdp}", fill='black', font=font)
            y += 30

        cache_dir = os.path.join('media', 'cache')
        os.makedirs(cache_dir, exist_ok=True)
        img_path = os.path.join(cache_dir, 'summary.png')
        img.save(img_path)

class ListCountriesView(APIView):
    def get(self, request):
        queryset = Country.objects.all()

        region = request.query_params.get('region')
        if region:
            queryset = queryset.filter(region__iexact=region)

        currency = request.query_params.get('currency')
        if currency:
            queryset = queryset.filter(currency_code__iexact=currency)

        sort = request.query_params.get('sort')
        if sort == 'gdp_desc':
            queryset = queryset.order_by('-estimated_gdp')
        elif sort == 'gdp_asc':
            queryset = queryset.order_by('estimated_gdp')
        else:
            queryset = queryset.order_by('name')

        serializer = CountrySerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class RetrieveCountryView(APIView):
    def get(self, request, name):
        try:
            country = Country.objects.get(name__iexact=name)
            serializer = CountrySerializer(country)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Country.DoesNotExist:
            return Response({'error': 'Country not found'}, status=status.HTTP_404_NOT_FOUND)

class DeleteCountryView(APIView):
    def delete(self, request, name):
        try:
            country = Country.objects.get(name__iexact=name)
            country.delete()
            return Response({'message': 'Country deleted successfully'}, status=status.HTTP_200_OK)
        except Country.DoesNotExist:
            return Response({'error': 'Country not found'}, status=status.HTTP_404_NOT_FOUND)

class StatusView(APIView):
    def get(self, request):
        total_countries = Country.objects.count()
        last_refresh = Country.objects.order_by('-last_refreshed_at').first()
        last_refreshed_at = last_refresh.last_refreshed_at.isoformat() if last_refresh else None
        return Response({
            'total_countries': total_countries,
            'last_refreshed_at': last_refreshed_at
        }, status=status.HTTP_200_OK)

class ImageView(APIView):
    def get(self, request):
        img_path = os.path.join('media', 'cache', 'summary.png')
        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                return HttpResponse(f.read(), content_type='image/png')
        else:
            return Response({'error': 'Summary image not found'}, status=status.HTTP_404_NOT_FOUND)
