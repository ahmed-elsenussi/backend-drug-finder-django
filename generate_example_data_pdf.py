from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=14)
pdf.cell(0, 10, "Example Data for MedicalStore and Medicine", ln=True, align='C')

pdf.ln(10)
pdf.set_font("Arial", size=12)
pdf.cell(0, 10, "MedicalStore Example Data", ln=True)
pdf.set_font("Arial", size=10)
stores = [
    ["id", "store_name", "store_address"],
    ["1", "Al Shifa Pharmacy", "123 Main St, Cairo"],
    ["2", "El Ezaby Pharmacy", "456 Nile Ave, Giza"],
    ["3", "United Pharmacy", "789 Tahrir Sq, Alexandria"]
]
for row in stores:
    pdf.cell(0, 8, " | ".join(row), ln=True)

pdf.ln(10)
pdf.set_font("Arial", size=12)
pdf.cell(0, 10, "Medicine Example Data", ln=True)
pdf.set_font("Arial", size=10)
medicines = [
    ["id", "brand_name", "generic_name", "chemical_name", "description", "atc_code", "cas_number", "price", "stock", "store (id)"],
    ["1", "Panadol", "Paracetamol", "Acetaminophen", "Pain reliever and fever reducer", "N02BE01", "103-90-2", "20.00", "100", "1"],
    ["2", "Augmentin", "Amoxicillin-Clavulanate", "Amoxicillin", "Antibiotic for infections", "J01CR02", "26787-78-0", "55.00", "50", "2"],
    ["3", "Voltaren", "Diclofenac", "Diclofenac Sodium", "Anti-inflammatory for pain relief", "M01AB05", "15307-79-6", "35.00", "80", "3"]
]
for row in medicines:
    pdf.cell(0, 8, " | ".join(row), ln=True)

pdf.output("example_data.pdf")
print("PDF file 'example_data.pdf' created successfully.")