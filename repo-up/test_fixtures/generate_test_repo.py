import os
import zipfile
import shutil

ROOT_DIR = "repo-up-comprehensive-test"

files = {
    # PYTHON
    "python_service/app.py": """import sys
from .service import process_data

def calculate_total(items):
    total = 0
    for item in items:
        total += item["price"]
    # Intentional: Undefined Name (undefined_discount)
    return total + undefined_discount

def get_user_status(user):
    # Intentional: Inconsistent Return
    if user:
        return "active"
    else:
        return
""",
    "python_service/auth.py": """import hashlib

def hash_password(pwd):
    # Intentional: Weak Hash
    return hashlib.md5(pwd.encode()).hexdigest()

# Intentional: Fake Secret
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"

def dangerous_eval(expression):
    # Intentional: Unsafe dynamic execution
    return eval(expression)
""",
    "python_service/database.py": """import yaml

def load_config(config_string):
    # Intentional: Unsafe Deserialization
    return yaml.load(config_string, Loader=yaml.Loader)
""",
    "python_service/service.py": """from .utils import helper

def build_response(data, unused_arg):
    # Intentional: Unused Variable
    debug_value = "unused"
    # Intentional: Long Line
    return {"data": data, "message": "This is a very very very very very very very very very very very very very very very very very very very very long line"}
""",
    "python_service/utils.py": """def helper():
    # Intentional: Exception handling issue (bare except or pass)
    try:
        open("nonexistent.txt")
    except:
        pass
""",
    "python_service/cycle_a.py": """from .cycle_b import do_b

def do_a():
    return do_b()
""",
    "python_service/cycle_b.py": """from .cycle_a import do_a

def do_b():
    return do_a()
""",
    "python_service/duplicate_a.py": """def calculate_discount_a(items):
    total = 0
    for item in items:
        total += item["price"]
    return total * 0.9
""",
    "python_service/duplicate_b.py": """def calculate_discount_b(products):
    amount = 0
    for product in products:
        amount += product["price"]
    return amount * 0.9
""",
    "python_service/tests/test_service.py": """def test_dummy():
    assert True
""",
    "python_service/__init__.py": "",

    # TYPESCRIPT
    "typescript_service/app.ts": """import { processCheckout } from './checkout';

const VERY_LONG_STRING = "This is a very very very very very very very very very very very very very very very very very very very very long line";

export function init() {
    let unusedVar = 42;
    // @ts-ignore
    return missingIdentifier;
}
""",
    "typescript_service/checkout.ts": """import { confirmPayment } from './paymentGateway';
import { updateInventory } from './inventory';

export async function processCheckout(payment: any) {
    // Missing error handling on async operation - candidate for deterministic repair
    await confirmPayment(payment);
    await updateInventory();
}
""",
    "typescript_service/paymentGateway.ts": """import * as crypto from 'crypto';

export async function confirmPayment(payment: any) {
    // Weak crypto
    const hash = crypto.createHash('md5').update('fake').digest('hex');
    // Fake token
    const token = "ghp_1234567890abcdef1234567890abcdef";
    return true;
}
""",
    "typescript_service/inventory.ts": """import { createOrder } from './order';

export async function updateInventory() {
    return createOrder();
}
""",
    "typescript_service/order.ts": """export function createOrder() {
    // Unsafe eval pattern
    eval('console.log("order created")');
}
""",
    "typescript_service/tokenValidator.ts": """// Clean file
export function isValidToken(token: string): boolean {
    return token.length > 10;
}
""",
    "typescript_service/cycleA.ts": """import { b } from './cycleB';
export const a = () => b();
""",
    "typescript_service/cycleB.ts": """import { a } from './cycleA';
export const b = () => a();
""",
    "typescript_service/tests/checkout.test.ts": """test('dummy', () => { expect(1).toBe(1); });
""",

    # JAVASCRIPT
    "javascript_service/server.js": """const handler = require('./handler');
const { doA } = require('./cycleA');

let unusedVar = "hello";

// Unresolved identifier
console.log(missingVar);
""",
    "javascript_service/handler.js": """const db = require('./database');
const child_process = require('child_process');

function buildCommand() {
    // Dangerous child_process API pattern
    return child_process.exec;
}

// Long line
const description = "This is a very very very very very very very very very very very very very very very very very very very very long line";
""",
    "javascript_service/database.js": """const crypto = require('crypto');

function hash() {
    // Weak crypto
    return crypto.createHash('md5').update('test').digest('hex');
}
""",
    "javascript_service/cycleA.js": """const { doB } = require('./cycleB');
exports.doA = () => doB();
""",
    "javascript_service/cycleB.js": """const { doA } = require('./cycleA');
exports.doB = () => doA();
""",
    "javascript_service/duplicateA.js": """function calc(items) {
    let t = 0;
    for(let i of items) t += i.price;
    return t * 0.9;
}
""",
    "javascript_service/duplicateB.js": """function compute(products) {
    let sum = 0;
    for(let p of products) sum += p.price;
    return sum * 0.9;
}
""",

    # JAVA
    "java_service/pom.xml": """<project><modelVersion>4.0.0</modelVersion><groupId>com.repoup</groupId><artifactId>test</artifactId><version>1.0</version></project>""",
    "java_service/src/main/java/com/repoup/Application.java": """package com.repoup;

public class Application {
    public static void main(String[] args) {
        PaymentService ps = new PaymentService();
        ps.process();
        // Unresolved symbol
        System.out.println(UnknownClass.val);
        // Unused variable
        int unused = 42;
    }
}
""",
    "java_service/src/main/java/com/repoup/BaseService.java": """package com.repoup;
public class BaseService {
    public void init() {}
}
""",
    "java_service/src/main/java/com/repoup/DatabaseService.java": """package com.repoup;
import java.security.MessageDigest;

public class DatabaseService extends BaseService {
    public void query() {
        try {
            // Weak crypto
            MessageDigest md = MessageDigest.getInstance("MD5");
        } catch(Exception e) {
            // Exception handling issue (ignored)
        }
        
        // Hardcoded credential
        String awsKey = "AKIAIOSFODNN7EXAMPLE";
    }
}
""",
    "java_service/src/main/java/com/repoup/PaymentService.java": """package com.repoup;

public class PaymentService extends DatabaseService {
    public void process() {
        try {
            // Dangerous API
            Runtime.getRuntime().exec("ls");
        } catch(Exception e) {}
    }
}
""",
    "java_service/src/main/java/com/repoup/CycleA.java": """package com.repoup;
public class CycleA {
    public void a() { new CycleB().b(); }
}
""",
    "java_service/src/main/java/com/repoup/CycleB.java": """package com.repoup;
public class CycleB {
    public void b() { new CycleA().a(); }
}
""",
    "java_service/src/main/java/com/repoup/DuplicateA.java": """package com.repoup;
public class DuplicateA {
    public double calc(double[] items) {
        double total = 0;
        for (double d : items) total += d;
        return total * 0.9;
    }
}
""",
    "java_service/src/main/java/com/repoup/DuplicateB.java": """package com.repoup;
public class DuplicateB {
    public double compute(double[] products) {
        double sum = 0;
        for (double p : products) sum += p;
        return sum * 0.9;
    }
}
""",

    # CPP
    "cpp_service/main.cpp": """#include "payment.h"
#include "utils.h"

int main() {
    processPayment();
    // Unresolved symbol
    unknownFunction();
    return 0;
}
""",
    "cpp_service/payment.h": "void processPayment();\n",
    "cpp_service/payment.cpp": """#include "payment.h"
#include "database.h"
#include <cstdlib>

void processPayment() {
    int unused = 42;
    // Dangerous API
    system("echo Hello");
    queryDb();
}
""",
    "cpp_service/database.h": "void queryDb();\n",
    "cpp_service/database.cpp": """#include "database.h"
#include <openssl/md5.h>

void queryDb() {
    // Fake secret
    const char* token = "ghp_1234567890abcdef1234567890abcdef";
    // Weak crypto reference
    MD5_CTX ctx;
}
""",
    "cpp_service/cycle_a.h": "void cycleA();\n",
    "cpp_service/cycle_a.cpp": """#include "cycle_a.h"
#include "cycle_b.h"
void cycleA() { cycleB(); }
""",
    "cpp_service/cycle_b.h": "void cycleB();\n",
    "cpp_service/cycle_b.cpp": """#include "cycle_b.h"
#include "cycle_a.h"
void cycleB() { cycleA(); }
""",
    "cpp_service/utils.h": "void helper();\n",
    "cpp_service/utils.cpp": """#include "utils.h"
void helper() {}
""",
    "cpp_service/duplicate_a.cpp": """double calc(double* items, int size) {
    double total = 0;
    for(int i=0; i<size; i++) total += items[i];
    return total * 0.9;
}
""",
    "cpp_service/duplicate_b.cpp": """double compute(double* products, int count) {
    double sum = 0;
    for(int j=0; j<count; j++) sum += products[j];
    return sum * 0.9;
}
""",

    # Meta
    "README.md": "# Repo-Up Comprehensive Analysis and Sandbox Test Repository\nThis is a synthetic test fixture. It intentionally contains code-quality/security/structural issues.",
    "TEST_EXPECTATIONS.md": """LANGUAGE: Python
FILE: python_service/auth.py
EXPECTED ISSUE: MD5 usage
EXPECTED CATEGORY: security

LANGUAGE: TypeScript
FILE: typescript_service/checkout.ts
EXPECTED ISSUE: Missing try/catch around async call
EXPECTED CATEGORY: code smell
EXPECTED REPAIR POSSIBILITY: Yes
""",
    "package.json": '{"name":"test-repo","version":"1.0.0"}',
    "requirements.txt": "pyyaml\n",
}

def generate_repo():
    if os.path.exists(ROOT_DIR):
        shutil.rmtree(ROOT_DIR)
    
    for filepath, content in files.items():
        full_path = os.path.join(ROOT_DIR, filepath)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
            
    zip_name = f"{ROOT_DIR}.zip"
    if os.path.exists(zip_name):
        os.remove(zip_name)
        
    with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files_in_dir in os.walk(ROOT_DIR):
            for file in files_in_dir:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(ROOT_DIR))
                zipf.write(file_path, arcname)
                
    print(f"Generated {zip_name} with {len(files)} files.")

if __name__ == "__main__":
    generate_repo()
