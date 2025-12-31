================================================================================
                    READ THIS FIRST - EXACT STEPS
================================================================================

YOU MUST DO THESE STEPS IN ORDER:

STEP 1: START THE SERVER
-------------------------
Double-click: START_HERE.bat

A window will open. KEEP IT OPEN!

Wait until you see this message:
    * Running on http://0.0.0.0:5000

When you see that, the server is running!


STEP 2: OPEN YOUR BROWSER
---------------------------
While the server window is still open:

1. Open Chrome, Firefox, or Edge
2. Type EXACTLY in the address bar:
   
   http://127.0.0.1:5000
   
   (Make sure it says "http://" NOT "https://")

3. Press Enter


STEP 3: WHAT YOU SHOULD SEE
-----------------------------
✅ SUCCESS: You see a LOGIN PAGE
   → Server is working! You can now use the app.

❌ ERROR: "Cannot reach this page"
   → Go to TROUBLESHOOTING below


TROUBLESHOOTING
---------------

If you see "Cannot reach this page":

1. CHECK SERVER WINDOW
   - Is it still open?
   - Do you see "Running on http://0.0.0.0:5000"?
   - If NO → Server didn't start. Check for error messages.

2. CHECK THE URL
   - Must be: http://127.0.0.1:5000
   - NOT: https://127.0.0.1:5000 (no 's')
   - NOT: 127.0.0.1:5000 (missing http://)

3. TRY DIFFERENT BROWSER
   - Chrome not working? Try Firefox
   - Firefox: http://127.0.0.1:5000

4. TRY LOCALHOST
   - Instead of 127.0.0.1, try:
   - http://localhost:5000

5. CHECK WINDOWS FIREWALL
   - Press Win+R, type: wf.msc
   - Inbound Rules → New Rule
   - Port → TCP → 5000 → Allow → Finish


STILL NOT WORKING?
------------------

Share these details:

1. What do you see in the server window?
   (Take a screenshot or copy the text)

2. What error do you see in the browser?
   (Exact error message)

3. Did you see "Running on http://0.0.0.0:5000"?
   (Yes or No)

4. What URL did you type exactly?


QUICK TEST
----------
Double-click: SIMPLE_TEST.html
This will help test if server is accessible.


================================================================================
REMEMBER:
- Server window MUST stay open
- Use http:// not https://
- URL must be exactly: http://127.0.0.1:5000
- If server shows "Running on..." it IS working
================================================================================




