# Closeknit

A community-based platform for sharing items and subscriptions within your trusted circles.

## Why Closeknit exists

How many times have you bought something expensive, used it once, and then watched it collect dust? A power drill for that weekend project. A camera for a vacation. A book you'll never read again.

Meanwhile, your friend across town bought the exact same thing last month and is facing the same problem.

This is wasteful. And expensive. And completely unnecessary.

Closeknit solves this by creating trusted sharing circles where you can borrow what you need and lend what you don't use. Think of it as a private marketplace for your friend groups, family, and close communities.

The math is simple: instead of 10 people buying 10 power drills, one person buys it and shares it with 9 others. Everyone saves money. Less stuff gets manufactured. Storage space is freed up. Communities get stronger.

## What you can share

**Physical items**: Books, electronics, tools, sports equipment, kitchen appliances, cameras, musical instruments - anything you own but don't use regularly.

**Digital subscriptions**: Netflix, Spotify, Adobe Creative Suite, gym memberships - subscriptions that support multiple users or that you're willing to share access to.

## How it works

### Communities
Create private groups for different circles in your life:
- Family members
- Close friends  
- Neighbors
- Coworkers
- Hobby groups

Each community has its own invite link. Only people you invite can see what's shared in that community.

### Items
List physical things you own and are willing to lend out. Set them as available to specific communities. When someone wants to borrow something, you can create a lease with start and end dates.

### Subscriptions
Share access to digital services you're already paying for. Mark which communities can access them. Perfect for family plans or services with multiple user slots.

### Requests
Can't find what you need? Post a request to your communities. Maybe someone has exactly what you're looking for but hasn't listed it yet.

### Leases
Track who has borrowed what and when it's due back. The system prevents double-booking and helps you keep track of your stuff.

## Technical details

Closeknit is built with Django and uses a PostgreSQL database. The frontend uses Bulma CSS framework for clean, responsive design.

**Key technologies:**
- Django
- PostgreSQL for data persistence
- Google OAuth for authentication
- Bulma CSS for styling
- WhiteNoise for static file serving
- Gunicorn for production deployment

**Architecture:**
- `Community` model manages private groups with invite-based membership
- `Item` model handles physical objects with sharing permissions
- `Subscription` model manages digital service sharing
- `Lease` model tracks borrowing periods with overlap prevention
- `Request` model enables community members to ask for specific items

## How to run

### Prerequisites
- Python 3.12+
- PostgreSQL
- Google OAuth credentials (for authentication)

### Local development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd closeknit
   ```

2. **Set up Python environment**
   ```bash
   # Using uv (recommended)
   uv sync
   ```

3. **Configure environment variables**
   Create a `.env` file in the project root:
   ```bash
   SECRET_KEY=your-secret-key-here
   DATABASE_URL=postgresql://username:password@localhost:5432/closeknit
   GOOGLE_AUTH_CLIENT_ID=your-google-oauth-client-id
   GOOGLE_AUTH_CLIENT_SECRET=your-google-oauth-client-secret
   ```

4. **Set up the database**
   ```bash
   # Create PostgreSQL database
   createdb closeknit
   
   # Run migrations
   python manage.py migrate
   ```

5. **Create a superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

The application will be available at `http://localhost:8000`.

### Google OAuth setup

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API
4. Create OAuth 2.0 credentials
5. Add `http://localhost:8000` to authorized origins
6. Add `http://localhost:8000/accounts/google/login/callback/` to authorized redirect URIs
7. Copy the client ID and secret to your `.env` file

### Production deployment

The application is configured for deployment on platforms like Railway, Heroku, or any service that supports Django applications.

**Environment variables for production:**
```bash
DJANGO_ENV=production
SECRET_KEY=your-production-secret-key
DATABASE_URL=your-production-database-url
GOOGLE_AUTH_CLIENT_ID=your-google-oauth-client-id
GOOGLE_AUTH_CLIENT_SECRET=your-google-oauth-client-secret
BREVO_API_KEY=your-email-service-key (optional)
```

**Docker deployment:**
```bash
# Build the image
docker build -t closeknit .

# Run with environment variables
docker run -p 8000:8000 --env-file .env closeknit
```

### Database migrations

When you make model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

### Static files

For production, collect static files:
```bash
python manage.py collectstatic
```


## Contributing

This is currently an beta project. If you find bugs or have suggestions, feel free to:
- Open an issue
- Submit a pull request
- Reach out directly

---

*Built by [Bharat Kalluri](https://bharatkalluri.com) - because sharing should be simple.*