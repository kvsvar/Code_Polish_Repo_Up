# C++ E-Commerce Test Fixture
- Circular Dependency: order_service.h -> payment_service.h -> notification_service.h -> order_service.h
- God Class: product_service.h (16 methods)
- Deep Inheritance: product.h -> generic_model.h -> auditable_entity.h -> base_entity.h
- Hardcoded Secret: constants.h
- Missing Try/Catch: payment_service.h (curl)
- Dangerous Function: config_loader.h (system())
