SELECT DISTINCT ON (LOWER ( description ))
  LOWER ( description ),
	component_type,
	FALSE,
	'ru'
FROM
	srbc_mealcomponent mc
WHERE
	NOT EXISTS ( SELECT title FROM srbc_mealproduct mp WHERE LOWER ( mc.description ) = mp.title )
	);

UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%1%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%2%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%3%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%4%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%5%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%6%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%7%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%8%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%9%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%0%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%(%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%)%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%,%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%.%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%+%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%[%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%]%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%/%';
UPDATE srbc_mealproduct SET component_type = NULL, is_verified = TRUE WHERE is_verified = FALSE and title like '%\%';