# Network Monitoring System

A full-stack web application for monitoring network health, including ping tests, bandwidth simulation, uptime checks, and local device discovery. Built with **Python, Flask, SQLite, HTML, CSS, and JavaScript**.

---

## Features

- **User Authentication**  
  Secure login and registration with password hashing.

- **Dashboard Overview**  
  View public IP, local IP, bandwidth usage, and connected devices.

- **Ping Test**  
  Test latency and packet loss to any domain or IP address.

- **Uptime Monitoring**  
  Check if websites are online or offline in real time.

- **Bandwidth Simulation**  
  Simulates download/upload speeds (updates every 2 seconds).

- **Local Network Device Discovery**  
  Scans your network and lists connected devices (IP + MAC).

- **Historical Logs**  
  Stores and displays past ping and uptime results.

- **Admin Panel**  
  Manage user accounts (only accessible by admin).

- **Help & Documentation**  
  Includes FAQs and troubleshooting tips.

- **Responsive Design**  
  Works on desktop, tablet, and mobile devices.


## Technologies Used

| Layer                         | Technology 


| **Frontend**                  |HTML, CSS, JavaScript 
| **Backend**                   | Python 3.11+ (Flask) 
| **Database**                  | SQLite 
| **Networking**                | `scapy`, `netifaces`, `requests`, system `ping` 
| **Security**                  | `bcrypt` (password hashing) 


## Project Structure


network-monitor/
│
├── app.py                    # Flask backend server
├── database/
│   └── network_monitor.db    # SQLite database 
├── static/
│   ├── css/style.css         #styling
    ├── dashboard.css         #Styling
│   └── js/main.js            # Client-side logic
├── templates/                # HTML templates
│   ├── login.html
│   ├── dashboard.html
│   ├── help.html
│   └── admin.html
├── requirements.txt          # Python dependencies
└── README.md                 # This file


##  Install Dependencies
pip install -r requirements.txt
# OR
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# IF HAVING CHALLENGES GO TO BROWSER AND INSTALL
netifaces-0.11.0-cp313-cp313-win_amd64.whl
# THEN IN TERMINAL 
pip install "C:\Users\Algo-Tech Systems\Downloads\netifaces-0.11.0-cp313-cp313-win_amd64.whl" ## replace with your path

# THEN RUN
pip install requests apscheduler scapy -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# Install Npcap (For Device Discovery)
Scapy needs Npcap to scan devices.

Download: https://npcap.com
Run installer
Check: "Install Npcap in WinPcap API-compatible Mode"


### RUN THE APP
python app.py

* Running on http://127.0.0.1:5000

### Open your browser and go to:
 http://localhost:5000

## Default Login
USERNAME                             PASSWORD

mutero                                mutero1234

