-- Idempotent seed data for Oracle using identity columns (no explicit IDs)
-- This avoids breaking identity sequences and maintains referential integrity

-- Vets
MERGE INTO vets v
USING (SELECT 'James' AS first_name, 'Carter' AS last_name FROM dual) src
ON (v.first_name = src.first_name AND v.last_name = src.last_name)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name) VALUES (src.first_name, src.last_name);

MERGE INTO vets v
USING (SELECT 'Helen' AS first_name, 'Leary' AS last_name FROM dual) src
ON (v.first_name = src.first_name AND v.last_name = src.last_name)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name) VALUES (src.first_name, src.last_name);

MERGE INTO vets v
USING (SELECT 'Linda' AS first_name, 'Douglas' AS last_name FROM dual) src
ON (v.first_name = src.first_name AND v.last_name = src.last_name)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name) VALUES (src.first_name, src.last_name);

MERGE INTO vets v
USING (SELECT 'Rafael' AS first_name, 'Ortega' AS last_name FROM dual) src
ON (v.first_name = src.first_name AND v.last_name = src.last_name)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name) VALUES (src.first_name, src.last_name);

MERGE INTO vets v
USING (SELECT 'Henry' AS first_name, 'Stevens' AS last_name FROM dual) src
ON (v.first_name = src.first_name AND v.last_name = src.last_name)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name) VALUES (src.first_name, src.last_name);

MERGE INTO vets v
USING (SELECT 'Sharon' AS first_name, 'Jenkins' AS last_name FROM dual) src
ON (v.first_name = src.first_name AND v.last_name = src.last_name)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name) VALUES (src.first_name, src.last_name);

-- Specialties
MERGE INTO specialties s
USING (SELECT 'radiology' AS name FROM dual) src
ON (s.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

MERGE INTO specialties s
USING (SELECT 'surgery' AS name FROM dual) src
ON (s.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

MERGE INTO specialties s
USING (SELECT 'dentistry' AS name FROM dual) src
ON (s.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

-- Types
MERGE INTO types t
USING (SELECT 'cat' AS name FROM dual) src
ON (t.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

MERGE INTO types t
USING (SELECT 'dog' AS name FROM dual) src
ON (t.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

MERGE INTO types t
USING (SELECT 'lizard' AS name FROM dual) src
ON (t.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

MERGE INTO types t
USING (SELECT 'snake' AS name FROM dual) src
ON (t.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

MERGE INTO types t
USING (SELECT 'bird' AS name FROM dual) src
ON (t.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

MERGE INTO types t
USING (SELECT 'hamster' AS name FROM dual) src
ON (t.name = src.name)
WHEN NOT MATCHED THEN
  INSERT (name) VALUES (src.name);

-- Owners (matched by telephone to ensure idempotency)
MERGE INTO owners o
USING (SELECT 'George' AS first_name, 'Franklin' AS last_name, '110 W. Liberty St.' AS address, 'Madison' AS city, '6085551023' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'Betty' AS first_name, 'Davis' AS last_name, '638 Cardinal Ave.' AS address, 'Sun Prairie' AS city, '6085551749' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'Eduardo' AS first_name, 'Rodriquez' AS last_name, '2693 Commerce St.' AS address, 'McFarland' AS city, '6085558763' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'Harold' AS first_name, 'Davis' AS last_name, '563 Friendly St.' AS address, 'Windsor' AS city, '6085553198' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'Peter' AS first_name, 'McTavish' AS last_name, '2387 S. Fair Way' AS address, 'Madison' AS city, '6085552765' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'Jean' AS first_name, 'Coleman' AS last_name, '105 N. Lake St.' AS address, 'Monona' AS city, '6085552654' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'Jeff' AS first_name, 'Black' AS last_name, '1450 Oak Blvd.' AS address, 'Monona' AS city, '6085555387' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'Maria' AS first_name, 'Escobito' AS last_name, '345 Maple St.' AS address, 'Madison' AS city, '6085557683' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'David' AS first_name, 'Schroeder' AS last_name, '2749 Blackhawk Trail' AS address, 'Madison' AS city, '6085559435' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

MERGE INTO owners o
USING (SELECT 'Carlos' AS first_name, 'Estaban' AS last_name, '2335 Independence La.' AS address, 'Waunakee' AS city, '6085555487' AS telephone FROM dual) src
ON (o.telephone = src.telephone)
WHEN NOT MATCHED THEN
  INSERT (first_name, last_name, address, city, telephone)
  VALUES (src.first_name, src.last_name, src.address, src.city, src.telephone);

-- Pets (lookup type by name and owner by telephone; match by (name, owner_id))
MERGE INTO pets p
USING (
  SELECT 'Lav' AS name,
         DATE '2000-09-07' AS birth_date,
         (SELECT id FROM types WHERE name = 'cat') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085551023') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Basil' AS name,
         DATE '2002-08-06' AS birth_date,
         (SELECT id FROM types WHERE name = 'hamster') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085551749') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Rosy' AS name,
         DATE '2001-04-17' AS birth_date,
         (SELECT id FROM types WHERE name = 'dog') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085558763') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Jewel' AS name,
         DATE '2000-03-07' AS birth_date,
         (SELECT id FROM types WHERE name = 'dog') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085558763') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Iggy' AS name,
         DATE '2000-11-30' AS birth_date,
         (SELECT id FROM types WHERE name = 'lizard') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085553198') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'George' AS name,
         DATE '2000-01-20' AS birth_date,
         (SELECT id FROM types WHERE name = 'snake') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085552765') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Samantha' AS name,
         DATE '1995-09-04' AS birth_date,
         (SELECT id FROM types WHERE name = 'cat') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085552654') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Max' AS name,
         DATE '1995-09-04' AS birth_date,
         (SELECT id FROM types WHERE name = 'cat') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085552654') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Lucky' AS name,
         DATE '1999-08-06' AS birth_date,
         (SELECT id FROM types WHERE name = 'bird') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085555387') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Mulligan' AS name,
         DATE '1997-02-24' AS birth_date,
         (SELECT id FROM types WHERE name = 'dog') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085557683') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Freddy' AS name,
         DATE '2000-03-09' AS birth_date,
         (SELECT id FROM types WHERE name = 'bird') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085559435') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Lucky' AS name,
         DATE '2000-06-24' AS birth_date,
         (SELECT id FROM types WHERE name = 'dog') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085555487') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

MERGE INTO pets p
USING (
  SELECT 'Sly' AS name,
         DATE '2002-06-08' AS birth_date,
         (SELECT id FROM types WHERE name = 'cat') AS type_id,
         (SELECT id FROM owners WHERE telephone = '6085555487') AS owner_id
  FROM dual
) src
ON (p.name = src.name AND p.owner_id = src.owner_id)
WHEN NOT MATCHED THEN
  INSERT (name, birth_date, type_id, owner_id)
  VALUES (src.name, src.birth_date, src.type_id, src.owner_id);

-- Vet specialties (look up vet by name and specialty by name)
MERGE INTO vet_specialties vs
USING (
  SELECT (SELECT id FROM vets WHERE first_name = 'Helen' AND last_name = 'Leary') AS vet_id,
         (SELECT id FROM specialties WHERE name = 'radiology') AS specialty_id
  FROM dual
) src
ON (vs.vet_id = src.vet_id AND vs.specialty_id = src.specialty_id)
WHEN NOT MATCHED THEN
  INSERT (vet_id, specialty_id) VALUES (src.vet_id, src.specialty_id);

MERGE INTO vet_specialties vs
USING (
  SELECT (SELECT id FROM vets WHERE first_name = 'Linda' AND last_name = 'Douglas') AS vet_id,
         (SELECT id FROM specialties WHERE name = 'surgery') AS specialty_id
  FROM dual
) src
ON (vs.vet_id = src.vet_id AND vs.specialty_id = src.specialty_id)
WHEN NOT MATCHED THEN
  INSERT (vet_id, specialty_id) VALUES (src.vet_id, src.specialty_id);

MERGE INTO vet_specialties vs
USING (
  SELECT (SELECT id FROM vets WHERE first_name = 'Linda' AND last_name = 'Douglas') AS vet_id,
         (SELECT id FROM specialties WHERE name = 'dentistry') AS specialty_id
  FROM dual
) src
ON (vs.vet_id = src.vet_id AND vs.specialty_id = src.specialty_id)
WHEN NOT MATCHED THEN
  INSERT (vet_id, specialty_id) VALUES (src.vet_id, src.specialty_id);

MERGE INTO vet_specialties vs
USING (
  SELECT (SELECT id FROM vets WHERE first_name = 'Rafael' AND last_name = 'Ortega') AS vet_id,
         (SELECT id FROM specialties WHERE name = 'surgery') AS specialty_id
  FROM dual
) src
ON (vs.vet_id = src.vet_id AND vs.specialty_id = src.specialty_id)
WHEN NOT MATCHED THEN
  INSERT (vet_id, specialty_id) VALUES (src.vet_id, src.specialty_id);

MERGE INTO vet_specialties vs
USING (
  SELECT (SELECT id FROM vets WHERE first_name = 'Henry' AND last_name = 'Stevens') AS vet_id,
         (SELECT id FROM specialties WHERE name = 'radiology') AS specialty_id
  FROM dual
) src
ON (vs.vet_id = src.vet_id AND vs.specialty_id = src.specialty_id)
WHEN NOT MATCHED THEN
  INSERT (vet_id, specialty_id) VALUES (src.vet_id, src.specialty_id);

-- Visits (lookup pet by (name, owner telephone); match by (pet_id, visit_date, description))
MERGE INTO visits v
USING (
  SELECT (SELECT p.id FROM pets p JOIN owners o ON p.owner_id = o.id WHERE p.name = 'Samantha' AND o.telephone = '6085552654') AS pet_id,
         DATE '2010-03-04' AS visit_date,
         'rabies shot' AS description
  FROM dual
) src
ON (v.pet_id = src.pet_id AND v.visit_date = src.visit_date AND v.description = src.description)
WHEN NOT MATCHED THEN
  INSERT (pet_id, visit_date, description) VALUES (src.pet_id, src.visit_date, src.description);

MERGE INTO visits v
USING (
  SELECT (SELECT p.id FROM pets p JOIN owners o ON p.owner_id = o.id WHERE p.name = 'Max' AND o.telephone = '6085552654') AS pet_id,
         DATE '2011-03-04' AS visit_date,
         'rabies shot' AS description
  FROM dual
) src
ON (v.pet_id = src.pet_id AND v.visit_date = src.visit_date AND v.description = src.description)
WHEN NOT MATCHED THEN
  INSERT (pet_id, visit_date, description) VALUES (src.pet_id, src.visit_date, src.description);

MERGE INTO visits v
USING (
  SELECT (SELECT p.id FROM pets p JOIN owners o ON p.owner_id = o.id WHERE p.name = 'Max' AND o.telephone = '6085552654') AS pet_id,
         DATE '2009-06-04' AS visit_date,
         'neutered' AS description
  FROM dual
) src
ON (v.pet_id = src.pet_id AND v.visit_date = src.visit_date AND v.description = src.description)
WHEN NOT MATCHED THEN
  INSERT (pet_id, visit_date, description) VALUES (src.pet_id, src.visit_date, src.description);

MERGE INTO visits v
USING (
  SELECT (SELECT p.id FROM pets p JOIN owners o ON p.owner_id = o.id WHERE p.name = 'Samantha' AND o.telephone = '6085552654') AS pet_id,
         DATE '2008-09-04' AS visit_date,
         'spayed' AS description
  FROM dual
) src
ON (v.pet_id = src.pet_id AND v.visit_date = src.visit_date AND v.description = src.description)
WHEN NOT MATCHED THEN
  INSERT (pet_id, visit_date, description) VALUES (src.pet_id, src.visit_date, src.description);
