---

## 🗂️ Project Structure

```
BackendDrugFinder/
├── ⚙️ config/             
├── 👤 users/             
│   └── models.py
│       ├────────── User (custom)
│       ├────────── Client 
│       └────────── Pharmacist 
│
├── 🏪 medical_stores/     
│   └── models.py
│       └────────── MedicalStore
│
├── 💊 inventory/           
│   └── models.py
│       ├────────── Medicine
│       └────────── MedicalDevice
│
├── 🛒 orders/             
│   └── models.py
│       ├────────── Cart
│       └────────── Order
│
├── 💳 payments/           
│   └── models.py
│       └────────── Payment
│
├── ⭐ reviews/             
│   └── models.py
│       └────────── Review
│
├── 🔔 notifications/       
│   └── models.py
│       └────────── Notification
```

## 🗂️ ERD

![ERD_Graduation_ITI_(4)](https://github.com/user-attachments/assets/404683c6-ac8f-4ee6-886f-ba455e3e19ca)

DON'T FORGET:
pip install -r requirements.txt

ON PUSH:
pip freeze > requirements.txt

---
