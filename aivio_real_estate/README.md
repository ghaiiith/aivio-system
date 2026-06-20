# AIVIO Real Estate Management

`aivio_real_estate` is a clean Odoo 19 Community module rebuilt from the uploaded real estate module idea, with a safer and more maintainable structure.

## Main Features

- Regions and project/building hierarchy.
- Floors and floor plan images.
- Real estate units with status, pricing, specifications, amenities, image gallery, linked product, and chatter.
- Reservations with expiry date, deposit amount, and contract creation.
- Unified ownership/rental contracts.
- Installment schedule generation.
- Customer invoice creation from installments using `account.move`.
- Partner smart buttons for real estate reservations and contracts.
- Product template link for real estate unit products.
- Odoo 19-style XML using `<list>` views and inline modifiers.
- Manager and user security groups.

## Installation

1. Copy `aivio_real_estate` into your Odoo custom addons path.
2. Restart Odoo.
3. Update Apps List.
4. Install **AIVIO Real Estate Management**.
5. Assign users to **AIVIO Real Estate / User** or **AIVIO Real Estate / Manager**.
6. Configure the fallback income account from **Real Estate > Configuration > Settings**.

## Suggested Flow

1. Create Regions.
2. Create Projects / Buildings.
3. Create Floors.
4. Create Units.
5. Create a Reservation.
6. Confirm the Reservation.
7. Create a Contract.
8. Generate Installments.
9. Confirm the Contract.
10. Create customer invoices from installments.

## Notes

The module intentionally removes old website/gallery controllers, backup files, cached Python files, old static gallery assets, and the Enterprise-only `account_accountant` dependency.


## 19.0.1.0.1

- Fixed Odoo 19 security group definition by replacing the removed `res.groups.category_id` usage with the new `res.groups.privilege` / `privilege_id` structure.
- Added module-owned settings action for Odoo 19 because `base.action_res_config_settings` is not available in this build.
