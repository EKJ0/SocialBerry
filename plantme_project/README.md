# PlantMe

PlantMe is a website concept for a person building habits (client) and a trusted person that turns healthy habits into a plant-growing journey.

## What is included

- Flask app structure
- Templates and static assets
- Trusted person dashboard
- Client dashboard
- Task management screens
- Garden / gamification page
- Messaging page
- Responsive styling
- Mock seed data for demo purposes

## Main idea implemented

- A trusted person supports accountability
- Clients complete goals and share updates
- Completed tasks give growth points
- Plants evolve from seed to sprout to full plant
- Water reminders support hydration habits
- Outdoor activity can give sunlight bonuses
- Walking proof can be shared as optional evidence
- Role-based screens for trusted person and client

## Run locally

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open:

```bash
http://127.0.0.1:5000
```

## Notes

This version is a polished prototype with mock data, not a production backend.
To make it production-ready, the next step would be adding:

- authentication
- database models
- file upload storage
- real chat
- notifications
- GPS / map integrations
- payment system for buying new plants or themes
