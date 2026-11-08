# ParkBuddy

Smart geospatial parking discovery and real-time slot reservation system built with **GeoDjango**, **PostGIS**, and an integrated **PyTorch Nepali NLP assistant**.

<br/>

[![GeoDjango](https://img.shields.io/badge/GeoDjango-5.1-005222?style=flat-square&logo=django&logoColor=f7f5f1)](https://github.com/nikace7/parkbuddy)
&nbsp;
[![PostGIS](https://img.shields.io/badge/PostGIS-Spatial_Database-005222?style=flat-square&logo=postgresql&logoColor=f7f5f1)](https://github.com/nikace7/parkbuddy)
&nbsp;
[![PyTorch NLP](https://img.shields.io/badge/PyTorch-Nepali_Chatbot-15181e?style=flat-square&logo=pytorch&logoColor=f7f5f1)](https://github.com/nikace7/parkbuddy)
&nbsp;
[![Payments](https://img.shields.io/badge/Payments-Khalti_Nepal-007136?style=flat-square)](https://khalti.com)
&nbsp;
[![Tailwind CSS](https://img.shields.io/badge/TailwindCSS-v3-15181e?style=flat-square&logo=tailwindcss&logoColor=f7f5f1)](https://tailwindcss.com)
&nbsp;
[![Async Tasks](https://img.shields.io/badge/Celery_·_Redis-Async_Tasks-15181e?style=flat-square&logo=redis&logoColor=f7f5f1)](https://docs.celeryq.dev)

---

### Overview

Urban drivers often spend critical time circling commercial districts searching for available parking. **ParkBuddy** solves this with an end-to-end platform that indexes parking lots using geospatial coordinates, calculates real-time spherical distances from a driver's live GPS location, handles reserved slot allocation, verifies payments via Khalti, and provides an on-demand AI assistant trained to understand user queries in Nepali and English.

---

### Core Architecture & Technical Highlights

```
+------------------------------------------------------------------------+
|                          Driver Client (Web)                           |
|       Leaflet Maps · GPS Location · Slot Selection · OTP Login         |
+-----------------------------------+------------------------------------+
                                    |
            REST APIs / Form Posts  |  WebSocket / Async Events
                                    v
+------------------------------------------------------------------------+
|                            GeoDjango Core                              |
|   - Spatial queries via PostGIS Distance function                      |
|   - Slot reservation & state machine (Available / Booked / Occupied)   |
|   - Khalti payment verification & callback reconciliation              |
+--------------------+------------------------------+--------------------+
                     |                              |
                     v                              v
+----------------------------------+  +----------------------------------+
|      PostGIS / PostgreSQL        |  |        PyTorch Assistant         |
|  - PointField (WGS 84, SRID 4326)|  |  - Nepali Intent Classifier      |
|  - Real-time radius queries      |  |  - Neural net intent routing     |
+----------------------------------+  +----------------------------------+
```

#### 1. Geospatial Discovery Engine (PostGIS + GeoDjango)
- **Spatial Indexing:** Parking lot coordinates are stored as spherical geography objects (`PointField(geography=True, srid=4326)`).
- **Proximity Filtering:** Instead of naive rectangular bounding boxes, queries execute native spatial distance calculations using GeoDjango's `Distance` function:
  ```python
  def find_nearest_parking_spaces(user_latitude, user_longitude, max_distance_km=2, vehicle_type=None):
      user_location = Point(user_longitude, user_latitude, srid=4326)
      query = ParkingSpace.objects.filter(available=True)
      if vehicle_type:
          query = query.filter(vehicle_type=vehicle_type)

      return query.annotate(
          distance=Distance('location', user_location)
      ).filter(distance__lt=max_distance_km * 1000).order_by('distance')
  ```

#### 2. Dual-Role Operational Workflows
- **Drivers:** Search nearby spaces, filter by vehicle type (Car vs. Bike), reserve specific slot numbers, specify expected arrival and exit durations, and complete in-app payment.
- **Parking Managers:** Register new facilities, configure capacity, upload site photographs, define tiered hourly/half-hourly rates, and monitor real-time on-site slot occupancy (`on_site_occupied_slots_count`).

#### 3. Integrated Nepali Conversational Assistant
- Located in `chatbot_main/`, featuring a PyTorch feedforward neural network trained on custom intent sets (`new_intents.json`).
- Handles bilingual tokenization, bag-of-words vectorization, and intent classification to answer driver inquiries regarding space availability, rates, and operating policies.

#### 4. Payment Gateway Reconciliation
- Integrated with **Khalti** for cashless settlements.
- Validates payment confirmation tokens through verification webhooks before transitioning slot bookings from provisional holds to confirmed reservations.

---

### Project Structure

```
parkbuddy/
├── chatbot_main/             # PyTorch NLP conversational model
│   ├── PABs.py               # Assistant inference & response routing
│   ├── nep_train.py          # Training pipeline & intent tokenization
│   ├── new_intents.json      # Structured intent catalog (Nepali/English)
│   └── best_chatbotNep.pth   # Pre-trained neural network weights
├── parkbuddy/                # Django project root
│   ├── settings.py           # GeoDjango, GDAL, PostGIS configuration
│   ├── urls.py               # Top-level URL routing
│   └── wsgi.py / asgi.py
├── theme/                    # Main application & UI layer (django-tailwind)
│   ├── models.py             # ParkingSpace, ParkingSlot, ParkingBooking, Payment
│   ├── views.py              # Spatial queries, booking views, payment handling
│   ├── urls.py               # Route endpoints
│   └── templates/            # Tailwind-styled responsive templates
├── seed_parking_spaces.py    # Database seeding utility for demo locations
├── manage.py
└── requirements.txt
```

---

### Getting Started

#### Prerequisites
- **Python 3.11 or 3.12** (spaCy 3.7 has no wheels for 3.13)
- **PostgreSQL 15+** with the **PostGIS** extension, or **Docker** to run both in a container
- **GDAL and GEOS** geospatial C libraries installed on your operating system (e.g., via OSGeo4W on Windows or `libgdal-dev` on Linux). On Windows, add `C:\OSGeo4W\bin` to `PATH`, and if your GDAL is newer than Django looks for (3.9 or later with Django 5.1), set `GDAL_LIBRARY_PATH` as shown in `.env.example`
- **Node.js 18+** (for Tailwind CSS build tooling)

#### 1. Clone & Set Up Virtual Environment
```bash
git clone https://github.com/nikace7/parkbuddy.git
cd parkbuddy

python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

This includes PyTorch and the spaCy English model for the chatbot, so the first install is a large download.

#### 2. Configure Database & PostGIS
Start PostGIS in a container:
```bash
docker run -d --name parkbuddy-db -e POSTGRES_PASSWORD=change-me -e POSTGRES_DB=ParkBuddy -p 5432:5432 postgis/postgis:15-3.4
```

Or create a database on your own PostgreSQL server and enable the extension:
```sql
CREATE DATABASE "ParkBuddy";
\c "ParkBuddy";
CREATE EXTENSION postgis;
```

Copy `.env.example` to `.env` and fill in the values. `DB_PASSWORD` must match your database, and `DB_HOST` and `DB_PORT` change where it is reached. The placeholder values are enough to run the app locally, because the Khalti and Sparrow keys are only used when paying or sending a login OTP. `.env` is git-ignored, so never commit it. Debug mode is off by default: set `DJANGO_DEBUG=True` in `.env` on your own machine, because static files and uploads are only served in debug mode.

#### 3. Run Migrations & Seed Data
```bash
python manage.py migrate
python seed_parking_spaces.py
```

#### 4. Build Styles & Launch Development Server
```bash
# Once, to install the Tailwind tooling:
python manage.py tailwind install

# In a separate terminal, watch Tailwind styles:
python manage.py tailwind start

# Run the Django application server:
python manage.py runserver
```

Navigate to `http://127.0.0.1:8000` in your browser.

#### 5. Run the Tests
```bash
python manage.py test
```

---

### Engineering Principles

- **Spatial Correctness:** Enforce spatial constraints at the database level using PostGIS rather than floating-point math in application memory.
- **Fail-Safe Booking Locks:** Ensure slot holds prevent double-booking race conditions during active driver check-outs.
- **Domain Adaptation:** Localization matters; combining Nepali NLP with local payment gateways (Khalti) addresses real municipal infrastructure realities.

---

### Author

**Nikesh Khatri**  
Software Engineer — Kathmandu, Nepal  
- Website: [nikeshkhatri.com.np](https://nikeshkhatri.com.np)  
- GitHub: [@nikace7](https://github.com/nikace7)  
- LinkedIn: [Nikesh Khatri](https://www.linkedin.com/in/nikesh-khatri-2b04582a9/)  
- Email: [khatrinikace@gmail.com](mailto:khatrinikace@gmail.com)

Built with [Bijay Karki](https://github.com/bkarki010), who built the sign-in screen, the map popup, and the slot details, payment and confirmation pages. I built the rest: the models, PostGIS search, booking, Khalti payments and the Nepali chatbot.
