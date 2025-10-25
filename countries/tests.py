from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from unittest.mock import patch, MagicMock
from .models import Country
import json
import requests

class CountryAPITestCase(APITestCase):

    def setUp(self):
        # Create sample data for testing
        self.country = Country.objects.create(
            name='Test Country',
            capital='Test Capital',
            region='Test Region',
            population=1000000,
            currency_code='USD',
            exchange_rate=1.0,
            estimated_gdp=1000000000.0,
            flag_url='https://example.com/flag.png'
        )

    @patch('countries.views.requests.get')
    def test_refresh_success(self, mock_get):
        # Mock successful responses
        mock_countries_response = MagicMock()
        mock_countries_response.raise_for_status.return_value = None
        mock_countries_response.json.return_value = [
            {
                'name': 'New Country',
                'capital': 'New Capital',
                'region': 'New Region',
                'population': 2000000,
                'flag': 'https://example.com/new_flag.png',
                'currencies': [{'code': 'EUR'}]
            }
        ]
        mock_rates_response = MagicMock()
        mock_rates_response.raise_for_status.return_value = None
        mock_rates_response.json.return_value = {'rates': {'EUR': 0.85}}

        mock_get.side_effect = [mock_countries_response, mock_rates_response]

        url = reverse('refresh-countries')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('message', response.data)
        self.assertEqual(response.data['message'], 'Countries refreshed successfully')

        # Check if new country was added
        new_country = Country.objects.filter(name__iexact='New Country').first()
        self.assertIsNotNone(new_country)
        self.assertEqual(new_country.currency_code, 'EUR')

    @patch('countries.views.requests.get')
    def test_refresh_countries_api_failure(self, mock_get):
        # Mock failure for countries API
        mock_countries_response = MagicMock()
        mock_countries_response.raise_for_status.side_effect = requests.RequestException('Connection timeout from restcountries.com')
        mock_get.return_value = mock_countries_response

        initial_count = Country.objects.count()

        url = reverse('refresh-countries')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['error'], 'External data source unavailable')
        self.assertIn('restcountries.com', response.data['details'])

        # Ensure no new countries added
        self.assertEqual(Country.objects.count(), initial_count)

    @patch('countries.views.requests.get')
    def test_refresh_rates_api_failure(self, mock_get):
        # Mock success for countries, failure for rates
        mock_countries_response = MagicMock()
        mock_countries_response.raise_for_status.return_value = None
        mock_countries_response.json.return_value = [
            {
                'name': 'New Country',
                'capital': 'New Capital',
                'region': 'New Region',
                'population': 2000000,
                'flag': 'https://example.com/new_flag.png',
                'currencies': [{'code': 'EUR'}]
            }
        ]
        mock_rates_response = MagicMock()
        mock_rates_response.raise_for_status.side_effect = requests.RequestException('API error')

        mock_get.side_effect = [mock_countries_response, mock_rates_response]

        initial_count = Country.objects.count()

        url = reverse('refresh-countries')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['error'], 'External data source unavailable')
        self.assertIn('open.er-api.com', response.data['details'])

        # Ensure no new countries added
        self.assertEqual(Country.objects.count(), initial_count)

    def test_list_countries(self):
        url = reverse('list-countries')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreater(len(response.data), 0)

    def test_list_countries_filter_region(self):
        url = reverse('list-countries') + '?region=Test Region'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for country in response.data:
            self.assertEqual(country['region'], 'Test Region')

    def test_list_countries_filter_currency(self):
        url = reverse('list-countries') + '?currency=USD'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for country in response.data:
            self.assertEqual(country['currency_code'], 'USD')

    def test_list_countries_sort_gdp_desc(self):
        url = reverse('list-countries') + '?sort=gdp_desc'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Assuming multiple countries, check order
        if len(response.data) > 1:
            self.assertGreaterEqual(response.data[0]['estimated_gdp'] or 0, response.data[1]['estimated_gdp'] or 0)

    def test_retrieve_country_success(self):
        url = reverse('retrieve-country', kwargs={'name': 'Test Country'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Country')

    def test_retrieve_country_not_found(self):
        url = reverse('retrieve-country', kwargs={'name': 'Nonexistent Country'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Country not found')

    def test_delete_country_success(self):
        url = reverse('delete-country', kwargs={'name': 'Test Country'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Country deleted successfully')
        self.assertFalse(Country.objects.filter(name__iexact='Test Country').exists())

    def test_delete_country_not_found(self):
        url = reverse('delete-country', kwargs={'name': 'Nonexistent Country'})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Country not found')

    def test_status(self):
        url = reverse('status')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_countries', response.data)
        self.assertIn('last_refreshed_at', response.data)

    @patch('countries.views.os.path.exists')
    def test_image_success(self, mock_exists):
        mock_exists.return_value = True
        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = b'fake image data'
            url = reverse('image')
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response['Content-Type'], 'image/png')

    @patch('countries.views.os.path.exists')
    def test_image_not_found(self, mock_exists):
        mock_exists.return_value = False
        url = reverse('image')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data['error'], 'Summary image not found')
