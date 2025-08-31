1. PRD (Product Requirements Document) - For Your Internal Planning
Even though the client's request was clear, creating a mini-PRD helps you stay organized, ensure you've met all requirements, and have a reference point for what you promised. Think of it as your project blueprint.

Project Title: Amazon.de Automation Task Bot

Version: 1.0

Date: [Current Date]

Prepared By: [Your Name]

1. Project Goal:
Automate a defined workflow on Amazon.de to assist users with job applications, including browsing, wishlist management, and Prime cancellation. The primary objective is to create a reliable, repeatable, and well-documented Python script.

2. Core Functionality Requirements:

Authentication:
Ability to log into a dummy Amazon.de account using provided credentials (email/password).
Secure handling of credentials (not hardcoded directly, or clearly marked as sensitive).
Browser Automation (Playwright):
Headless mode off (visible browser for debugging/user observation).
Human-like behavior:
Realistic navigation delays.
Randomized scrolling actions.
Randomized pauses between interactions.
Proxy routing for all traffic.
Specific Actions:
Browse: Navigate to and interact with 5 distinct random product pages.
Wishlist: Add 2 distinct products to the wishlist.
Prime Cancellation: Detect and click the "End Membership" button on the Prime management page if active.
Logging:
Structured JSON log file (log.json).
Each entry must include: step (e.g., "Login", "Browse Product", "Add to Wishlist"), status ("info", "success", "error", "warning", "critical"), timestamp (ISO format), and optional details.
Error Handling:
Retry logic: If an action fails, retry once.
Failure management: If retries fail, capture a screenshot of the error state and reference its path in the log.
Deliverables:
main.py (The primary Python script).
requirements.txt (Lists all necessary Python packages).
README.md (Clear setup, installation, and execution instructions).
log.json (A sample of the structured log file).
screenshots/ (A folder to store error screenshots).
3. Technical Requirements:

Language: Python 3.11+
Libraries: Playwright (must be used, no Selenium), random, time, json, os, datetime.
Environment: Designed to run locally on a user's machine.
Proxy: Must use the provided proxy format for all browser interactions.
4. Constraints & Considerations:

Timebox: Maximum 5 hours for development.
Compensation: $100 USD upon delivery and review.
Future Potential: Successful pilot may lead to a 1-2 week pilot project and a full-time retainer.
2. Running It & Verification
Yes, you absolutely must test it.

How to Test Locally:
Set up your environment:
Install Python (if you haven't already).
Create a new folder for this project (e.g., amazon_automation).
Inside that folder, create the Python script (main.py), requirements.txt, and an empty folder called screenshots.
Create a package.json file (even though it's Python, npm install is sometimes used for playwright's browser binaries). Correction: For Python, you will use playwright install directly.
Create a virtual environment: python -m venv venv
Activate it: source venv/bin/activate (or venv\Scripts\activate on Windows).
Install dependencies: pip install -r requirements.txt
Install Playwright browsers: playwright install
Run the script: python main.py
Observe: Watch the browser window. Does it log in? Does it browse? Does it add to the wishlist? Does it find the Prime button? Check the log.json file for correctness.
Test Failure: To simulate an error, you could temporarily change a selector to something invalid, run the script, and check if it retries and takes a screenshot.
Is it Legit? The project description itself is quite clear. The use of dummy accounts, a proxy, and a paid test task is standard for this kind of work. The compensation is low, but it's a common entry point. The ethical question is about Amazon's ToS, which we'll address next.
3. Legality & Ethics
This is where we need to be careful.

Amazon's Terms of Service (ToS): Automating actions like this, especially repetitive actions like browsing and adding to wishlists, often violates Amazon's ToS. Repeated violations can lead to account bans for the user (the client).
Your Role: As a developer, you are building a tool. You are not directly violating Amazon's ToS by providing the tool. However, it is crucial to be aware that the client is using it in a way that could be against Amazon's rules.
Your Deliverables: You are providing a script, logs, and screenshots. You are not managing his account or running the bot on his behalf for his live Amazon account. This provides a layer of separation.
The "Why": The client's motivation is desperation due to manual job searching. While automation is a goal, automating activities on Amazon that mimic user behavior is often a red flag for platforms. However, for a dummy account, the immediate risk is lower. The main risk is if the client uses this to automate actions on his real account, which might get his account banned.
Your stance: You build the tool as requested, ensuring it functions correctly, handles errors, and is well-documented. You should not advise him on how to violate Amazon's ToS or run it on his live accounts. Stick to the technical delivery.

4. Verification
Code Quality: Ensure your Python code is clean, follows PEP 8 standards, is well-commented, and includes the requested logging and error handling.
Functionality: Run the script yourself (using the dummy credentials he provides) and verify that all steps (login, browse, wishlist, Prime cancel) work as described.
Deliverables:
Ensure main.py works.
Ensure requirements.txt is correct.
Ensure README.md is clear and accurate.
Run the script and capture a sample log.json file.
If you intentionally trigger an error during testing, ensure a screenshot is saved and referenced in the log.