<div align="center">

# 📧 IT Support Email Manager

### 🤖 AI-Powered Email Priority Classification System

<p align="center">
  <strong>Automatically classify IT support tickets by priority using DistilBERT NLP</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/PyTorch-2.0+-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white" alt="PyTorch">
  <img src="https://img.shields.io/badge/Transformers-HuggingFace-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black" alt="Transformers">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Active-success?style=flat-square" alt="Status">
  <img src="https://img.shields.io/badge/Platform-Windows-blue?style=flat-square" alt="Platform">
</p>

---

<p align="center">
  <a href="#-features">Features</a> •
  <a href="#-installation">Installation</a> •
  <a href="#-how-to-use">Usage</a> •
  <a href="#-machine-learning-model">ML Model</a> •
  <a href="#-author">Author</a>
</p>

</div>

---

## ✨ Features

### Core Functionality
- 🔐 **Secure Email Login** - Connect to Gmail via IMAP with App Password authentication
- 📧 **Automatic Email Fetching** - Load and process unread emails from your inbox
- 🤖 **AI-Powered Priority Classification** - Uses fine-tuned DistilBERT model to classify tickets (High, Medium, Low)
- 🔍 **Smart Search & Filter** - Search emails by subject, sender, or content
- 📊 **Excel Export** - Download all tickets as Excel report for analysis

### Ticket Management
- 📋 **Status Tracking** - Track tickets as New, Escalated, or Done
- ⚡ **Quick Actions** - Escalate issues or mark them as resolved
- ⏱️ **Resolution Time Logging** - Record time spent resolving each issue
- 🗑️ **Delete Tickets** - Remove unwanted tickets from the list

### User Interface
- 🎨 **Modern UI Design** - Clean, professional interface with custom styling
- 🖱️ **Interactive Buttons** - Hover and click effects on all buttons
- 📱 **Responsive Layout** - Maximized window with resizable components
- 🏷️ **Priority Badges** - Color-coded priority indicators (Red=High, Orange=Medium, Green=Low)

---

## 📁 Project Structure

```
helpdesk-nlp/
├── app/
│   └── app.py              # Main application file
├── data/
│   └── dataset.csv         # Training dataset
├── notebook/
│   ├── EDA.ipynb           # Exploratory Data Analysis
│   ├── NLP_Model.ipynb     # Model training notebook
│   └── requirements.txt    # Notebook dependencies
├── weight/
│   └── best.pt             # Trained model weights
├── README.md
└── requirements.txt
```

---

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Step 1: Clone or Download the Project
```bash
cd helpdesk-nlp
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
```bash
cd app
python app.py
```

---

## 📧 Gmail Setup (Required)

To use this application with Gmail, you must create an **App Password**:

### Step 1: Enable 2-Step Verification
1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **2-Step Verification**
3. Follow the prompts to enable it

### Step 2: Generate App Password
1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select **"Mail"** as the app
3. Select **"Windows Computer"** as the device (or "Other")
4. Click **"Generate"**
5. Copy the **16-character password** (without spaces)

### Step 3: Login to Application
- **Email**: Your full Gmail address (e.g., `yourname@gmail.com`)
- **Password**: The 16-character App Password (NOT your regular Gmail password)

---

## 📖 How to Use

### 1. Login
- Enter your Gmail address and App Password
- Click **"Login"** button

### 2. Load Emails
- Click **"Load Emails"** to fetch unread messages
- Emails are automatically classified by AI model

### 3. View & Manage Tickets
- **Double-click** any row to view email details
- Use **Search bar** to filter by subject, sender, or content
- **Escalate** - Forward issue to team
- **Mark Done** - Record resolution time and close ticket

### 4. Export Report
- Click **"Download"** to export all tickets to Excel

### 5. Logout
- Click **"Logout"** to disconnect and return to login screen

---

## 🧠 Machine Learning Model

The application uses a fine-tuned **DistilBERT** model for email priority classification:

| Component | Description |
|-----------|-------------|
| Base Model | `distilbert-base-uncased` |
| Task | Sequence Classification |
| Classes | High, Medium, Low |
| Framework | PyTorch + Transformers |

The model is trained on IT support ticket data and saved in `weight/best.pt`.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|------------|--------|
| **Python 3.8+** | Core programming language |
| **Tkinter** | Desktop GUI framework |
| **PyTorch** | Deep learning framework |
| **Transformers** | NLP model library (Hugging Face) |
| **Pandas** | Data manipulation |
| **OpenPyXL** | Excel file export |
| **IMAP** | Email protocol (built-in) |

---

## ❗ Troubleshooting

### "Login failed" Error
- ✅ Verify you're using App Password, not regular password
- ✅ Check that 2-Step Verification is enabled
- ✅ Ensure IMAP is enabled in Gmail settings

### "Failed to check emails" Error
- ✅ Check your internet connection
- ✅ Re-login to refresh the connection
- ✅ Make sure you have unread emails in inbox

### Model Loading Issues
- ✅ Ensure `weight/best.pt` file exists
- ✅ Run from the `app/` directory
- ✅ Check PyTorch and Transformers are installed

### Slow Performance
- ✅ First run downloads DistilBERT tokenizer (~250MB)
- ✅ Use GPU if available for faster inference

---

## 🔒 Security Notes

- 🔐 App Passwords are specific to this application only
- 🚫 The app **only reads** emails, never sends or modifies them
- 🗑️ You can revoke App Passwords anytime from Google Account
- ⚠️ Never share your App Password with anyone

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the [issues page](https://github.com/SoloWPM23/HelpdeskTicketClassificationSystem/issues).

1. Fork the project
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

<div align="center">

## 👨‍💻 Author

<img src="https://img.shields.io/badge/Made%20with-❤️-red?style=for-the-badge" alt="Made with love">

### **SoloWPM23**

<p>
  <a href="https://github.com/SoloWPM23">
    <img src="https://img.shields.io/badge/GitHub-SoloWPM23-181717?style=for-the-badge&logo=github&logoColor=white" alt="GitHub">
  </a>
</p>

<p align="center">
  <i>Developed as part of an NLP learning project for IT Support ticket automation</i>
</p>

---

<p align="center">
  ⭐ Star this repository if you find it helpful! ⭐
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/SoloWPM23/HelpdeskTicketClassificationSystem?style=social" alt="Stars">
  <img src="https://img.shields.io/github/forks/SoloWPM23/HelpdeskTicketClassificationSystem?style=social" alt="Forks">
</p>
