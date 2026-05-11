# AI_CONTEXT.md

Project-specific context. This file changes as the project evolves. Read it on every new task.

## Project identity

- **Name:** TNK SteelTrack
- **One-line description:** Hệ thống quản lý kho thép, đơn hàng và báo cáo cho công ty TNK
- **Status:** pre-MVP
- **Primary users:** Nhân viên kho, quản lý, admin công ty TNK
- **Why it exists:** Thay thế quản lý thủ công bằng excel, tập trung hóa dữ liệu tồn kho và đơn hàng

## Domain model

- **User** — Tài khoản hệ thống, có role: admin / manager / staff / viewer
- **SteelItem** — Mặt hàng thép (loại, quy cách, đơn vị tính, tồn kho)
- **Order** — Đơn hàng bán/mua, liên kết với khách hàng và mặt hàng
- **StockMovement** — Phiếu nhập/xuất kho, cập nhật tồn kho theo từng giao dịch
- **Customer** — Khách hàng / nhà cung cấp
- **Report** — Báo cáo tổng hợp (doanh thu, tồn kho, công nợ)

Key relationships:
- Order has many OrderItem → each OrderItem links to SteelItem
- StockMovement belongs to SteelItem and optionally to Order
- User has one role; role controls access to views

Key invariants:
- Tồn kho không được âm sau khi xuất
- Đơn hàng đã hoàn thành không thể chỉnh sửa
- Mỗi StockMovement phải có quantity > 0

## Glossary

| Term | Meaning |
| ---- | ------- |
| Tồn kho | Số lượng hàng hiện có trong kho |
| Phiếu nhập | Nhập hàng vào kho (StockMovement type=IN) |
| Phiếu xuất | Xuất hàng ra khỏi kho (StockMovement type=OUT) |
| Quy cách | Kích thước/thông số kỹ thuật của thép (ví dụ: Ø12, 6m) |
| Mã hàng | SKU định danh mặt hàng thép |

## Tech stack (exact versions)

| Layer        | Stack                                  |
| ------------ | -------------------------------------- |
| Python       | 3.12                                   |
| Django       | 5.1                                    |
| DRF          | Chỉ dùng khi cần JSON API              |
| PostgreSQL   | 16                                     |
| Redis        | 7                                      |
| Celery       | 5.x                                    |
| Frontend     | HTMX, Tailwind CSS, Alpine.js, vanilla JS |
| Web server   | Gunicorn behind Nginx                  |
| Container    | Docker + Docker Compose                |
| CI/CD        | GitHub Actions                         |
| Hosting      | TBD                                    |
| Monitoring   | Sentry                                 |
| Email        | TBD                                    |
| Storage      | TBD (S3 hoặc MinIO)                    |

## Current goals (this quarter / sprint)

- Dựng cấu trúc project và CI/CD pipeline ✅
- Implement module Kho thép (inventory): CRUD mặt hàng, nhập/xuất kho
- Implement module Đơn hàng (orders): tạo/sửa/duyệt đơn
- Trang login + phân quyền theo role

## Active concerns / known issues

- Chưa có schema thực tế — chờ user confirm domain model trước khi viết migrations
- Hosting chưa quyết định

## Constraints & preferences

- KHÔNG dùng class-based views — function views only
- KHÔNG dùng SPA/React/Vue — HTMX + server-render
- Tất cả thời gian lưu UTC, hiển thị theo Asia/Ho_Chi_Minh
- Dùng `uv` thay vì pip-tools
- Template đặt tại `frontend/templates/`, không đặt trong từng app
- Services layer bắt buộc — không đặt business logic trong views hoặc models

## What to defer to the human

Always pause and ask before:
- Thay đổi schema ở bảng: orders, stock_movements (khi đã có data)
- Thêm third-party payment integration
- Thay đổi logic phân quyền / role
- Thêm dependency mới

## Quick links

- Repo: TBD
- Production: TBD
- Staging: TBD
