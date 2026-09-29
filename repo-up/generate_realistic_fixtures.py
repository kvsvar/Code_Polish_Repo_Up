import os
import shutil
import zipfile
import glob

def create_python_fixture(base_dir):
    os.makedirs(f"{base_dir}/models", exist_ok=True)
    os.makedirs(f"{base_dir}/services", exist_ok=True)
    os.makedirs(f"{base_dir}/controllers", exist_ok=True)
    os.makedirs(f"{base_dir}/utils", exist_ok=True)
    os.makedirs(f"{base_dir}/config", exist_ok=True)

    # config
    with open(f"{base_dir}/config/__init__.py", "w") as f: f.write("")
    with open(f"{base_dir}/config/constants.py", "w") as f:
        f.write('API_KEY = "AKIAIOSFODNN7EXAMPLE"\n')
        f.write('VERSION = "1.0.0"\n')

    # utils
    with open(f"{base_dir}/utils/__init__.py", "w") as f: f.write("")
    with open(f"{base_dir}/utils/logger.py", "w") as f:
        f.write('class Logger:\n    def log(self, msg):\n        print(msg)\n')
    with open(f"{base_dir}/utils/db_util.py", "w") as f:
        f.write('from utils.logger import Logger\n')
        f.write('class DbUtil:\n    def connect(self):\n        Logger().log("Connected")\n')
    with open(f"{base_dir}/utils/config_loader.py", "w") as f:
        f.write('class ConfigLoader:\n    def load(self, dynamic_str):\n        # Dangerous function\n        eval(dynamic_str)\n')

    # models (Deep Inheritance)
    with open(f"{base_dir}/models/__init__.py", "w") as f: f.write("")
    with open(f"{base_dir}/models/base.py", "w") as f:
        f.write('class BaseEntity:\n    pass\n')
    with open(f"{base_dir}/models/auditable.py", "w") as f:
        f.write('from models.base import BaseEntity\nclass AuditableEntity(BaseEntity):\n    pass\n')
    with open(f"{base_dir}/models/generic.py", "w") as f:
        f.write('from models.auditable import AuditableEntity\nclass GenericModel(AuditableEntity):\n    pass\n')
    with open(f"{base_dir}/models/product.py", "w") as f:
        f.write('from models.generic import GenericModel\nclass Product(GenericModel):\n    def __init__(self, id, name):\n        self.id = id\n        self.name = name\n')
    with open(f"{base_dir}/models/user.py", "w") as f:
        f.write('from models.base import BaseEntity\nclass User(BaseEntity):\n    pass\n')
    with open(f"{base_dir}/models/order.py", "w") as f:
        f.write('from models.user import User\nfrom models.product import Product\nclass Order:\n    pass\n')
    with open(f"{base_dir}/models/payment.py", "w") as f:
        f.write('from models.order import Order\nclass Payment:\n    pass\n')

    # services
    with open(f"{base_dir}/services/__init__.py", "w") as f: f.write("")
    with open(f"{base_dir}/services/user_service.py", "w") as f:
        f.write('from utils.db_util import DbUtil\nfrom models.user import User\nclass UserService:\n    def get(self):\n        pass\n')
    
    # God Class
    with open(f"{base_dir}/services/product_service.py", "w") as f:
        methods = "\n".join([f"    def action_{i}(self):\n        pass" for i in range(16)])
        f.write(f'from utils.db_util import DbUtil\nfrom models.product import Product\nclass ProductService:\n{methods}\n')

    # Circular Dependency: OrderService -> PaymentService -> NotificationService -> OrderService
    with open(f"{base_dir}/services/order_service.py", "w") as f:
        f.write('from services.payment_service import PaymentService\nfrom utils.logger import Logger\nclass OrderService:\n    def process(self):\n        pass\n')
    
    with open(f"{base_dir}/services/payment_service.py", "w") as f:
        f.write('import requests\nfrom services.notification_service import NotificationService\nfrom config.constants import API_KEY\n')
        f.write('class PaymentService:\n    def pay(self):\n        # No try/catch on I/O\n        requests.post("http://api.payment", data={"key": API_KEY})\n')

    with open(f"{base_dir}/services/notification_service.py", "w") as f:
        f.write('from services.order_service import OrderService\nfrom utils.logger import Logger\nclass NotificationService:\n    def notify(self):\n        pass\n')

    # controllers
    with open(f"{base_dir}/controllers/__init__.py", "w") as f: f.write("")
    with open(f"{base_dir}/controllers/order_controller.py", "w") as f:
        f.write('from services.order_service import OrderService\nclass OrderController:\n    pass\n')

    # env files
    with open(f"{base_dir}/.env", "w") as f:
        f.write("SECRET=12345\n")
    with open(f"{base_dir}/.env.example", "w") as f:
        f.write("SECRET=placeholder\n")
        
    with open(f"{base_dir}/README.md", "w") as f:
        f.write("# Python E-Commerce Test Fixture\n")
        f.write("- Circular Dependency: order_service -> payment_service -> notification_service -> order_service\n")
        f.write("- God Class: product_service.py (ProductService has 16 methods)\n")
        f.write("- Deep Inheritance: product.py (Product -> GenericModel -> AuditableEntity -> BaseEntity)\n")
        f.write("- Hardcoded Secret: config/constants.py\n")
        f.write("- Missing Try/Catch: payment_service.py (uses requests)\n")
        f.write("- Dangerous Function: config_loader.py (eval)\n")
        f.write("- Exposed Env: .env file present\n")

def create_java_fixture(base_dir):
    os.makedirs(f"{base_dir}/src/main/java/com/demo/models", exist_ok=True)
    os.makedirs(f"{base_dir}/src/main/java/com/demo/services", exist_ok=True)
    os.makedirs(f"{base_dir}/src/main/java/com/demo/controllers", exist_ok=True)
    os.makedirs(f"{base_dir}/src/main/java/com/demo/utils", exist_ok=True)
    os.makedirs(f"{base_dir}/src/main/java/com/demo/config", exist_ok=True)

    # config
    with open(f"{base_dir}/src/main/java/com/demo/config/Constants.java", "w") as f:
        f.write('package com.demo.config;\npublic class Constants {\n    public static final String API_KEY = "AKIAIOSFODNN7EXAMPLE";\n}\n')

    # utils
    with open(f"{base_dir}/src/main/java/com/demo/utils/Logger.java", "w") as f:
        f.write('package com.demo.utils;\npublic class Logger {\n    public void log(String msg) { System.out.println(msg); }\n}\n')
    with open(f"{base_dir}/src/main/java/com/demo/utils/DbUtil.java", "w") as f:
        f.write('package com.demo.utils;\npublic class DbUtil {\n    public void connect() { new Logger().log("Connected"); }\n}\n')
    with open(f"{base_dir}/src/main/java/com/demo/utils/ConfigLoader.java", "w") as f:
        f.write('package com.demo.utils;\npublic class ConfigLoader {\n    public void load(String cmd) throws Exception {\n        Runtime.getRuntime().exec(cmd);\n    }\n}\n')

    # models (Deep Inheritance)
    with open(f"{base_dir}/src/main/java/com/demo/models/BaseEntity.java", "w") as f:
        f.write('package com.demo.models;\npublic class BaseEntity {}\n')
    with open(f"{base_dir}/src/main/java/com/demo/models/AuditableEntity.java", "w") as f:
        f.write('package com.demo.models;\npublic class AuditableEntity extends BaseEntity {}\n')
    with open(f"{base_dir}/src/main/java/com/demo/models/GenericModel.java", "w") as f:
        f.write('package com.demo.models;\npublic class GenericModel extends AuditableEntity {}\n')
    with open(f"{base_dir}/src/main/java/com/demo/models/Product.java", "w") as f:
        f.write('package com.demo.models;\npublic class Product extends GenericModel {}\n')
    with open(f"{base_dir}/src/main/java/com/demo/models/User.java", "w") as f:
        f.write('package com.demo.models;\npublic class User extends BaseEntity {}\n')
    with open(f"{base_dir}/src/main/java/com/demo/models/Order.java", "w") as f:
        f.write('package com.demo.models;\npublic class Order {\n  User user;\n  Product product;\n}\n')
    with open(f"{base_dir}/src/main/java/com/demo/models/Payment.java", "w") as f:
        f.write('package com.demo.models;\npublic class Payment {\n  Order order;\n}\n')

    # services
    with open(f"{base_dir}/src/main/java/com/demo/services/UserService.java", "w") as f:
        f.write('package com.demo.services;\nimport com.demo.utils.DbUtil;\nimport com.demo.models.User;\npublic class UserService {}\n')
    
    # God Class
    with open(f"{base_dir}/src/main/java/com/demo/services/ProductService.java", "w") as f:
        methods = "\n".join([f"    public void action_{i}() {{}}" for i in range(16)])
        f.write(f'package com.demo.services;\nimport com.demo.utils.DbUtil;\nimport com.demo.models.Product;\npublic class ProductService {{\n{methods}\n}}\n')

    # Circular Dependency
    with open(f"{base_dir}/src/main/java/com/demo/services/OrderService.java", "w") as f:
        f.write('package com.demo.services;\nimport com.demo.utils.Logger;\npublic class OrderService {\n  PaymentService ps;\n}\n')
    
    with open(f"{base_dir}/src/main/java/com/demo/services/PaymentService.java", "w") as f:
        f.write('package com.demo.services;\nimport java.net.HttpURLConnection;\nimport java.net.URL;\nimport com.demo.config.Constants;\n')
        f.write('public class PaymentService {\n  NotificationService ns;\n  public void pay() throws Exception {\n    HttpURLConnection conn = (HttpURLConnection) new URL("http://api").openConnection();\n  }\n}\n')

    with open(f"{base_dir}/src/main/java/com/demo/services/NotificationService.java", "w") as f:
        f.write('package com.demo.services;\nimport com.demo.utils.Logger;\npublic class NotificationService {\n  OrderService os;\n}\n')

    # controllers
    with open(f"{base_dir}/src/main/java/com/demo/controllers/OrderController.java", "w") as f:
        f.write('package com.demo.controllers;\nimport com.demo.services.OrderService;\npublic class OrderController {}\n')

    # env files
    with open(f"{base_dir}/.env", "w") as f: f.write("SECRET=12345\n")
    with open(f"{base_dir}/.env.example", "w") as f: f.write("SECRET=placeholder\n")
        
    with open(f"{base_dir}/README.md", "w") as f:
        f.write("# Java E-Commerce Test Fixture\n")
        f.write("- Circular Dependency: OrderService -> PaymentService -> NotificationService -> OrderService\n")
        f.write("- God Class: ProductService (16 methods)\n")
        f.write("- Deep Inheritance: Product -> GenericModel -> AuditableEntity -> BaseEntity\n")
        f.write("- Hardcoded Secret: Constants.java\n")
        f.write("- Missing Try/Catch: PaymentService.java (HttpURLConnection)\n")
        f.write("- Dangerous Function: ConfigLoader.java (Runtime.getRuntime().exec())\n")

def create_cpp_fixture(base_dir):
    os.makedirs(f"{base_dir}/include/models", exist_ok=True)
    os.makedirs(f"{base_dir}/src/services", exist_ok=True)
    os.makedirs(f"{base_dir}/include/services", exist_ok=True)
    os.makedirs(f"{base_dir}/src/utils", exist_ok=True)
    os.makedirs(f"{base_dir}/include/utils", exist_ok=True)
    os.makedirs(f"{base_dir}/include/config", exist_ok=True)

    # config
    with open(f"{base_dir}/include/config/constants.h", "w") as f:
        f.write('#ifndef CONSTANTS_H\n#define CONSTANTS_H\n#include <string>\nconst std::string API_KEY = "AKIAIOSFODNN7EXAMPLE";\n#endif\n')

    # utils
    with open(f"{base_dir}/include/utils/logger.h", "w") as f:
        f.write('#ifndef LOGGER_H\n#define LOGGER_H\nclass Logger { public: void log(); };\n#endif\n')
    with open(f"{base_dir}/include/utils/config_loader.h", "w") as f:
        f.write('#ifndef CONFIG_LOADER_H\n#define CONFIG_LOADER_H\n#include <cstdlib>\nclass ConfigLoader { public: void load() { system("cat config"); } };\n#endif\n')

    # models (Deep Inheritance)
    with open(f"{base_dir}/include/models/base_entity.h", "w") as f:
        f.write('#ifndef BASE_H\n#define BASE_H\nclass BaseEntity {};\n#endif\n')
    with open(f"{base_dir}/include/models/auditable_entity.h", "w") as f:
        f.write('#ifndef AUDIT_H\n#define AUDIT_H\n#include "base_entity.h"\nclass AuditableEntity : public BaseEntity {};\n#endif\n')
    with open(f"{base_dir}/include/models/generic_model.h", "w") as f:
        f.write('#ifndef GENERIC_H\n#define GENERIC_H\n#include "auditable_entity.h"\nclass GenericModel : public AuditableEntity {};\n#endif\n')
    with open(f"{base_dir}/include/models/product.h", "w") as f:
        f.write('#ifndef PRODUCT_H\n#define PRODUCT_H\n#include "generic_model.h"\nclass Product : public GenericModel {};\n#endif\n')

    # God Class
    with open(f"{base_dir}/include/services/product_service.h", "w") as f:
        methods = "\n".join([f"    void action_{i}();" for i in range(16)])
        f.write(f'#ifndef PROD_SVC_H\n#define PROD_SVC_H\n#include "../models/product.h"\nclass ProductService {{\npublic:\n{methods}\n}};\n#endif\n')

    # Circular Dependency
    with open(f"{base_dir}/include/services/order_service.h", "w") as f:
        f.write('#ifndef ORDER_SVC_H\n#define ORDER_SVC_H\n#include "payment_service.h"\nclass OrderService {};\n#endif\n')
    with open(f"{base_dir}/include/services/payment_service.h", "w") as f:
        f.write('#ifndef PAY_SVC_H\n#define PAY_SVC_H\n#include "notification_service.h"\n#include <curl/curl.h>\nclass PaymentService { public: void pay() { curl_easy_init(); } };\n#endif\n')
    with open(f"{base_dir}/include/services/notification_service.h", "w") as f:
        f.write('#ifndef NOTIF_SVC_H\n#define NOTIF_SVC_H\n#include "order_service.h"\nclass NotificationService {};\n#endif\n')

    # env files
    with open(f"{base_dir}/.env", "w") as f: f.write("SECRET=12345\n")
    with open(f"{base_dir}/.env.example", "w") as f: f.write("SECRET=placeholder\n")
        
    with open(f"{base_dir}/README.md", "w") as f:
        f.write("# C++ E-Commerce Test Fixture\n")
        f.write("- Circular Dependency: order_service.h -> payment_service.h -> notification_service.h -> order_service.h\n")
        f.write("- God Class: product_service.h (16 methods)\n")
        f.write("- Deep Inheritance: product.h -> generic_model.h -> auditable_entity.h -> base_entity.h\n")
        f.write("- Hardcoded Secret: constants.h\n")
        f.write("- Missing Try/Catch: payment_service.h (curl)\n")
        f.write("- Dangerous Function: config_loader.h (system())\n")

def make_zip(source_dir, output_filename):
    shutil.make_archive(output_filename.replace('.zip', ''), 'zip', source_dir)
    shutil.rmtree(source_dir)

if __name__ == "__main__":
    out_dir = "test_fixtures"
    os.makedirs(out_dir, exist_ok=True)
    
    # Remove old zips
    for z in glob.glob(f"{out_dir}/*.zip"):
        try:
            os.remove(z)
        except:
            pass

    # Python
    py_dir = f"{out_dir}/fixture_demo_python"
    create_python_fixture(py_dir)
    make_zip(py_dir, f"{out_dir}/fixture_demo_python.zip")
    
    # Java
    java_dir = f"{out_dir}/fixture_demo_java"
    create_java_fixture(java_dir)
    make_zip(java_dir, f"{out_dir}/fixture_demo_java.zip")
    
    # C++
    cpp_dir = f"{out_dir}/fixture_demo_cpp"
    create_cpp_fixture(cpp_dir)
    make_zip(cpp_dir, f"{out_dir}/fixture_demo_cpp.zip")
    
    print("Generated 3 realistic fixture zips!")
