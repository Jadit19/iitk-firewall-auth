# IITK Firewall Authentication

While connected to the _IITK_ network or using the ethernet, it always asks for authentication by opening the [gateway portal](https://gateway.iitk.ac.in:1003/login?) and requiring one to enter his / her CC username and password.

This is a simple script you can run in the background or as a starter script to handle the authentication and keeping alive the connection in case you're using the ethernet to download huge files, make a local network or just want a lower lag while playing games.

## Steps

1. Connect the ethernet to your laptop.
2. Go to [hostel IP address](https://www.iitk.ac.in/cc/IP_Details/Hostel_IP_Address.html) to get the IP address of your room.
3. Enter the details into your wired connection.
4. Run this script in the background using:

   ```sh
   python3 authenticator.py
   ```
