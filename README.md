[![JobVault Libre logo](src/myapp/assets/JV_logofull.png)](https://jobvault-libre.mhevia.com/)

**A privacy-focused, open-source job application tracker that keeps your data under your control.**

Website: https://jobvault-libre.mhevia.com/

JobVault Libre is a local desktop application designed to help job seekers organise and track their applications without relying on cloud accounts, subscriptions, or third-party data storage.

Your job search data stays on your machine. Track applications, deadlines, documents, notes, follow-ups, and outcomes through a simple native interface.

## Features

- 🔒 **Local-first privacy**
  - All application data is stored locally on your device.
  - No account required.
  - No telemetry or external data collection.

- 📋 **Application tracking**
  - Store job postings and company information.
  - Track application status and progress.

- 📄 **Application materials management**
  - Keep notes about submitted applications.
  - Store information about CVs, cover letters, and other materials.

- 🔎 **Fast organisation**
  - Search and manage applications easily.
  - Keep your job search history structured.

- 🌐 **Optional browser extension integration**
  - Collect job information directly from supported job websites.
  - Available for browsers such as Firefox and Chrome.

## Why JobVault Libre?

Job searching often involves keeping track of postings, deadlines, application materials, follow-ups, and outcomes. Many existing tools solve this by storing your information on external servers or requiring an online account (often with subscriptions). JobVault Libre takes a different approach. It offers a native desktop experience with no cloud component, no dependency on web services, and no requirement to share any personal information with third parties.

JobVault Libre aims to provide a structured, efficient, and private environment for managing every part of the job application process. The application allows you to record job details, track the status of each application, manage dates and actions, store notes, and document what you submitted. All data remains on your device and can be searched instantly.

JobVault Libre is intended for job seekers who value privacy, users who prefer offline desktop applications, and anyone who wishes to maintain their job-search information in a secure and transparent way.

## Screenshots


## Download

Pre-built versions are available from the project website:

https://jobvault-libre.mhevia.com/download

Currently available:

- Linux AppImage

## Installation

### Linux AppImage

Download the AppImage file and make it executable:

```bash
chmod +x JobVault_Libre-x86_64.AppImage
```

Run:

```bash
./JobVault_Libre-x86_64.AppImage
```

## Download and register as desktop application

```bash
sudo .\create_desktop.sh
```

### Running from source

Requirements:

* Python 3.11+

Clone the repository:

```bash
git clone https://github.com/<your-user>/JobVault-Libre.git
cd JobVault-Libre
```

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Run:

```bash
cd src
python -m myapp.app
```

### Building from source

Requirements:

* Python 3.11+
* linuxdeploy

Clone the repository:

```bash
git clone https://github.com/<your-user>/JobVault-Libre.git
cd JobVault-Libre
```

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

Build:

```bash
make linux
```

## Project Structure

```
.
├── src/
│   └── myapp/          # Application source code
├── docs/               # Project website
├── LICENSE
├── Makefile
├── README.md
└── requirements.txt
```

## Development Goals

JobVault Libre aims to provide:

* A reliable offline job tracking experience.
* A transparent and auditable alternative to cloud-based trackers.
* A lightweight application suitable for everyday use.
* Optional integrations that improve workflow without compromising privacy.

## Contributing

Contributions, bug reports, and suggestions are welcome.

Before contributing, please check existing issues and discuss major changes.

## Third-Party Components

This project includes **QToggle**, originally created by Luan Dias.

Repository:
[https://github.com/luandiasrj/QToggle_-_Advanced_QCheckbox_for_PyQT6](https://github.com/luandiasrj/QToggle_-_Advanced_QCheckbox_for_PyQT6)

Licensed under the GNU General Public License v3.

## License

JobVault Libre is released under the GNU General Public License v3.0.

See [LICENSE](LICENSE) for details.