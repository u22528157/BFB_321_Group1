!/usr/bin/env python3
"""
Database initialization script for Flask app
Converts MySQL schema to SQLite and creates the database
"""

import sqlite3
import os

def create_database():
    
    db_path = 'practical_management.db'
    
    
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"Removed existing database: {db_path}")
    
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    
    
    
    cursor.execute('''
        CREATE TABLE Student (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name VARCHAR(100) NOT NULL,
            email_address VARCHAR(100) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 2. Practical table
    cursor.execute('''
        CREATE TABLE Practical (
            prac_number INTEGER PRIMARY KEY AUTOINCREMENT,
            prac_name VARCHAR(50) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 3. Supplier table
    cursor.execute('''
        CREATE TABLE Supplier (
            supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_name VARCHAR(45) NOT NULL,
            supplier_location VARCHAR(45),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 4. Components table
    cursor.execute('''
        CREATE TABLE Components (
            component_id INTEGER PRIMARY KEY AUTOINCREMENT,
            component_name VARCHAR(45) NOT NULL,
            
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
        # 5. Supplier_components table
    cursor.execute('''
        CREATE TABLE Supplier_components (
            quantity_in_stock INTEGER NOT NULL,
            price_component_per_supplier DECIMAL(10,2),
            component_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (component_id, supplier_id),
            FOREIGN KEY (component_id) REFERENCES Components(component_id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id) ON DELETE CASCADE
        )
    ''')
    
    # 6. Alt_components table
    cursor.execute('''
        CREATE TABLE Alt_components (
            alt_component_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alt_component_name VARCHAR(45) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 7. Supplier_alt_components table
    cursor.execute('''
        CREATE TABLE Supplier_alt_components (
            alt_quantity_in_stock INTEGER,
            alt_price_component_per_supplier DECIMAL(10,2),
            alt_component_id INTEGER NOT NULL,
            supplier_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (alt_component_id, supplier_id),
            FOREIGN KEY (alt_component_id) REFERENCES Alt_components(alt_component_id) ON DELETE CASCADE,
            FOREIGN KEY (supplier_id) REFERENCES Supplier(supplier_id) ON DELETE CASCADE
        )
    ''')
    
    # 8. Practical_component table
    cursor.execute('''
        CREATE TABLE Practical_component (
            quantity INTEGER NOT NULL,
            component_id INTEGER NOT NULL,
            practical_number INTEGER NOT NULL,
            alt_component_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (component_id, practical_number),
            FOREIGN KEY (component_id) REFERENCES Components(component_id) ON DELETE CASCADE,
            FOREIGN KEY (practical_number) REFERENCES Practical(prac_number) ON DELETE CASCADE,
            FOREIGN KEY (alt_component_id) REFERENCES Alt_components(alt_component_id) ON DELETE SET NULL
        )
    ''')
    
   
    
    # Sample practicals
    cursor.execute('''
        INSERT INTO Practical (prac_name) VALUES
        ('Practical 1 - Digital Logic'),
        ('Practical 2 - Sequential Circuits'),
        ('Practical 3 - Combinational Logic'),
        ('Add-on Components')
    ''')
    
    # Sample suppliers
    cursor.execute('''
        INSERT INTO Supplier (supplier_name, supplier_location) VALUES
        ('ChipWorld', 'Online'),
        ('ElectroWorld', 'Cape Town'),
        ('ComponentHub', 'Online'),
        ('TechShop', 'Online'),
        ('CapacitorWorld', 'Online'),
        ('SwitchTech', 'Online'),
        ('DisplayTech', 'Online'),
        ('MakerSpace', 'Johannesburg')
    ''')
    
    # Sample components
    cursor.execute('''
        INSERT INTO Components (component_name) VALUES
        ('74HCT04 Hex Inverter'),
        ('74HCT08 AND Gate'),
        ('74HCT32 OR Gate'),
        ('74HCT86 XOR Gate'),
        ('LED Pack Mixed Colors'),
        ('100μF Capacitor'),
        ('4-input DIP switch'),
        ('74HCT574 D Flip-Flop'),
        ('Push Button SPST'),
        ('74HCT139 Decoder'),
        ('74HCT151 Multiplexer'),
        ('74HCT595 Shift Register'),
        ('7-Segment Display'),
        ('Digital Multimeter'),
        ('Soldering Kit')
    ''')
    
    # Sample supplier components (component_id, supplier_id, quantity, price)
    cursor.execute('''
        INSERT INTO Supplier_components (quantity_in_stock, price_component_per_supplier, component_id, supplier_id) VALUES
        -- 74HCT04 Hex Inverter (component_id=1)
        (50, 3.99, 1, 1),  -- ChipWorld
        (25, 4.50, 1, 2),  -- ElectroWorld
        -- 74HCT08 AND Gate (component_id=2)
        (40, 3.99, 2, 1),  -- ChipWorld
        (30, 4.25, 2, 3),  -- ComponentHub
        -- 74HCT32 OR Gate (component_id=3)
        (35, 3.99, 3, 1),  -- ChipWorld
        (20, 4.35, 3, 2),  -- ElectroWorld
        -- 74HCT86 XOR Gate (component_id=4)
        (45, 4.25, 4, 1),  -- ChipWorld
        (30, 4.75, 4, 3),  -- ComponentHub
        -- LED Pack Mixed Colors (component_id=5)
        (60, 5.99, 5, 3),  -- ComponentHub
        (40, 3.99, 5, 2),  -- ElectroWorld
        (80, 12.99, 5, 4), -- TechShop
        -- 100μF Capacitor (component_id=6)
        (100, 2.99, 6, 5), -- CapacitorWorld
        (50, 1.99, 6, 2),  -- ElectroWorld
        (70, 3.50, 6, 3),  -- ComponentHub
        -- 4-input DIP switch (component_id=7)
        (25, 2.25, 7, 6),  -- SwitchTech
        (15, 1.99, 7, 2),  -- ElectroWorld
        (30, 2.75, 7, 3),  -- ComponentHub
        -- 74HCT574 D Flip-Flop (component_id=8)
        (30, 4.99, 8, 1),   -- ChipWorld
        (20, 5.25, 8, 2),   -- ElectroWorld
        -- Push Button SPST (component_id=9)
        (50, 1.99, 9, 6),   -- SwitchTech
        (40, 1.75, 9, 3),   -- ComponentHub
        (30, 2.25, 9, 2),   -- ElectroWorld
        -- 74HCT139 Decoder (component_id=10)
        (25, 4.50, 10, 1),  -- ChipWorld
        (20, 4.75, 10, 3),  -- ComponentHub
        (15, 4.99, 10, 2),  -- ElectroWorld
        -- 74HCT151 Multiplexer (component_id=11)
        (35, 4.25, 11, 1),  -- ChipWorld
        (25, 4.50, 11, 3),  -- ComponentHub
        -- 74HCT595 Shift Register (component_id=12)
        (40, 3.99, 12, 1),  -- ChipWorld
        (25, 4.25, 12, 2),  -- ElectroWorld
        -- 7-Segment Display (component_id=13)
        (30, 2.99, 13, 7),  -- DisplayTech
        (25, 5.99, 13, 3),  -- ComponentHub
        (20, 8.99, 13, 2),  -- ElectroWorld
        -- Digital Multimeter (component_id=14)
        (10, 45.99, 14, 8), -- MakerSpace
        (15, 35.99, 14, 4), -- TechShop
        -- Soldering Kit (component_id=15)
        (20, 29.99, 15, 8), -- MakerSpace
        (25, 49.99, 15, 4)  -- TechShop
    ''')
    
    # Sample alternative components
    cursor.execute('''
        INSERT INTO Alt_components (alt_component_name) VALUES
        ('Arduino Nano'),
        ('Mini Breadboard'),
        ('Micro Servo'),
        ('NodeMCU'),
        ('Raspberry Pi Pico')
    ''')
    
    # Sample supplier alternative components
    cursor.execute('''
        INSERT INTO Supplier_alt_components (alt_quantity_in_stock, alt_price_component_per_supplier, alt_component_id, supplier_id) VALUES
        -- Arduino Nano (alt_component_id=1)
        (20, 18.99, 1, 8),  -- MakerSpace
        (15, 22.50, 1, 4),  -- TechShop
        -- Mini Breadboard (alt_component_id=2)
        (50, 5.99, 2, 3),   -- ComponentHub
        (30, 7.50, 2, 8),   -- MakerSpace
        -- Micro Servo (alt_component_id=3)
        (25, 12.99, 3, 4),  -- TechShop
        (20, 15.99, 3, 8),  -- MakerSpace
        -- NodeMCU (alt_component_id=4)
        (15, 24.99, 4, 8),  -- MakerSpace
        (10, 27.50, 4, 4),  -- TechShop
        -- Raspberry Pi Pico (alt_component_id=5)
        (12, 35.99, 5, 4),  -- TechShop
        (8, 39.99, 5, 8)    -- MakerSpace
    ''')
    
    # Sample practical components (quantity, component_id, practical_number, alt_component_id)
    cursor.execute('''
        INSERT INTO Practical_component (quantity, component_id, practical_number, alt_component_id) VALUES
        -- Practical 1 - Digital Logic
        (1, 1, 1, 1),     -- 74HCT04 Hex Inverter (alt: Arduino Nano)
        (1, 2, 1, NULL),  -- 74HCT08 AND Gate
        (1, 3, 1, NULL),  -- 74HCT32 OR Gate
        (1, 4, 1, NULL),  -- 74HCT86 XOR Gate
        (1, 5, 1, NULL),  -- LED Pack Mixed Colors
        (1, 6, 1, NULL),  -- 100μF Capacitor
        (1, 7, 1, 2),     -- 4-input DIP switch (alt: Mini Breadboard)
        -- Practical 2 - Sequential Circuits  
        (1, 8, 2, 3),     -- 74HCT574 D Flip-Flop (alt: Micro Servo)
        (2, 9, 2, NULL),  -- Push Button SPST
        (1, 10, 2, NULL), -- 74HCT139 Decoder
        (1, 11, 2, NULL), -- 74HCT151 Multiplexer
        (1, 12, 2, NULL), -- 74HCT595 Shift Register
        (1, 13, 2, NULL), -- 7-Segment Display
        -- Practical 3 - Combinational Logic (similar to Practical 2)
        (1, 8, 3, 4),     -- 74HCT574 D Flip-Flop (alt: NodeMCU)
        (2, 9, 3, NULL),  -- Push Button SPST
        (1, 10, 3, NULL), -- 74HCT139 Decoder
        (1, 11, 3, NULL), -- 74HCT151 Multiplexer
        (1, 12, 3, NULL), -- 74HCT595 Shift Register
        (1, 13, 3, NULL), -- 7-Segment Display
        -- Add-on Components
        (1, 14, 4, NULL), -- Digital Multimeter
        (1, 15, 4, NULL)  -- Soldering Kit
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database created successfully: {db_path}")
    print("Tables created:")
    print("- Student (with full_name, email_address, password_hash)")
    print("- Practical, Supplier, Components")
    print("- Supplier_components, Alt_components, Supplier_alt_components")
    print("- Practical_component")
    print("\nSample data inserted for all tables except Student (users will register)")

if __name__ == '__main__':
    create_database()