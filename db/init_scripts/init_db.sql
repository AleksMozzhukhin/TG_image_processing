CREATE TABLE IF NOT EXISTS "image" (
  "id" integer PRIMARY KEY,
  "user_id" integer,
  "request" varchar,
  "image" bytea,
  "date" timestamp
);