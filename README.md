# summer_drone
A socket-based simulation of a drone authorization system using identity-based encryption (IBE).

How to Run the Project

Requirements:
Python 3
SageMath (used for elliptic curve operations)


Step 1: Start each service in its own terminal
Key Generation Authority (KGA)

bash
Copy
Edit
sage -python kga_server.py
DRP Manager (Drone Reputation Profile)

bash
Copy
Edit
python3 drp_manager.py
SAM (Safety Authorization Manager)

bash
Copy
Edit
sage -python sam.py
Each should print a message like:
Listening on 127.0.0.1:<port>

Step 2: Run the Drone
In a new terminal:

bash
Copy
Edit
sage -python drone.py
You should see output showing:
The drone requesting flight permission
SAM's decision (approval, conditional, or denial)
A mission exit log
