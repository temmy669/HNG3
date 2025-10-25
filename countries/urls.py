from django.urls import path
from .views import RefreshCountriesView, ListCountriesView, RetrieveCountryView, DeleteCountryView, StatusView, ImageView

urlpatterns = [
    path('countries/refresh', RefreshCountriesView.as_view(), name='refresh-countries'),
    path('countries', ListCountriesView.as_view(), name='list-countries'),
    path('countries/image', ImageView.as_view(), name='image'),
    path('countries/<str:name>', RetrieveCountryView.as_view(), name='retrieve-country'),
    path('countries/<str:name>', DeleteCountryView.as_view(), name='delete-country'),
    path('status', StatusView.as_view(), name='status'),
    
]
