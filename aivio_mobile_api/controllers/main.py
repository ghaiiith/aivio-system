# -*- coding: utf-8 -*-
import json
import os
from datetime import timedelta

from odoo import fields, http, _
from odoo.http import request
from odoo.exceptions import AccessDenied, UserError, ValidationError
from werkzeug.wrappers import Response


class AivioMobileApiController(http.Controller):
    """REST API gateway for AIVIO mobile applications.

    The mobile apps do not use /web/dataset/call_kw, XML-RPC, or JSON-RPC.
    Each endpoint validates the mobile token, checks the computed AIVIO role,
    and then applies a role-aware domain before reading/writing records.
    """

    # -----------------------------
    # Generic helpers
    # -----------------------------
    def _payload(self):
        if request.httprequest.method == 'GET':
            return dict(request.httprequest.args)
        data = request.httprequest.get_data(as_text=True) or '{}'
        if not data:
            return {}
        try:
            payload = json.loads(data)
        except Exception:
            return {}
        # Accept both normal REST JSON and Odoo JSON-RPC style bodies:
        # {"login": "...", "password": "..."}
        # {"jsonrpc": "2.0", "params": {"db": "...", "login": "...", "password": "..."}}
        if isinstance(payload, dict) and isinstance(payload.get('params'), dict):
            params = payload.get('params') or {}
            params.setdefault('_jsonrpc', payload.get('jsonrpc'))
            return params
        return payload if isinstance(payload, dict) else {}

    def _json(self, body, status=200):
        return Response(json.dumps(body, ensure_ascii=False, default=str), status=status, content_type='application/json; charset=utf-8')

    def _ok(self, data=None, message='Done', status=200):
        return self._json({'success': True, 'message': message, 'data': data or {}, 'errors': []}, status=status)

    def _error(self, message='Error', code='error', status=200, field=None):
        return self._json({'success': False, 'message': message, 'data': None, 'errors': [{'code': code, 'field': field}]}, status=status)

    def _audit(self, user, endpoint, status='success', message=None, payload=None):
        try:
            request.env['aivio.api.audit.log'].sudo().create({
                'user_id': user.id if user else False,
                'endpoint': endpoint,
                'method': request.httprequest.method,
                'status': status,
                'ip_address': request.httprequest.remote_addr,
                'payload': json.dumps(payload or {}, ensure_ascii=False)[:5000],
                'response_message': message,
            })
        except Exception:
            # Audit must never break mobile traffic.
            pass

    def _bearer_token(self):
        auth = request.httprequest.headers.get('Authorization') or ''
        if auth.lower().startswith('bearer '):
            return auth.split(' ', 1)[1].strip()
        return request.httprequest.headers.get('X-AIVIO-Token') or request.httprequest.args.get('token')

    def _token_record(self):
        token = self._bearer_token()
        if not token:
            raise AccessDenied(_('Missing Authorization token.'))
        rec = request.env['aivio.api.token'].sudo().search([('token', '=', token), ('active', '=', True)], limit=1)
        if not rec or not rec.is_valid():
            raise AccessDenied(_('Invalid or expired token.'))
        rec.mark_used()
        return rec

    def _current_user(self):
        return self._token_record().user_id

    def _require_user(self):
        try:
            return self._current_user()
        except AccessDenied as exc:
            raise exc

    def _check_role(self, user, allowed_roles):
        if user.aivio_app_role not in allowed_roles:
            raise AccessDenied(_('You are not allowed to access this endpoint.'))

    def _call(self, func, allowed_roles=None):
        payload = self._payload()
        user = None
        try:
            user = self._require_user()
            if allowed_roles:
                self._check_role(user, allowed_roles)
            res = func(user, payload)
            self._audit(user, request.httprequest.path, 'success', 'OK', payload)
            return res
        except AccessDenied as exc:
            self._audit(user, request.httprequest.path, 'denied', str(exc), payload)
            return self._error(str(exc), 'access_denied', 403)
        except (UserError, ValidationError) as exc:
            self._audit(user, request.httprequest.path, 'error', str(exc), payload)
            return self._error(str(exc), 'validation_error')
        except Exception as exc:
            self._audit(user, request.httprequest.path, 'error', str(exc), payload)
            return self._error(str(exc), 'server_error', 500)

    def _dt(self, value):
        return fields.Datetime.to_string(value) if value else None

    def _date(self, value):
        return fields.Date.to_string(value) if value else None

    def _image_url(self, model, res_id, field='image_1920'):
        if not res_id:
            return None
        return '/web/image/%s/%s/%s' % (model, res_id, field)

    # -----------------------------
    # Serializers
    # -----------------------------
    def _serialize_unit(self, unit):
        return {
            'id': unit.id,
            'name': unit.name,
            'code': unit.code,
            'building_id': unit.project_id.id,
            'building_name': unit.project_id.name,
            'floor_id': unit.floor_id.id,
            'floor_name': unit.floor_id.name,
            'state': unit.state,
            'area': unit.area,
            'bedrooms': unit.bedrooms,
            'bathrooms': unit.bathrooms,
        }

    def _serialize_profile(self, profile):
        return {
            'id': profile.id,
            'name': profile.name,
            'partner_id': profile.partner_id.id,
            'user_id': profile.user_id.id,
            'resident_type': profile.resident_type,
            'state': profile.state,
            'phone': profile.phone,
            'mobile': profile.mobile,
            'email': profile.email,
            'primary_unit': self._serialize_unit(profile.primary_unit_id) if profile.primary_unit_id else None,
            'units': [self._serialize_unit(u) for u in profile.unit_ids],
        }

    def _serialize_visitor(self, visit):
        return {
            'id': visit.id,
            'name': visit.name,
            'visitor_name': visit.visitor_name,
            'visitor_phone': visit.visitor_phone,
            'visitor_count': visit.visitor_count,
            'visit_type': visit.visit_type,
            'reason': visit.reason,
            'resident_id': visit.resident_id.id,
            'resident_name': visit.resident_id.name,
            'unit_id': visit.unit_id.id,
            'unit_name': visit.unit_id.name,
            'building_id': visit.building_id.id,
            'building_name': visit.building_id.name,
            'gate_id': visit.gate_id.id,
            'gate_name': visit.gate_id.name,
            'valid_from': self._dt(visit.valid_from),
            'valid_to': self._dt(visit.valid_to),
            'visit_datetime': self._dt(visit.visit_datetime),
            'has_car': visit.has_car,
            'car_plate': visit.car_plate,
            'qr_token': visit.qr_token,
            'status': visit.status,
            'checked_in_at': self._dt(visit.checked_in_at),
            'checked_out_at': self._dt(visit.checked_out_at),
        }

    def _serialize_ticket(self, ticket):
        return {
            'id': ticket.id,
            'name': ticket.name,
            'subject': ticket.subject,
            'description': ticket.description,
            'resident_id': ticket.resident_id.id,
            'resident_name': ticket.resident_id.name,
            'unit_id': ticket.unit_id.id,
            'unit_name': ticket.unit_id.name,
            'category_id': ticket.category_id.id,
            'category_name': ticket.category_id.name,
            'priority': ticket.priority,
            'stage_id': ticket.stage_id.id,
            'stage_name': ticket.stage_id.name,
            'team_id': ticket.team_id.id,
            'team_name': ticket.team_id.name,
            'assigned_user_id': ticket.assigned_user_id.id,
            'assigned_user_name': ticket.assigned_user_id.name,
            'state': ticket.state,
            'expected_date': self._dt(ticket.expected_date),
            'closed_date': self._dt(ticket.closed_date),
            'average_rating': ticket.average_rating,
        }

    def _serialize_invoice(self, inv):
        return {
            'id': inv.id,
            'name': inv.name,
            'invoice_date': self._date(inv.invoice_date),
            'due_date': self._date(inv.invoice_date_due),
            'partner_id': inv.partner_id.id,
            'amount_total': inv.amount_total,
            'amount_residual': inv.amount_residual,
            'currency': inv.currency_id.name,
            'payment_state': inv.payment_state,
            'state': inv.state,
            'unit_id': inv.aivio_unit_id.id,
            'unit_name': inv.aivio_unit_id.name,
        }

    # -----------------------------
    # Auth endpoints
    # -----------------------------
    @http.route(['/api/auth/login', '/api/v1/auth/login'], type='http', auth='none', methods=['POST'], csrf=False)
    def login(self, **kw):
        payload = self._payload()
        login = payload.get('login') or payload.get('email') or payload.get('username')
        password = payload.get('password')
        if not login or not password:
            return self._error('login and password are required', 'missing_credentials')
        db = payload.get('db') or request.httprequest.headers.get('X-Odoo-Db') or request.httprequest.args.get('db') or request.db
        if not db:
            return self._error('Database is required. Send db in the login body or configure dbfilter for this host.', 'missing_database', 400, 'db')

        # Match Odoo /web/session/authenticate behavior as much as possible.
        # Depending on the Odoo 19 build, authenticate may return an int, a dict
        # with uid, or only update request.session.uid.
        uid = False

        def _extract_uid(result):
            if isinstance(result, int):
                return result
            if isinstance(result, dict):
                return result.get('uid') or result.get('user_id') or request.session.uid
            return request.session.uid

        credential = {'login': login, 'password': password, 'type': 'password'}
        auth_errors = []
        try:
            result = request.session.authenticate(db, credential)
            uid = _extract_uid(result)
        except TypeError as exc:
            auth_errors.append(str(exc))
            try:
                result = request.session.authenticate(db, login, password)
                uid = _extract_uid(result)
            except Exception as old_exc:
                auth_errors.append(str(old_exc))
                uid = False
        except Exception as exc:
            auth_errors.append(str(exc))
            uid = False

        if not uid:
            # Last safe fallback: call the same low-level user login check used by
            # Odoo session authentication in many versions. This keeps portal
            # users working when a custom route is called without an existing web
            # session.
            try:
                Users = request.env['res.users'].sudo()
                if hasattr(Users, '_login'):
                    try:
                        uid = Users._login(db, login, password, request.httprequest.environ)
                    except TypeError:
                        uid = Users._login(db, login, password)
            except Exception as exc:
                auth_errors.append(str(exc))
                uid = False

        if not uid:
            self._audit(None, request.httprequest.path, 'denied', '; '.join(auth_errors), {'login': login, 'db': db})
            return self._error('Invalid login or password', 'invalid_credentials', 401)
        user = request.env['res.users'].sudo().browse(uid)
        if not user.exists() or not user.aivio_app_role:
            return self._error('User has no AIVIO mobile role', 'missing_role', 403)
        token = request.env['aivio.api.token'].sudo().create_for_user(
            user,
            ttl_days=int(payload.get('ttl_days') or 30),
            ip_address=request.httprequest.remote_addr,
            user_agent=request.httprequest.headers.get('User-Agent'),
            device_token=payload.get('device_token'),
        )
        data = {
            'token': token.token,
            'refresh_token': token.refresh_token,
            'expires_at': self._dt(token.expires_at),
            'user': {
                'id': user.id,
                'name': user.name,
                'login': user.login,
                'role': user.aivio_app_role,
                'groups': [user.aivio_app_role],
                'allowed_apps': user.aivio_get_allowed_apps(),
            },
        }
        self._audit(user, request.httprequest.path, 'success', 'Login', payload)
        return self._ok(data, 'Login successful')

    @http.route(['/api/auth/logout', '/api/v1/auth/logout'], type='http', auth='none', methods=['POST'], csrf=False)
    def logout(self, **kw):
        def do(user, payload):
            self._token_record().revoke()
            return self._ok({}, 'Logged out')
        return self._call(do)

    @http.route(['/api/v1/auth/refresh'], type='http', auth='none', methods=['POST'], csrf=False)
    def refresh(self, **kw):
        payload = self._payload()
        refresh_token = payload.get('refresh_token')
        rec = request.env['aivio.api.token'].sudo().search([('refresh_token', '=', refresh_token), ('active', '=', True)], limit=1)
        if not rec or not rec.is_valid():
            return self._error('Invalid refresh token', 'invalid_refresh_token', 401)
        rec.revoke()
        new = request.env['aivio.api.token'].sudo().create_for_user(rec.user_id, ttl_days=30, ip_address=request.httprequest.remote_addr, user_agent=request.httprequest.headers.get('User-Agent'))
        return self._ok({'token': new.token, 'refresh_token': new.refresh_token, 'expires_at': self._dt(new.expires_at)}, 'Token refreshed')

    @http.route(['/api/auth/access_groups', '/api/v1/auth/access-groups'], type='http', auth='none', methods=['GET'], csrf=False)
    def access_groups(self, **kw):
        def do(user, payload):
            role = user.aivio_app_role
            endpoints = {
                'resident': ['/api/user/profile', '/api/user/ads_banner', '/api/user/amount_due', '/api/user/Invoices', '/api/user/payments', '/api/user/get_visitor', '/api/user/add_new_visitor', '/api/user/tickets', '/api/user/new_ticket'],
                'security': ['/api/user/profile', '/api/user/get_visitor', '/api/user/confirm_visit', '/api/user/add_new_visitor', '/api/user/advanced_search'],
                'maintenance': ['/api/user/profile', '/api/user/tickets', '/api/user/Tickets_status', '/api/user/change_tickets,status', '/api/user/send_work_sheet'],
                'maintenance_supervisor': ['/api/user/profile', '/api/user/tickets', '/api/user/assigin_tickets', '/api/user/memeber_info', '/api/user/summery'],
                'manager': ['*'],
            }
            return self._ok({
                'role': role,
                'groups': {
                    'resident': role == 'resident',
                    'security': role == 'security',
                    'maintenance': role == 'maintenance',
                    'maintenance_supervisor': role == 'maintenance_supervisor',
                    'manager': role == 'manager',
                },
                'allowed_apps': user.aivio_get_allowed_apps(),
                'allowed_endpoints': endpoints.get(role, []),
            })
        return self._call(do)

    # -----------------------------
    # Common user/profile/notifications
    # -----------------------------
    @http.route(['/api/user/profile', '/api/v1/user/profile', '/api/v1/resident/profile'], type='http', auth='none', methods=['GET'], csrf=False)
    def profile(self, **kw):
        def do(user, payload):
            profiles = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id)])
            return self._ok({
                'id': user.id,
                'name': user.name,
                'login': user.login,
                'role': user.aivio_app_role,
                'allowed_apps': user.aivio_get_allowed_apps(),
                'units': [self._serialize_unit(u) for u in user.aivio_unit_ids],
                'resident_profiles': [self._serialize_profile(p) for p in profiles],
            })
        return self._call(do)

    @http.route(['/api/user/device_token', '/api/v1/auth/register-device', '/api/v1/notifications/register-token'], type='http', auth='none', methods=['POST'], csrf=False)
    def device_token(self, **kw):
        def do(user, payload):
            token = payload.get('device_token') or payload.get('token')
            if not token:
                raise ValidationError(_('device_token is required.'))
            vals = {
                'user_id': user.id,
                'token': token,
                'platform': payload.get('platform') or 'android',
                'app_name': payload.get('app_name') or (user.aivio_app_role if user.aivio_app_role in ('resident', 'security', 'maintenance') else False),
                'device_name': payload.get('device_name'),
                'last_seen': fields.Datetime.now(),
                'active': True,
            }
            Token = request.env['aivio.mobile.device.token'].sudo()
            rec = Token.search([('token', '=', token)], limit=1)
            if rec:
                rec.write(vals)
            else:
                rec = Token.create(vals)
            return self._ok({'id': rec.id}, 'Device token saved')
        return self._call(do)

    @http.route(['/api/user/notifications', '/api/v1/notifications'], type='http', auth='none', methods=['GET'], csrf=False)
    def notifications(self, **kw):
        def do(user, payload):
            limit = int(payload.get('limit') or 50)
            records = request.env['aivio.notification'].sudo().search([('user_id', '=', user.id)], limit=limit)
            data = [{
                'id': n.id,
                'title': n.title,
                'body': n.body,
                'type': n.notification_type,
                'state': n.state,
                'create_date': self._dt(n.create_date),
                'sent_date': self._dt(n.sent_date),
                'read_date': self._dt(n.read_date),
                'related_model': n.related_model,
                'related_res_id': n.related_res_id,
            } for n in records]
            return self._ok({'notifications': data})
        return self._call(do)

    @http.route(['/api/user/read_notifications', '/api/v1/notifications/<int:notification_id>/read'], type='http', auth='none', methods=['POST'], csrf=False)
    def read_notifications(self, notification_id=None, **kw):
        def do(user, payload):
            ids = payload.get('ids') or ([notification_id] if notification_id else [])
            records = request.env['aivio.notification'].sudo().search([('id', 'in', ids), ('user_id', '=', user.id)])
            records.action_mark_read()
            return self._ok({'read_ids': records.ids})
        return self._call(do)

    # -----------------------------
    # Resident APIs
    # -----------------------------
    @http.route(['/api/v1/resident/home'], type='http', auth='none', methods=['GET'], csrf=False)
    def resident_home(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            profiles = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id)])
            invoices = request.env['account.move'].sudo().search([('aivio_resident_profile_id', 'in', profiles.ids), ('move_type', '=', 'out_invoice')], limit=10)
            tickets = request.env['aivio.maintenance.ticket'].sudo().search([('resident_user_id', '=', user.id)], limit=10)
            visitors = request.env['aivio.visitor.visit'].sudo().search([('resident_user_id', '=', user.id)], limit=10)
            return self._ok({
                'profiles': [self._serialize_profile(p) for p in profiles],
                'units': [self._serialize_unit(u) for u in user.aivio_unit_ids],
                'amount_due': sum(invoices.mapped('amount_residual')),
                'recent_invoices': [self._serialize_invoice(i) for i in invoices],
                'recent_tickets': [self._serialize_ticket(t) for t in tickets],
                'recent_visitors': [self._serialize_visitor(v) for v in visitors],
            })
        return self._call(do)

    @http.route(['/api/v1/resident/unit'], type='http', auth='none', methods=['GET'], csrf=False)
    def resident_units(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            return self._ok({'units': [self._serialize_unit(u) for u in user.aivio_unit_ids]})
        return self._call(do)

    @http.route(['/api/v1/resident/family'], type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def resident_family(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            Profile = request.env['aivio.resident.profile'].sudo()
            profile = Profile.search([('user_id', '=', user.id)], limit=1)
            if not profile:
                raise ValidationError(_('No resident profile found.'))
            if request.httprequest.method == 'POST':
                request.env['aivio.family.member'].sudo().create({
                    'resident_id': profile.id,
                    'name': payload.get('name'),
                    'relation': payload.get('relation') or 'other',
                    'phone': payload.get('phone'),
                    'identification_no': payload.get('identification_no'),
                    'birth_date': payload.get('birth_date') or False,
                    'notes': payload.get('notes'),
                })
            members = request.env['aivio.family.member'].sudo().search([('resident_id', '=', profile.id)])
            return self._ok({'family': [{'id': m.id, 'name': m.name, 'relation': m.relation, 'phone': m.phone, 'identification_no': m.identification_no} for m in members]})
        return self._call(do)

    @http.route(['/api/v1/resident/vehicles'], type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def resident_vehicles(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            profile = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id)], limit=1)
            if not profile:
                raise ValidationError(_('No resident profile found.'))
            if request.httprequest.method == 'POST':
                request.env['aivio.resident.vehicle'].sudo().create({
                    'resident_id': profile.id,
                    'unit_id': int(payload.get('unit_id')) if payload.get('unit_id') else (profile.primary_unit_id.id or False),
                    'plate_number': payload.get('plate_number'),
                    'vehicle_type': payload.get('vehicle_type') or 'car',
                    'brand': payload.get('brand'),
                    'model': payload.get('model'),
                    'color': payload.get('color'),
                })
            vehicles = request.env['aivio.resident.vehicle'].sudo().search([('resident_id', '=', profile.id)])
            return self._ok({'vehicles': [{'id': v.id, 'plate_number': v.plate_number, 'brand': v.brand, 'model': v.model, 'color': v.color, 'authorized': v.authorized} for v in vehicles]})
        return self._call(do)

    @http.route(['/api/user/ads_banner', '/api/v1/resident/ads-banner'], type='http', auth='none', methods=['GET'], csrf=False)
    def ads_banner(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            today = fields.Date.context_today(request.env.user)
            units = user.aivio_unit_ids
            buildings = units.mapped('project_id')
            domain = [('active', '=', True), '|', ('date_from', '=', False), ('date_from', '<=', today), '|', ('date_to', '=', False), ('date_to', '>=', today)]
            banners = request.env['aivio.ads.banner'].sudo().search(domain)
            data = []
            for b in banners:
                allowed = b.target_type == 'all' or (b.target_type == 'building' and b.project_id in buildings) or (b.target_type == 'unit' and bool(b.unit_ids & units))
                if allowed:
                    data.append({'id': b.id, 'title': b.title, 'subtitle': b.subtitle, 'image_url': self._image_url('aivio.ads.banner', b.id), 'link_url': b.link_url})
            return self._ok({'banners': data})
        return self._call(do)

    @http.route(['/api/user/amount_due', '/api/v1/resident/amount-due'], type='http', auth='none', methods=['GET'], csrf=False)
    def amount_due(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            profiles = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id)])
            invoices = request.env['account.move'].sudo().search([('aivio_resident_profile_id', 'in', profiles.ids), ('move_type', '=', 'out_invoice'), ('state', '=', 'posted')])
            return self._ok({'amount_due': sum(invoices.mapped('amount_residual')), 'currency': request.env.company.currency_id.name})
        return self._call(do)

    @http.route(['/api/user/Invoices', '/api/user/invoices', '/api/v1/invoices'], type='http', auth='none', methods=['GET'], csrf=False)
    def invoices(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            profiles = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id)])
            invoices = request.env['account.move'].sudo().search([('aivio_resident_profile_id', 'in', profiles.ids), ('move_type', '=', 'out_invoice')], limit=int(payload.get('limit') or 100))
            return self._ok({'invoices': [self._serialize_invoice(i) for i in invoices]})
        return self._call(do)

    @http.route(['/api/v1/invoices/<int:invoice_id>'], type='http', auth='none', methods=['GET'], csrf=False)
    def invoice_detail(self, invoice_id, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            inv = request.env['account.move'].sudo().browse(invoice_id)
            if not inv.exists() or inv.aivio_resident_profile_id.user_id.id != user.id:
                raise AccessDenied(_('Invoice not found.'))
            data = self._serialize_invoice(inv)
            data['lines'] = [{'id': l.id, 'name': l.name, 'quantity': l.quantity, 'price_unit': l.price_unit, 'price_subtotal': l.price_subtotal} for l in inv.invoice_line_ids]
            return self._ok(data)
        return self._call(do)

    @http.route(['/api/user/payments', '/api/v1/payments', '/api/v1/payment-proof'], type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def payments(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            if request.httprequest.method == 'POST':
                invoice_id = int(payload.get('invoice_id') or 0)
                inv = request.env['account.move'].sudo().browse(invoice_id)
                if not inv.exists() or inv.aivio_resident_profile_id.user_id.id != user.id:
                    raise AccessDenied(_('Invoice not found.'))
                proof = request.env['aivio.payment.proof'].sudo().create({
                    'invoice_id': inv.id,
                    'amount': payload.get('amount') or inv.amount_residual,
                    'payment_date': payload.get('payment_date') or fields.Date.context_today(request.env.user),
                    'attachment': payload.get('attachment'),
                    'attachment_filename': payload.get('attachment_filename') or 'payment_proof.jpg',
                    'note': payload.get('note'),
                })
                return self._ok({'payment_proof_id': proof.id, 'state': proof.state}, 'Payment proof uploaded')
            profiles = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id)])
            proofs = request.env['aivio.payment.proof'].sudo().search([('resident_id', 'in', profiles.ids)], limit=int(payload.get('limit') or 100))
            return self._ok({'payments': [{'id': p.id, 'name': p.name, 'invoice_id': p.invoice_id.id, 'amount': p.amount, 'currency': p.currency_id.name, 'payment_date': self._date(p.payment_date), 'state': p.state} for p in proofs]})
        return self._call(do)

    # -----------------------------
    # Visitors / security
    # -----------------------------
    def _visitor_domain_for_role(self, user):
        if user.aivio_app_role == 'resident':
            return [('resident_user_id', '=', user.id)]
        if user.aivio_app_role == 'security':
            return ['|', ('building_id', 'in', user.aivio_gate_ids.mapped('building_id').ids), ('gate_id', 'in', user.aivio_gate_ids.ids)]
        if user.aivio_app_role == 'manager':
            return []
        return [('id', '=', 0)]

    @http.route(['/api/user/get_visitor', '/api/v1/security/expected-visitors'], type='http', auth='none', methods=['GET'], csrf=False)
    def get_visitor(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'security', 'manager'])
            visits = request.env['aivio.visitor.visit'].sudo().search(self._visitor_domain_for_role(user), limit=int(payload.get('limit') or 100))
            return self._ok({'visitors': [self._serialize_visitor(v) for v in visits]})
        return self._call(do)

    @http.route(['/api/user/add_new_visitoer', '/api/user/add_new_visitor', '/api/v1/security/visitor/checkin-manual'], type='http', auth='none', methods=['POST'], csrf=False)
    def add_new_visitor(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'security', 'manager'])
            resident = False
            unit = False
            if user.aivio_app_role == 'resident':
                resident = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id)], limit=1)
                unit = request.env['aivio.real.estate.unit'].sudo().browse(int(payload.get('unit_id'))) if payload.get('unit_id') else resident.primary_unit_id
                if unit and unit not in user.aivio_unit_ids:
                    raise AccessDenied(_('You cannot create a visitor for this unit.'))
            else:
                resident = request.env['aivio.resident.profile'].sudo().browse(int(payload.get('resident_id') or 0))
                unit = request.env['aivio.real.estate.unit'].sudo().browse(int(payload.get('unit_id') or 0))
            if not resident or not resident.exists():
                raise ValidationError(_('resident_id is required or no resident profile exists.'))
            visit = request.env['aivio.visitor.visit'].sudo().create({
                'visitor_name': payload.get('visitor_name') or payload.get('name'),
                'visitor_phone': payload.get('visitor_phone') or payload.get('phone'),
                'visitor_id_number': payload.get('visitor_id_number'),
                'visitor_count': int(payload.get('visitor_count') or 1),
                'visit_type': payload.get('visit_type') or 'one_time',
                'reason': payload.get('reason'),
                'resident_id': resident.id,
                'unit_id': unit.id if unit else False,
                'gate_id': int(payload.get('gate_id')) if payload.get('gate_id') else False,
                'valid_from': payload.get('valid_from') or fields.Datetime.now(),
                'valid_to': payload.get('valid_to') or (fields.Datetime.now() + timedelta(hours=12)),
                'has_car': bool(payload.get('has_car')),
                'car_plate': payload.get('car_plate'),
                'status': 'approved' if user.aivio_app_role in ('resident', 'manager') else 'arrived',
            })
            if user.aivio_app_role == 'security':
                gate = user.aivio_gate_ids[:1]
                visit.action_check_in(gate=gate, guard=user)
            return self._ok({'visitor': self._serialize_visitor(visit)}, 'Visitor created')
        return self._call(do)

    @http.route(['/api/user/confirm_visit', '/api/user/confirm _visit', '/api/v1/security/visitor/scan', '/api/v1/security/visitor/checkin'], type='http', auth='none', methods=['POST'], csrf=False)
    def confirm_visit(self, **kw):
        def do(user, payload):
            self._check_role(user, ['security', 'manager'])
            domain = []
            if payload.get('qr_token'):
                domain = [('qr_token', '=', payload.get('qr_token'))]
            elif payload.get('visit_id'):
                domain = [('id', '=', int(payload.get('visit_id')))]
            else:
                raise ValidationError(_('qr_token or visit_id is required.'))
            visit = request.env['aivio.visitor.visit'].sudo().search(domain, limit=1)
            if not visit:
                raise ValidationError(_('Visit not found.'))
            gate = request.env['aivio.security.gate'].sudo().browse(int(payload.get('gate_id'))) if payload.get('gate_id') else user.aivio_gate_ids[:1]
            visit.action_check_in(gate=gate, guard=user)
            return self._ok({'visitor': self._serialize_visitor(visit)}, 'Visit confirmed')
        return self._call(do)

    @http.route(['/api/v1/security/visitor/checkout'], type='http', auth='none', methods=['POST'], csrf=False)
    def visitor_checkout(self, **kw):
        def do(user, payload):
            self._check_role(user, ['security', 'manager'])
            visit = request.env['aivio.visitor.visit'].sudo().browse(int(payload.get('visit_id') or 0))
            if not visit:
                raise ValidationError(_('Visit not found.'))
            gate = request.env['aivio.security.gate'].sudo().browse(int(payload.get('gate_id'))) if payload.get('gate_id') else user.aivio_gate_ids[:1]
            visit.action_check_out(gate=gate, guard=user)
            return self._ok({'visitor': self._serialize_visitor(visit)}, 'Visit checked out')
        return self._call(do)

    @http.route(['/api/v1/security/incident'], type='http', auth='none', methods=['POST'], csrf=False)
    def security_incident(self, **kw):
        def do(user, payload):
            self._check_role(user, ['security', 'manager'])
            inc = request.env['aivio.security.incident'].sudo().create({
                'gate_id': int(payload.get('gate_id')) if payload.get('gate_id') else (user.aivio_gate_ids[:1].id or False),
                'reported_by_id': user.id,
                'severity': payload.get('severity') or 'medium',
                'description': payload.get('description'),
                'attachment': payload.get('attachment'),
                'attachment_filename': payload.get('attachment_filename'),
            })
            return self._ok({'incident_id': inc.id, 'name': inc.name}, 'Incident created')
        return self._call(do)

    @http.route(['/api/v1/security/shift'], type='http', auth='none', methods=['GET'], csrf=False)
    def security_shift(self, **kw):
        def do(user, payload):
            self._check_role(user, ['security', 'manager'])
            shifts = request.env['aivio.guard.shift'].sudo().search(['|', ('user_id', '=', user.id), ('gate_id', 'in', user.aivio_gate_ids.ids)], limit=20)
            return self._ok({'shifts': [{'id': s.id, 'name': s.name, 'gate_id': s.gate_id.id, 'gate_name': s.gate_id.name, 'start_datetime': self._dt(s.start_datetime), 'end_datetime': self._dt(s.end_datetime), 'state': s.state} for s in shifts]})
        return self._call(do)

    @http.route(['/api/user/advanced_search'], type='http', auth='none', methods=['GET'], csrf=False)
    def advanced_search(self, **kw):
        def do(user, payload):
            q = (payload.get('q') or '').strip()
            if not q:
                raise ValidationError(_('Search text is required.'))
            data = {'residents': [], 'visitors': [], 'vehicles': []}
            if user.aivio_app_role in ('security', 'manager'):
                residents = request.env['aivio.resident.profile'].sudo().search(['|', ('name', 'ilike', q), ('phone', 'ilike', q)], limit=20)
                visitors = request.env['aivio.visitor.visit'].sudo().search(['|', '|', ('visitor_name', 'ilike', q), ('visitor_phone', 'ilike', q), ('car_plate', 'ilike', q)], limit=20)
                vehicles = request.env['aivio.resident.vehicle'].sudo().search(['|', ('plate_number', 'ilike', q), ('resident_id.name', 'ilike', q)], limit=20)
            elif user.aivio_app_role == 'resident':
                residents = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id), '|', ('name', 'ilike', q), ('phone', 'ilike', q)], limit=20)
                visitors = request.env['aivio.visitor.visit'].sudo().search([('resident_user_id', '=', user.id), '|', ('visitor_name', 'ilike', q), ('visitor_phone', 'ilike', q)], limit=20)
                vehicles = request.env['aivio.resident.vehicle'].sudo().search([('resident_id.user_id', '=', user.id), ('plate_number', 'ilike', q)], limit=20)
            elif user.aivio_app_role in ('maintenance', 'maintenance_supervisor'):
                residents = request.env['aivio.resident.profile'].sudo().search(['|', ('name', 'ilike', q), ('phone', 'ilike', q)], limit=10)
                visitors = request.env['aivio.visitor.visit']
                vehicles = request.env['aivio.resident.vehicle']
            else:
                raise AccessDenied(_('You are not allowed to search.'))
            data['residents'] = [self._serialize_profile(r) for r in residents]
            data['visitors'] = [self._serialize_visitor(v) for v in visitors]
            data['vehicles'] = [{'id': v.id, 'plate_number': v.plate_number, 'resident_name': v.resident_id.name, 'unit_id': v.unit_id.id} for v in vehicles]
            return self._ok(data)
        return self._call(do)

    # -----------------------------
    # Maintenance APIs
    # -----------------------------
    def _ticket_domain_for_role(self, user):
        if user.aivio_app_role == 'resident':
            return [('resident_user_id', '=', user.id)]
        if user.aivio_app_role == 'maintenance':
            return ['|', ('assigned_user_id', '=', user.id), ('team_id', 'in', user.aivio_maintenance_team_ids.ids)]
        if user.aivio_app_role == 'maintenance_supervisor':
            return [('team_id', 'in', user.aivio_maintenance_team_ids.ids)]
        if user.aivio_app_role == 'manager':
            return []
        return [('id', '=', 0)]

    @http.route(['/api/user/tickets', '/api/v1/tickets', '/api/v1/technician/tasks'], type='http', auth='none', methods=['GET'], csrf=False)
    def tickets(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'maintenance', 'maintenance_supervisor', 'manager'])
            tickets = request.env['aivio.maintenance.ticket'].sudo().search(self._ticket_domain_for_role(user), limit=int(payload.get('limit') or 100))
            return self._ok({'tickets': [self._serialize_ticket(t) for t in tickets]})
        return self._call(do)

    @http.route(['/api/v1/tickets/<int:ticket_id>'], type='http', auth='none', methods=['GET'], csrf=False)
    def ticket_detail(self, ticket_id, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'maintenance', 'maintenance_supervisor', 'manager'])
            ticket = request.env['aivio.maintenance.ticket'].sudo().search([('id', '=', ticket_id)] + self._ticket_domain_for_role(user), limit=1)
            if not ticket:
                raise AccessDenied(_('Ticket not found.'))
            data = self._serialize_ticket(ticket)
            data['worksheets'] = [{'id': w.id, 'technician_id': w.technician_id.id, 'work_note': w.work_note, 'state': w.state, 'work_date': self._dt(w.work_date)} for w in ticket.worksheet_ids]
            data['ratings'] = [{'id': r.id, 'rating': r.rating, 'feedback': r.feedback} for r in ticket.rating_ids]
            return self._ok(data)
        return self._call(do)

    @http.route(['/api/user/new_ticket', '/api/v1/tickets'], type='http', auth='none', methods=['POST'], csrf=False)
    def new_ticket(self, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'maintenance', 'maintenance_supervisor', 'security', 'manager'])
            resident = False
            if user.aivio_app_role == 'resident':
                resident = request.env['aivio.resident.profile'].sudo().search([('user_id', '=', user.id)], limit=1)
                unit_id = int(payload.get('unit_id')) if payload.get('unit_id') else resident.primary_unit_id.id
                if unit_id not in user.aivio_unit_ids.ids:
                    raise AccessDenied(_('You cannot create a ticket for this unit.'))
            else:
                resident = request.env['aivio.resident.profile'].sudo().browse(int(payload.get('resident_id') or 0))
                unit_id = int(payload.get('unit_id') or 0)
            ticket = request.env['aivio.maintenance.ticket'].sudo().create({
                'subject': payload.get('subject') or payload.get('name'),
                'description': payload.get('description'),
                'resident_id': resident.id if resident else False,
                'unit_id': unit_id,
                'category_id': int(payload.get('category_id')) if payload.get('category_id') else False,
                'priority': str(payload.get('priority') or '1'),
                'team_id': int(payload.get('team_id')) if payload.get('team_id') else False,
                'assigned_user_id': int(payload.get('assigned_user_id')) if payload.get('assigned_user_id') else False,
            })
            if payload.get('image'):
                request.env['aivio.maintenance.ticket.image'].sudo().create({'ticket_id': ticket.id, 'image': payload.get('image'), 'filename': payload.get('image_filename') or 'ticket.jpg', 'image_type': 'before'})
            return self._ok({'ticket': self._serialize_ticket(ticket)}, 'Ticket created')
        return self._call(do)

    @http.route(['/api/user/helpdesk_team'], type='http', auth='none', methods=['GET'], csrf=False)
    def helpdesk_team(self, **kw):
        def do(user, payload):
            teams = request.env['aivio.maintenance.team'].sudo().search([('active', '=', True)])
            return self._ok({'teams': [{'id': t.id, 'name': t.name, 'members': [{'id': u.id, 'name': u.name} for u in t.member_user_ids]} for t in teams]})
        return self._call(do)

    @http.route(['/api/user/Tickets_status', '/api/user/tickets_status'], type='http', auth='none', methods=['GET'], csrf=False)
    def tickets_status(self, **kw):
        def do(user, payload):
            stages = request.env['aivio.maintenance.stage'].sudo().search([])
            return self._ok({'statuses': [{'id': s.id, 'name': s.name, 'sequence': s.sequence, 'is_done': s.is_done, 'is_cancelled': s.is_cancelled} for s in stages]})
        return self._call(do)

    @http.route(['/api/user/assigin_tickets', '/api/user/assign_tickets'], type='http', auth='none', methods=['POST'], csrf=False)
    def assign_tickets(self, **kw):
        def do(user, payload):
            self._check_role(user, ['maintenance_supervisor', 'manager'])
            ticket = request.env['aivio.maintenance.ticket'].sudo().browse(int(payload.get('ticket_id') or 0))
            if not ticket:
                raise ValidationError(_('Ticket not found.'))
            if user.aivio_app_role == 'maintenance_supervisor' and ticket.team_id not in user.aivio_maintenance_team_ids:
                raise AccessDenied(_('You can only assign tickets inside your teams.'))
            ticket.write({
                'team_id': int(payload.get('team_id')) if payload.get('team_id') else ticket.team_id.id,
                'assigned_user_id': int(payload.get('assigned_user_id') or payload.get('technician_id') or 0),
                'state': 'assigned',
            })
            return self._ok({'ticket': self._serialize_ticket(ticket)}, 'Ticket assigned')
        return self._call(do)

    @http.route(['/api/user/memeber_info', '/api/user/member_info'], type='http', auth='none', methods=['GET'], csrf=False)
    def member_info(self, **kw):
        def do(user, payload):
            self._check_role(user, ['maintenance', 'maintenance_supervisor', 'manager'])
            teams = user.aivio_maintenance_team_ids if user.aivio_maintenance_team_ids else request.env['aivio.maintenance.team'].sudo().search([])
            return self._ok({'members': [{'team_id': t.id, 'team_name': t.name, 'users': [{'id': u.id, 'name': u.name, 'role': u.aivio_app_role} for u in (t.member_user_ids | t.supervisor_user_ids)]} for t in teams]})
        return self._call(do)

    @http.route(['/api/user/summery', '/api/user/summary'], type='http', auth='none', methods=['GET'], csrf=False)
    def summary(self, **kw):
        def do(user, payload):
            self._check_role(user, ['maintenance_supervisor', 'manager'])
            domain = self._ticket_domain_for_role(user)
            Ticket = request.env['aivio.maintenance.ticket'].sudo()
            states = ['new', 'assigned', 'in_progress', 'waiting', 'done', 'closed', 'cancelled']
            return self._ok({'tickets': {st: Ticket.search_count(domain + [('state', '=', st)]) for st in states}, 'total': Ticket.search_count(domain)})
        return self._call(do)

    @http.route(['/api/user/change_tickets,status', '/api/user/change_ticket_status', '/api/v1/technician/tasks/<int:ticket_id>/accept', '/api/v1/technician/tasks/<int:ticket_id>/start', '/api/v1/technician/tasks/<int:ticket_id>/complete'], type='http', auth='none', methods=['POST'], csrf=False)
    def change_ticket_status(self, ticket_id=None, **kw):
        def do(user, payload):
            self._check_role(user, ['maintenance', 'maintenance_supervisor', 'manager'])
            tid = ticket_id or int(payload.get('ticket_id') or 0)
            ticket = request.env['aivio.maintenance.ticket'].sudo().browse(tid)
            if not ticket:
                raise ValidationError(_('Ticket not found.'))
            if user.aivio_app_role == 'maintenance' and ticket.assigned_user_id.id not in (False, user.id) and ticket.team_id not in user.aivio_maintenance_team_ids:
                raise AccessDenied(_('You cannot update this ticket.'))
            path = request.httprequest.path
            state = payload.get('state')
            if path.endswith('/accept'):
                state = 'assigned'
                if not ticket.assigned_user_id:
                    ticket.assigned_user_id = user.id
            elif path.endswith('/start'):
                state = 'in_progress'
            elif path.endswith('/complete'):
                state = 'done'
            if state == 'done':
                ticket.action_done()
            else:
                ticket.write({'state': state})
            return self._ok({'ticket': self._serialize_ticket(ticket)}, 'Ticket status changed')
        return self._call(do)

    @http.route(['/api/user/send_work_sheet', '/api/v1/tickets/<int:ticket_id>/message'], type='http', auth='none', methods=['POST'], csrf=False)
    def send_work_sheet(self, ticket_id=None, **kw):
        def do(user, payload):
            self._check_role(user, ['maintenance', 'maintenance_supervisor', 'manager'])
            ticket = request.env['aivio.maintenance.ticket'].sudo().browse(ticket_id or int(payload.get('ticket_id') or 0))
            if not ticket:
                raise ValidationError(_('Ticket not found.'))
            worksheet = request.env['aivio.maintenance.worksheet'].sudo().create({
                'ticket_id': ticket.id,
                'technician_id': user.id,
                'work_note': payload.get('work_note') or payload.get('message') or '',
                'materials_note': payload.get('materials_note'),
                'start_datetime': payload.get('start_datetime') or False,
                'end_datetime': payload.get('end_datetime') or False,
                'resident_signature': payload.get('resident_signature'),
                'state': 'submitted',
            })
            return self._ok({'worksheet_id': worksheet.id, 'ticket': self._serialize_ticket(ticket)}, 'Worksheet submitted')
        return self._call(do)

    @http.route(['/api/user/rate_ticket', '/api/v1/tickets/<int:ticket_id>/rate'], type='http', auth='none', methods=['POST'], csrf=False)
    def rate_ticket(self, ticket_id=None, **kw):
        def do(user, payload):
            self._check_role(user, ['resident', 'manager'])
            tid = ticket_id or int(payload.get('ticket_id') or 0)
            ticket = request.env['aivio.maintenance.ticket'].sudo().browse(tid)
            if not ticket or (user.aivio_app_role == 'resident' and ticket.resident_user_id.id != user.id):
                raise AccessDenied(_('Ticket not found.'))
            rating = int(payload.get('rating') or 0)
            if rating < 1 or rating > 5:
                raise ValidationError(_('Rating must be between 1 and 5.'))
            rec = request.env['aivio.ticket.rating'].sudo().create({'ticket_id': ticket.id, 'user_id': user.id, 'rating': rating, 'feedback': payload.get('feedback')})
            return self._ok({'rating_id': rec.id}, 'Ticket rated')
        return self._call(do)

    @http.route(['/api/v1/tickets/<int:ticket_id>/cancel'], type='http', auth='none', methods=['POST'], csrf=False)
    def cancel_ticket(self, ticket_id, **kw):
        def do(user, payload):
            ticket = request.env['aivio.maintenance.ticket'].sudo().browse(ticket_id)
            if user.aivio_app_role == 'resident' and ticket.resident_user_id.id != user.id:
                raise AccessDenied(_('Ticket not found.'))
            ticket.action_cancel()
            return self._ok({'ticket': self._serialize_ticket(ticket)}, 'Ticket cancelled')
        return self._call(do, ['resident', 'maintenance_supervisor', 'manager'])

    @http.route(['/api/v1/technician/tasks/<int:ticket_id>/upload-image'], type='http', auth='none', methods=['POST'], csrf=False)
    def upload_ticket_image(self, ticket_id, **kw):
        def do(user, payload):
            self._check_role(user, ['maintenance', 'maintenance_supervisor', 'manager'])
            ticket = request.env['aivio.maintenance.ticket'].sudo().browse(ticket_id)
            if not ticket:
                raise ValidationError(_('Ticket not found.'))
            img = request.env['aivio.maintenance.ticket.image'].sudo().create({'ticket_id': ticket.id, 'image': payload.get('image'), 'filename': payload.get('filename') or 'image.jpg', 'image_type': payload.get('image_type') or 'other', 'note': payload.get('note')})
            return self._ok({'image_id': img.id}, 'Image uploaded')
        return self._call(do)

    # -----------------------------
    # API docs static endpoints
    # -----------------------------
    @http.route(['/api/aivio/openapi.json', '/api/aivio/swagger.json'], type='http', auth='none', methods=['GET'], csrf=False)
    def openapi_json(self, **kw):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'api', 'openapi.json')
        with open(path, 'r', encoding='utf-8') as f:
            return Response(f.read(), content_type='application/json; charset=utf-8')

    @http.route(['/api/aivio/openapi.yaml'], type='http', auth='none', methods=['GET'], csrf=False)
    def openapi_yaml(self, **kw):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'api', 'openapi.yaml')
        with open(path, 'r', encoding='utf-8') as f:
            return Response(f.read(), content_type='application/yaml; charset=utf-8')

    @http.route(['/api/aivio/postman.json'], type='http', auth='none', methods=['GET'], csrf=False)
    def postman_json(self, **kw):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'api', 'AIVIO_Odoo19_API.postman_collection.json')
        with open(path, 'r', encoding='utf-8') as f:
            return Response(f.read(), content_type='application/json; charset=utf-8')
