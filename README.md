# IRCTC Tatkal Automation Agent

An enterprise-grade, fully autonomous RPA bot designed to navigate the IRCTC ticketing platform. Engineered to bypass Akamai Bot Manager, handle Angular frontend race conditions, and seamlessly execute high-precision Tatkal bookings.

## ✨ Features
- **Akamai Bot Manager Bypass:** Utilizes `undetected-chromedriver` to mask CDP fingerprints and emulate legitimate human sessions.
- **Precision Tatkal Scheduling:** System-clock-based timing loops (T-90s, T-50s, T-0s) to execute actions at the exact millisecond of the 10:00 AM / 11:00 AM rush.
- **Local OCR Captcha Solver:** Integrates Tesseract C++ engine and OpenCV image processing to automatically strip background noise and solve text captchas in 0.1 seconds. Includes whitelists for IRCTC symbol captchas.
- **Angular Race Condition Handling:** "Human Typer" algorithms inject keystrokes with calculated delays, and structural XPaths (Last-Element strategies) bypass PrimeNG DOM obfuscation.
- **Dynamic Payment Gateway Routing:** Automatically toggles between E-Wallet and UPI (Paytm) workflows via `.env` configuration.
- **Invisible PDF Generation:** Bypasses native Windows OS print dialogs by using Chrome DevTools Protocol (`Page.printToPDF`) to silently rip and scale the ticket directly from the browser's memory.

## 🛠️ Prerequisites
- Python 3.12+
- Google Chrome
- [Tesseract-OCR for Windows](https://github.com/UB-Mannheim/tesseract/wiki) (Installed to default `C:\Program Files\Tesseract-OCR\`)

## 📦 Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/IRCTC-Agent.git
   cd IRCTC-Agent
   ```
2. Install the required Python dependencies:
   ```bash
   pip install undetected-chromedriver selenium python-dotenv pytesseract opencv-python numpy Pillow
   ```
3. Create a `.env` file in the root directory based on the configuration below.

## ⚙️ Configuration (`.env`)
Create a `.env` file with your specific journey details:
```env
# Everything except username, password, passenger name in UPPERCASE
IRCTC_username = username
IRCTC_password = password
SOURCE_STATION=station_code
DESTINATION_STATION=station_code
# DD/MM/YYYY
JOURNEY_DATE=date
# GENERAL or TATKAL
JOURNEY_QUOTA=quota
TRAIN_NUMBER=train_number
# Example - SL, 3A, 2S
CLASS=class_code
# Example - PRASAD|25|M|NO PREFERENCE, SIDDHESH|25|M|LOWER
PASSENGERS=full name|age|M/F/T|seat_preference
BOOK_ONLY_IF_CONFIRMED=False
# E-WALLET or UPI
PAYMENT_METHOD=UPI
```

## 🚀 Usage
Simply execute the main script. If `JOURNEY_QUOTA` is set to `TATKAL`, the bot will automatically calculate the booking time (10 AM for AC, 11 AM for Non-AC) and hold execution until T-90 seconds.

```bash
python main_selenium.py
```

## ⚠️ Disclaimer
This project is for educational and research purposes only. Automating ticketing platforms may violate Terms of Service. Use at your own risk. The developers assume no liability for account suspensions or financial loss.
