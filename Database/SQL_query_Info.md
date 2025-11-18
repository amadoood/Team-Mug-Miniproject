This document describes the full relational structure of the Mug Exchange backend database.
It includes table definitions, relationships, and the fields required for backend API integration.


## Tables Overview

The system uses 5 normalized tables:
- users – stores customer information
- mugs – stores physical mug identity and status
- orders – links users, mugs, and café orders
- events – logs every pickup/return
- devices – identifies hardware endpoints (scanner, return bin)


Schema Details

## Table: `users`

| Column       | Type                              | Notes                     |
|--------------|-----------------------------------|---------------------------|
| `id`         | INT PRIMARY KEY AUTO_INCREMENT    | unique user ID            |
| `name`       | VARCHAR(255)                      |                           |
| `email`      | VARCHAR(255) UNIQUE               | identity + login reference |
| `phone`      | VARCHAR(20) NULL                  | optional                  |
| `created_at` | TIMESTAMP DEFAULT CURRENT_TIMESTAMP |                           |

## Table: `mugs`

| Column            | Type                                                     | Notes                                           |
|-------------------|-----------------------------------------------------------|-------------------------------------------------|
| `id`              | INT PRIMARY KEY AUTO_INCREMENT                            | mug identifier                                  |
| `tag_uid`         | VARCHAR(255) UNIQUE                                       | RFID UID                                        |
| `status`          | ENUM('available','in_use','returned')                     | mug state                                       |
| `lease_expires_at`| DATETIME NULL                                             | return deadline                                 |
| `last_event_id`   | INT NULL                                                  | FK → `events.id`                                |
| `created_at`      | TIMESTAMP DEFAULT CURRENT_TIMESTAMP                       |                                                 |
| `updated_at`      | TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP | auto-updated on changes                |

## Table: `orders`

| Column        | Type                                | Notes                            |
|---------------|---------------------------------------|----------------------------------|
| `id`          | INT PRIMARY KEY AUTO_INCREMENT        | order ID                         |
| `external_ref`| VARCHAR(255)                          | POS / Grubhub / vendor reference |
| `user_id`     | INT                                   | FK → `users.id`                  |
| `location_id` | INT                                   | identifies café location         |
| `mug_id`      | INT                                   | FK → `mugs.id`                   |
| `created_at`  | TIMESTAMP DEFAULT CURRENT_TIMESTAMP   |                                  |


## Table: `events`

| Column         | Type                                             | Notes                                        |
|----------------|--------------------------------------------------|----------------------------------------------|
| `id`           | INT PRIMARY KEY AUTO_INCREMENT                   | event ID                                     |
| `type`         | ENUM('pickup','return','overdue','error')        | type of event                                |
| `mug_id`       | INT                                              | FK → `mugs.id`                               |
| `user_id`      | INT                                              | FK → `users.id`                              |
| `order_id`     | INT                                              | FK → `orders.id`                             |
| `device_id`    | INT                                              | FK → `devices.id`                            |
| `ts`           | TIMESTAMP DEFAULT CURRENT_TIMESTAMP              | event timestamp                              |
| `payload_json` | JSON NULL                                        | optional metadata                            |

payload_json is an optional JSON field for flexible metadata per event. Use it for debug info or additional properties that don’t fit in fixed columns.
NULL is allowed.

## Table: `devices`

| Column        | Type                                | Notes                                    |
|---------------|---------------------------------------|------------------------------------------|
| `id`          | INT PRIMARY KEY AUTO_INCREMENT        | unique device ID                         |
| `location_id` | INT                                   | identifies café or building              |
| `kind`        | ENUM('scanner','return_bin')          | hardware type                            |
| `public_key`  | VARCHAR(255)                          | device authentication key                |
| `last_seen_at`| TIMESTAMP DEFAULT CURRENT_TIMESTAMP   | last device heartbeat                    |





