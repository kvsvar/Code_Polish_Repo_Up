# Python E-Commerce Test Fixture
- Circular Dependency: order_service -> payment_service -> notification_service -> order_service
- God Class: product_service.py (ProductService has 16 methods)
- Deep Inheritance: product.py (Product -> GenericModel -> AuditableEntity -> BaseEntity)
- Hardcoded Secret: config/constants.py
- Missing Try/Catch: payment_service.py (uses requests)
- Dangerous Function: config_loader.py (eval)
- Exposed Env: .env file present
