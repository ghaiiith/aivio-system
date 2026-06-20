# Developer Notes - AIVIO Real Estate

## Technical Name

`aivio_real_estate`

## Target Version

Odoo 19 Community

## Dependencies

- `base`
- `mail`
- `web`
- `product`
- `account`

## File Map

```text
aivio_real_estate/
├── __init__.py
├── __manifest__.py
├── data/
│   ├── real_estate_data.xml
│   ├── real_estate_demo.xml
│   └── real_estate_sequences.xml
├── doc/
│   └── DEVELOPER.md
├── models/
│   ├── amenity.py
│   ├── contract.py
│   ├── floor.py
│   ├── installment.py
│   ├── product_template.py
│   ├── project.py
│   ├── region.py
│   ├── reservation.py
│   ├── res_config_settings.py
│   ├── res_partner.py
│   ├── unit.py
│   ├── unit_image.py
│   └── unit_type.py
├── report/
│   └── real_estate_contract_report.xml
├── security/
│   ├── ir.model.access.csv
│   └── real_estate_security.xml
├── static/description/
│   ├── banner.png
│   ├── icon.png
│   └── index.html
└── views/
    ├── amenity_views.xml
    ├── contract_views.xml
    ├── floor_views.xml
    ├── installment_views.xml
    ├── product_template_views.xml
    ├── project_views.xml
    ├── real_estate_menus.xml
    ├── region_views.xml
    ├── reservation_views.xml
    ├── res_config_settings_views.xml
    ├── res_partner_views.xml
    ├── unit_type_views.xml
    └── unit_views.xml
```

## Model Summary

- `aivio.real.estate.region`: hierarchical regions.
- `aivio.real.estate.project`: project/building master.
- `aivio.real.estate.floor`: project floor plan records.
- `aivio.real.estate.unit`: real estate unit inventory.
- `aivio.real.estate.unit.image`: image carousel/gallery lines for each unit.
- `aivio.real.estate.reservation`: reservation workflow.
- `aivio.real.estate.contract`: ownership/rental contract workflow.
- `aivio.real.estate.installment`: contract installment schedule and invoice creation.
- `aivio.real.estate.unit.type`: configurable unit categories.
- `aivio.real.estate.amenity`: configurable unit amenities.

## Design Choices

- A unified contract model is used for both sale and rental to avoid duplicate logic.
- Unit products are created automatically and marked with `is_real_estate_unit`.
- Invoice creation uses standard customer invoices (`account.move` with `move_type='out_invoice'`).
- Fallback income account is configurable from settings.
- Old unnecessary assets and controllers were not migrated.

## Important Extension Points

- Add more contract states in `models/contract.py` if legal approval or audit workflows are needed.
- Add separate printed QWeb templates for rental and ownership if each has a different legal layout.
- Add automated cron for expired reservations if required.
- Add portal/website only as a separate optional module to keep this core module clean.
