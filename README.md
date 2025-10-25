# Country Currency & Exchange API

A RESTful API built with Django and Django REST Framework that fetches country data from external APIs, stores it in a MySQL database, and provides CRUD operations with exchange rate calculations and image generation.

## Features

- Fetch country data from restcountries.com
- Retrieve exchange rates from open.er-api.com
- Calculate estimated GDP with random multipliers
- Store data in MySQL database
- CRUD operations for countries
- Filtering and sorting capabilities
- Generate summary images on refresh
- Comprehensive error handling

## Endpoints

- `POST /countries/refresh` - Refresh country data and exchange rates
- `GET /countries` - List all countries with optional filters (?region=Africa&currency=NGN&sort=gdp_desc)
- `GET /countries/{name}` - Get specific country by name
- `DELETE /countries/{name}/delete` - Delete a country by name
- `GET /status` - Get total countries and last refresh timestamp
- `GET /countries/image` - Serve summary image

## Setup Instructions

### Prerequisites

- Python 3.8+
- MySQL Server
- Virtual environment (recommended)

### Installation

1. Clone the repository:

   ```bash
   git clone <repo-url>
   cd HNG3
   ```

2. Create and activate virtual environment:

   ```bash
   python -m venv venv
   venv\Scripts\activate  # On Windows
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Set up MySQL database:

   - Create a database named `countries_db`
   - Update `.env` file with your MySQL credentials

5. Run migrations:

   ```bash
   python manage.py makemigrations countries
   python manage.py migrate
   ```

6. Run the server:
   ```bash
   python manage.py runserver
   ```

## Environment Variables

Create a `.env` file in the project root with:

```
DB_NAME=countries_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

## Usage

### Refresh Data

```bash
curl -X POST http://localhost:8000/countries/refresh
```

### List Countries

```bash
curl http://localhost:8000/countries?region=Africa&sort=gdp_desc
```

### Get Status

```bash
curl http://localhost:8000/status
```

## Deployment

This API can be deployed to platforms like Railway, Heroku, or AWS. Ensure MySQL is configured in production.

## Testing

Test the endpoints using tools like Postman or curl. Verify data fetching, CRUD operations, and image generation.

## Notes

- External API calls have 10-second timeouts
- GDP calculation uses random multipliers (1000-2000) on each refresh
- Images are generated in `media/cache/summary.png`
- Case-insensitive country name matching
