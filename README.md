# Drug Finder

Drug Finder is a full-stack web application that helps users (clients/patients) find medicines and medical devices, locate pharmacies, manage orders, and interact with an AI-powered assistant for health and project-related queries. The system supports multiple user roles: clients, pharmacists, and admins, each with tailored dashboards and features.

---

## 🚀 Key Features

- **Medicine & Device Search:** Search for medicines/devices, view details, and find pharmacies that stock them.
- **Pharmacy Locator:** Map and list views to find nearby pharmacies.
- **Shopping Cart & Orders:** Add items to cart, checkout, and track order history.
- **Payments:** Integrated payment system for order processing.
- **Reviews & Ratings:** Clients can review pharmacies and products.
- **Notifications:** Real-time notifications for order status, reminders, and more.
- **AI Chatbot:** Intelligent assistant that answers health, medicine, and project-related questions using advanced NLP and retrieval-augmented generation (RAG).
- **Role-based Dashboards:** Separate interfaces and features for clients, pharmacists, and admins.
- **Admin Panel:** Manage users, pharmacies, medicines, orders, and handle pharmacist requests.

---

## 🛠️ Tech Stack

### Backend
- **Framework:** Django 5, Django REST Framework
- **AI/NLP:** LangChain, HuggingFace Transformers, RAG (Retrieval-Augmented Generation)
- **Database:** PostgreSQL (with Postgres full-text search and Trigram similarity)
- **Vector Store:** Supabase (for document embeddings and retrieval)
- **Real-time:** Django Channels, Redis, Socket.io (Node.js microservice for real-time features)
- **Payments:** Stripe
- **Other:** Google Auth, CORS, JWT authentication

### Frontend
- **Framework:** React (Create React App)
- **State Management:** Redux Toolkit
- **Styling:** Tailwind CSS
- **Maps:** Mapbox GL, Google Maps API
- **UI Libraries:** Headless UI, Heroicons, Lucide, React Icons, Framer Motion
- **Testing:** React Testing Library, Jest
- **Notifications:** React Hot Toast, React Toastify, SweetAlert2
- **Real-time:** Socket.io-client
- **AI Chat:** Integrated chatbox with backend AI endpoint

---

## 📁 Project Structure

### Backend
```
backend-drug-finder/
├── config/                # Project settings and configuration
├── users/                 # User models (User, Client, Pharmacist)
├── medical_stores/        # Pharmacy/store models
├── inventory/             # Medicines and medical devices
├── orders/                # Cart and order management
├── payments/              # Payment processing
├── reviews/               # Reviews and ratings
├── notifications/         # User notifications
├── AI_chat/               # AI assistant logic and endpoints
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
```

### Frontend
```
front-drug-finder/
├── src/
│   ├── pages/             # Main app pages (client, pharmacist, admin, AI chat, etc.)
│   ├── components/        # Reusable UI components
│   ├── features/          # Redux slices and feature logic
│   ├── services/          # API service layer (axios)
│   ├── context/           # React context providers
│   ├── hooks/             # Custom React hooks
│   ├── utils/             # Utility functions
│   ├── app/               # App-level config
│   └── index.js           # App entry point
├── public/                # Static assets
├── package.json           # JS dependencies and scripts
├── tailwind.config.js     # Tailwind CSS config
```

---

## ⚡ Setup & Installation

### Backend

1. **Install dependencies:**
   ```bash
   cd backend-drug-finder
   pip install -r requirements.txt
   ```
2. **Run migrations:**
   ```bash
   python manage.py migrate
   ```
3. **Start the backend server:**
   ```bash
   python manage.py runserver
   ```
4. **(Optional) Start Node.js real-time server:**
   ```bash
   npm install
   node server.js
   ```

### Frontend

1. **Install dependencies:**
   ```bash
   cd front-drug-finder
   npm install
   ```
2. **Start the frontend server:**
   ```bash
   npm start
   ```

---

## 🧑‍💻 Usage

- Access the frontend at `http://localhost:3000`
- Backend API runs at `http://localhost:8000`
- Use the AI Chatbot via the floating chat button or `/chat` route

---

## 🤖 AI Chatbot

- **Capabilities:** Answers health, medicine, pharmacy, and project-related questions.
- **Tech:** Uses LangChain, HuggingFace, and Supabase for RAG.
- **How to use:** Type your question in the chatbox. The bot can answer follow-ups, provide pharmacy locations, and explain project features.

---

## 👥 User Roles

- **Client:** Search medicines, order, review, chat with AI.
- **Pharmacist:** Manage store inventory, orders, profile.
- **Admin:** Manage users, pharmacies, medicines, orders, and handle requests.

---

## 🤝 Contributing

1. Fork the repo
2. Create your feature branch (`git checkout -b feature/YourFeature`)
3. Commit your changes (`git commit -am 'Add some feature'`)
4. Push to the branch (`git push origin feature/YourFeature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 🙏 Credits

- [Create React App](https://github.com/facebook/create-react-app)
- [Django](https://www.djangoproject.com/)
- [LangChain](https://www.langchain.com/)
- [HuggingFace](https://huggingface.co/)
- [Supabase](https://supabase.com/)
- [Stripe](https://stripe.com/)
- [Mapbox](https://www.mapbox.com/) 