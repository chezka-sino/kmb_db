CREATE TABLE "customers" (
  "id" integer PRIMARY KEY,
  "first_name" varchar,
  "last_name" varchar,
  "email" varchar,
  "created_at" date,
  "dne" bool
);

CREATE TABLE "passes" (
  "id" integer PRIMARY KEY,
  "pass_name" varchar,
  "punches" int,
  "price" int
);

CREATE TABLE "classes" (
  "id" integer PRIMARY KEY,
  "day" varchar,
  "class_start" datetime,
  "class_name" varchar
);

CREATE TABLE "purchases" (
  "user_id" integer,
  "pass_id" integer,
  "purchase_date" date,
  "method" varchar
);

CREATE TABLE "attendances" (
  "user_id" integer,
  "pass_id" integer,
  "class_id" integer
);

ALTER TABLE "attendances" ADD FOREIGN KEY ("pass_id") REFERENCES "passes" ("id");

ALTER TABLE "attendances" ADD FOREIGN KEY ("class_id") REFERENCES "classes" ("id");

ALTER TABLE "purchases" ADD FOREIGN KEY ("user_id") REFERENCES "customers" ("id");

ALTER TABLE "purchases" ADD FOREIGN KEY ("pass_id") REFERENCES "passes" ("id");

ALTER TABLE "attendances" ADD FOREIGN KEY ("user_id") REFERENCES "customers" ("id");
