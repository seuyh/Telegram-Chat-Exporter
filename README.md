# Telegram Chat Exporter

A powerful and sophisticated console-based tool to export your Telegram chat history into beautiful, self-contained HTML files. Engineered for efficiency and reliability, it uses an SQLite backend to handle even massive chats with minimal memory usage and includes a fully-featured interactive media gallery.

---

## ✨ Key Features

* **🗂️ Efficient & Robust**: Utilizes a temporary SQLite database to process chats of any size with very low memory overhead. The entire export process is a single, continuous operation.
* **🖼️ Interactive Media Gallery**: The exported HTML file includes a beautiful, built-in media viewer. Click any image or video to open a full-screen gallery with keyboard (←/→) and touch-swipe navigation.
* **🔒 Export Private Content**: Seamlessly export messages and media from private chats, groups, and channels that you have access to.
* **🔐 Secure Session Management**: Authenticate once and reuse your session for future exports. Your credentials are never stored in plain text.
* **🎨 Beautiful HTML Output**: Generates a clean, modern, and fully self-contained HTML file. No external dependencies are needed to view the exported chat.
* **⚙️ Advanced Export Options**:
    * Browse and select chats from an interactive list.
    * Search for chats by name.
    * Export directly using a User/Chat/Channel ID or username.
    * Choose to export with or without media files.
    * Set a maximum file size for media downloads to skip large files.
* **🛡️ Configurable**: Features adjustable request delays with built-in presets (Safe, Balanced, Risky) to protect your account from API rate limits.

---

## ⚠️ Important Disclaimer & Risks

This is an unofficial tool and is not affiliated with Telegram. Using the Telegram API for automation always carries some risk.

* **API Rate Limits**: Sending too many requests in a short period can result in temporary limitations from Telegram (FloodWaitError). This tool is designed to handle these errors gracefully, but aggressive use is discouraged. Please note that export speed is often dictated by these API limits, not by the performance of the script or your computer.
* **Account Suspension**: While highly unlikely with normal use, excessive or abusive behavior could potentially lead to the suspension of your Telegram account.
* **Recommendation**: For your primary or important accounts, it is **strongly recommended** to use the **"Safe"** or **"Balanced"** delay settings within the tool to minimize risks.

The developers of this tool are not responsible for any consequences resulting from its use. **Use it at your own risk.**

---

## 📂 Project Structure

The project is organized into a modular structure for clarity and maintainability.

```

telegram-chat-exporter/
│
├── core/                 \# Core application logic package
│   ├── client\_manager.py \# Manages Telethon client and sessions
│   ├── exporter.py       \# Handles the main export logic (API -\> SQLite -\> HTML)
│   ├── html\_generator.py \# Generates the final HTML report with the media viewer
│   ├── media\_handler.py  \# Manages media file downloads
│   ├── settings.py       \# Manages configurable delay settings
│   ├── ui.py             \# Handles all command-line user interactions (menus, prompts)
│   └── utils.py          \# Helper utility functions
│
│── sessions/             \# Directory with your Telethon sessions
│   └── your_account.session \# Session file
│
├── main.py               \# Main entry point of the application
├── requirements.txt      \# Python dependencies
└── README.md             \# This file

````

---

## 🚀 Getting Started

### Prerequisites

* **Python 3.8+**
* **Telegram API Credentials** (`API ID` and `API Hash`): You must obtain these from [my.telegram.org](https://my.telegram.org).

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/seuyh/telegram-chat-exporter.git](https://github.com/your-username/telegram-chat-exporter.git)
    cd telegram-chat-exporter
    ```

2.  **Install the required libraries:**
    ```bash
    pip install -r requirements.txt
    ```

### How to Use

1.  **Run the script from your terminal:**
    ```bash
    python main.py
    ```

2.  **First-Time Setup (Create a Session):**
    * On your first run, choose `Create new session`.
    * Enter your `API ID`, `API Hash`, phone number, and a name for the session file (e.g., `my_account`).
    * You will receive a login code from Telegram. Enter it when prompted.
    * If you have 2-Step Verification enabled, you will also be asked for your password.
    * Your session will be saved in the `sessions/` folder.

    > **Note on Sessions:** This tool uses **Telethon** for session management. Only session files created by this tool or other Telethon-based applications are compatible.

3.  **Exporting a Chat:**
    * On subsequent runs, choose `Use existing session` to log in instantly.
    * From the main menu, you can browse, search, or directly specify the chat you wish to export.
    * Follow the on-screen prompts to configure your export (e.g., download media, set a max file size).

4.  **Viewing the Result:**
    * Once the process is complete, you will find a new folder inside the `exports/` directory containing your `messages.html` file and any downloaded media.
    * Open the `messages.html` file in any modern web browser to view your exported chat.

---

## 🤝 Contributing & Feedback

Found a bug, have a suggestion for a new feature, or need an improvement? We'd love to hear from you!

Please feel free to open an issue on the [**GitHub Issues**](https://github.com/seuyh/telegram-chat-exporter/issues) page.