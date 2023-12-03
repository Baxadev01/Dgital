INSERT INTO public.crm_payment(
	id, payment_provider, payment_id, status, date_added, amount, currency, payment_type, payment_url, last_updated_at, paid_at, apple_payment_id, discount_code_id, google_payment_id, tariff_id, user_id, wave_id)
	SELECT id, payment_provider, payment_id, status, date_added, amount, currency, payment_type, payment_url, last_updated_at, paid_at, NULL, discount_code_id, NULL, tariff_id, user_id, wave_id
	FROM crm_order WHERE status != 'CANCELED'

-- Set Next ID Value to MAX ID
SELECT setval('crm_payment_id_seq', (SELECT MAX(id) FROM crm_Payment));
	