"""Initial schema

Revision ID: 0001
Revises:
Create Date: 2026-08-03

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("ebay_user_id", sa.String(255), nullable=True),
        sa.Column("settings", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "ebay_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marketplace", sa.String(20), nullable=False),
        sa.Column("access_token", sa.String(2048), nullable=False),
        sa.Column("refresh_token", sa.String(2048), nullable=False),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scopes", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False, server_default="ALIEXPRESS"),
        sa.Column("store_url", sa.String(1000), nullable=True),
        sa.Column("store_id", sa.String(100), nullable=True),
        sa.Column("contact_info", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("reliability_rating", sa.Numeric(3, 2), nullable=True),
        sa.Column("avg_shipping_days", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "products",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("category_id", sa.String(50), nullable=True),
        sa.Column("condition", sa.String(20), nullable=False, server_default="NEW"),
        sa.Column("condition_description", sa.Text(), nullable=True),
        sa.Column("brand", sa.String(255), nullable=True),
        sa.Column("mpn", sa.String(255), nullable=True),
        sa.Column("upc", sa.String(50), nullable=True),
        sa.Column("ean", sa.String(50), nullable=True),
        sa.Column("isbn", sa.String(50), nullable=True),
        sa.Column("item_specifics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("weight_oz", sa.Numeric(10, 2), nullable=True),
        sa.Column("dimensions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tags", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_products_user_sku", "products", ["user_id", "sku"], unique=True)

    op.create_table(
        "product_images",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("storage_key", sa.String(500), nullable=False),
        sa.Column("url", sa.String(1000), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("original_filename", sa.String(500), nullable=True),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "product_suppliers",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("supplier_product_url", sa.String(1000), nullable=True),
        sa.Column("supplier_product_id", sa.String(255), nullable=True),
        sa.Column("unit_cost", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("shipping_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("min_order_quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_preferred", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("last_price_check_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("price_history", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "inventory",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity_available", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("quantity_reserved", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_point", sa.Integer(), nullable=True),
        sa.Column("reorder_quantity", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("last_checked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("product_id"),
    )

    op.create_table(
        "listing_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category_id", sa.String(50), nullable=True),
        sa.Column("html_template", sa.Text(), nullable=True),
        sa.Column("default_item_specifics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("default_shipping_policy_id", sa.String(100), nullable=True),
        sa.Column("default_return_policy_id", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "listings",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marketplace", sa.String(20), nullable=False, server_default="EBAY_US"),
        sa.Column("ebay_item_id", sa.String(50), nullable=True),
        sa.Column("ebay_offer_id", sa.String(100), nullable=True),
        sa.Column("listing_type", sa.String(20), nullable=False, server_default="FIXED_PRICE"),
        sa.Column("status", sa.String(20), nullable=False, server_default="DRAFT"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("quantity_listed", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quantity_sold", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shipping_policy_id", sa.String(100), nullable=True),
        sa.Column("return_policy_id", sa.String(100), nullable=True),
        sa.Column("payment_policy_id", sa.String(100), nullable=True),
        sa.Column("listing_duration", sa.String(20), nullable=False, server_default="GTC"),
        sa.Column("promoted_listing_rate", sa.Numeric(5, 2), nullable=True),
        sa.Column("ebay_category_id", sa.String(50), nullable=True),
        sa.Column("ebay_store_category_id", sa.String(50), nullable=True),
        sa.Column("listing_template_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("item_specifics_override", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("description_html", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ebay_fees", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_messages", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_template_id"], ["listing_templates.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ebay_item_id"),
    )
    op.create_index("ix_listings_ebay_item_id", "listings", ["ebay_item_id"])
    op.create_index("ix_listings_status", "listings", ["status"])

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marketplace", sa.String(20), nullable=False, server_default="EBAY_US"),
        sa.Column("ebay_order_id", sa.String(100), nullable=False),
        sa.Column("buyer_username", sa.String(255), nullable=True),
        sa.Column("buyer_email", sa.String(255), nullable=True),
        sa.Column("order_status", sa.String(30), nullable=False, server_default="CREATED"),
        sa.Column("payment_status", sa.String(30), nullable=False, server_default="PENDING"),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("subtotal", sa.Numeric(10, 2), nullable=False),
        sa.Column("shipping_cost", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ebay_fees_total", sa.Numeric(10, 2), nullable=True),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("shipping_address", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("shipping_carrier", sa.String(100), nullable=True),
        sa.Column("tracking_number", sa.String(255), nullable=True),
        sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("estimated_delivery", sa.DateTime(timezone=True), nullable=True),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancel_reason", sa.String(255), nullable=True),
        sa.Column("buyer_checkout_notes", sa.Text(), nullable=True),
        sa.Column("aliexpress_order_id", sa.String(100), nullable=True),
        sa.Column("aliexpress_order_status", sa.String(30), nullable=True),
        sa.Column("aliexpress_tracking_number", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("ebay_order_id"),
    )
    op.create_index("ix_orders_ebay_order_id", "orders", ["ebay_order_id"])
    op.create_index("ix_orders_order_status", "orders", ["order_status"])

    op.create_table(
        "order_line_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ebay_line_item_id", sa.String(100), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("sku", sa.String(100), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("total_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("ebay_final_value_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("ebay_payment_processing_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("ebay_promoted_listing_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("ebay_international_fee", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "profitability_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_line_item_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("record_type", sa.String(20), nullable=False),
        sa.Column("sale_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("cost_of_goods", sa.Numeric(10, 2), nullable=False),
        sa.Column("shipping_cost_to_buyer", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("shipping_cost_from_supplier", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ebay_final_value_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ebay_payment_processing_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ebay_promoted_listing_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ebay_international_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("ebay_insertion_fee", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("other_fees", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("tax_collected", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("total_costs", sa.Numeric(10, 2), nullable=False),
        sa.Column("gross_profit", sa.Numeric(10, 2), nullable=False),
        sa.Column("profit_margin_pct", sa.Numeric(8, 4), nullable=False),
        sa.Column("roi_pct", sa.Numeric(8, 4), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="USD"),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_line_item_id"], ["order_line_items.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_profitability_product_type", "profitability_records", ["product_id", "record_type"])

    op.create_table(
        "pricing_rules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("rule_type", sa.String(30), nullable=False),
        sa.Column("min_margin_pct", sa.Numeric(8, 4), nullable=True),
        sa.Column("min_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("max_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("target_margin_pct", sa.Numeric(8, 4), nullable=True),
        sa.Column("reprice_strategy", sa.String(30), nullable=False, server_default="TARGET_MARGIN"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_triggered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "price_change_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("listing_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pricing_rule_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("old_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("new_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("reason", sa.String(30), nullable=False),
        sa.Column("reason_detail", sa.Text(), nullable=True),
        sa.Column("applied_to_ebay", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("ebay_update_error", sa.Text(), nullable=True),
        sa.Column("triggered_by", sa.String(20), nullable=False, server_default="SCHEDULER"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["listing_id"], ["listings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["pricing_rule_id"], ["pricing_rules.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_price_change_log_listing", "price_change_log", ["listing_id", "created_at"])

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ebay_message_id", sa.String(255), nullable=True),
        sa.Column("buyer_username", sa.String(255), nullable=False),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("subject", sa.String(500), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("responded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "returns",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ebay_return_id", sa.String(100), nullable=True),
        sa.Column("reason", sa.String(255), nullable=True),
        sa.Column("buyer_comments", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="REQUESTED"),
        sa.Column("refund_amount", sa.Numeric(10, 2), nullable=True),
        sa.Column("return_shipping_paid_by", sa.String(10), nullable=False, server_default="SELLER"),
        sa.Column("return_tracking_number", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("severity", sa.String(10), nullable=False, server_default="INFO"),
        sa.Column("related_entity_type", sa.String(50), nullable=True),
        sa.Column("related_entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_read", "notifications", ["user_id", "is_read"])

    op.create_table(
        "job_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("job_type", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("items_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_log", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("result_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("triggered_by", sa.String(20), nullable=False, server_default="SCHEDULER"),
        sa.Column("celery_task_id", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_history_type_status", "job_history", ["job_type", "status"])

    op.create_table(
        "fee_schedules",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("marketplace", sa.String(20), nullable=False, server_default="EBAY_US"),
        sa.Column("category_id", sa.String(50), nullable=False),
        sa.Column("category_name", sa.String(255), nullable=True),
        sa.Column("final_value_fee_pct", sa.Numeric(6, 4), nullable=False),
        sa.Column("final_value_fee_cap", sa.Numeric(10, 2), nullable=True),
        sa.Column("payment_processing_pct", sa.Numeric(6, 4), nullable=False, server_default="2.35"),
        sa.Column("payment_processing_fixed", sa.Numeric(10, 2), nullable=False, server_default="0.25"),
        sa.Column("international_fee_pct", sa.Numeric(6, 4), nullable=False, server_default="1.65"),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_fee_schedules_category", "fee_schedules", ["category_id"])

    op.create_table(
        "ebay_category_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("marketplace", sa.String(20), nullable=False, server_default="EBAY_US"),
        sa.Column("category_id", sa.String(50), nullable=False),
        sa.Column("category_name", sa.String(255), nullable=False),
        sa.Column("parent_category_id", sa.String(50), nullable=True),
        sa.Column("level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("leaf_category", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("required_item_specifics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recommended_item_specifics", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("fetched_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ebay_category_cache_category_id", "ebay_category_cache", ["category_id"])


def downgrade() -> None:
    op.drop_table("ebay_category_cache")
    op.drop_table("fee_schedules")
    op.drop_table("job_history")
    op.drop_table("notifications")
    op.drop_table("returns")
    op.drop_table("messages")
    op.drop_table("price_change_log")
    op.drop_table("pricing_rules")
    op.drop_table("profitability_records")
    op.drop_table("order_line_items")
    op.drop_table("orders")
    op.drop_table("listings")
    op.drop_table("listing_templates")
    op.drop_table("inventory")
    op.drop_table("product_suppliers")
    op.drop_table("product_images")
    op.drop_table("products")
    op.drop_table("suppliers")
    op.drop_table("ebay_credentials")
    op.drop_table("users")
