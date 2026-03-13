-- ============================================================================
-- AgriVision Pro - Database Schema
-- PostgreSQL SQL Script
-- ============================================================================

-- Create Farmers Table
CREATE TABLE IF NOT EXISTS farmers (
    id SERIAL PRIMARY KEY,
    phone VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100),
    location VARCHAR(200),
    language VARCHAR(20) DEFAULT 'hi',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Crop Reports Table
CREATE TABLE IF NOT EXISTS crop_reports (
    id SERIAL PRIMARY KEY,
    farmer_id INTEGER NOT NULL REFERENCES farmers(id) ON DELETE CASCADE,
    crop_name VARCHAR(100),
    disease_name VARCHAR(100),
    confidence_score FLOAT DEFAULT 0.0,
    treatment TEXT,
    image_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Treatments Table (Reference Data)
CREATE TABLE IF NOT EXISTS treatments (
    id SERIAL PRIMARY KEY,
    disease_name VARCHAR(100) UNIQUE,
    pesticide_name VARCHAR(200),
    dosage VARCHAR(100),
    application_method VARCHAR(200),
    cost FLOAT DEFAULT 0.0,
    local_dealer VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes for Better Performance
CREATE INDEX IF NOT EXISTS idx_farmers_phone ON farmers(phone);
CREATE INDEX IF NOT EXISTS idx_crop_reports_farmer_id ON crop_reports(farmer_id);
CREATE INDEX IF NOT EXISTS idx_crop_reports_created_at ON crop_reports(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_treatments_disease ON treatments(disease_name);

-- ============================================================================
-- Sample Data for Testing (Optional)
-- ============================================================================

-- Insert sample farmer
INSERT INTO farmers (phone, name, location, language)
VALUES ('9876543210', 'Ramesh Kumar', 'Karnataka', 'hi')
ON CONFLICT (phone) DO NOTHING;

-- Insert common diseases and treatments
INSERT INTO treatments (disease_name, pesticide_name, dosage, application_method, cost)
VALUES 
    ('Rice Blast', 'Tricyclazole', '0.6g/L', 'Spray', 250),
    ('Powdery Mildew', 'Sulfur', '20ml/10L', 'Spray', 150),
    ('Early Blight', 'Mancozeb', '2.5g/L', 'Spray', 200),
    ('Late Blight', 'Metalaxyl', '1ml/L', 'Spray', 300),
    ('Bacterial Leaf Blight', 'Streptomycin', '2ml/L', 'Spray', 400)
ON CONFLICT (disease_name) DO NOTHING;

-- ============================================================================
-- End of Schema
-- ============================================================================