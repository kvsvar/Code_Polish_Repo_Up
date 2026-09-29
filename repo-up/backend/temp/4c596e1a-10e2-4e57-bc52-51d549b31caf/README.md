# Java E-Commerce Test Fixture
- Circular Dependency: OrderService -> PaymentService -> NotificationService -> OrderService
- God Class: ProductService (16 methods)
- Deep Inheritance: Product -> GenericModel -> AuditableEntity -> BaseEntity
- Hardcoded Secret: Constants.java
- Missing Try/Catch: PaymentService.java (HttpURLConnection)
- Dangerous Function: ConfigLoader.java (Runtime.getRuntime().exec())
