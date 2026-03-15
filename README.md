# Smart AI Complaint Management

An AI-powered complaint management system that features automatic category classification, priority assignment, and duplicate detection using NLP.

## Prerequisites

- Python 3.8 or higher
- `pip` (Python package installer)

## Setup and Running

1. **Navigate to the Project Directory**:
   Open your terminal/command prompt and `cd` into the project folder.

2. **Set up Virtual Environment**:
   If the `venv` folder already exists, activate it:
   - **Windows**:
     ```bash
     .\venv\Scripts\activate
     ```
   - **Linux/Mac**:
     ```bash
     source venv/bin/activate
     ```
   *If it doesn't exist, create it first with `python -m venv venv` and then activate it.*

3. **Install Dependencies**:
   Install the required libraries using the provided `requirements.txt`:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   Start the Flask server:
   ```bash
   python app.py
   ```

5. **Access the App**:
   Once the server is running, open your web browser and go to:
   [http://localhost:5000](http://localhost:5000)

## Default User Accounts

The system is pre-seeded with the following accounts for testing:

- **Admin**: `admin@gmail.com` / `admin123`
- **Water Officer**: `officer_water@gmail.com` / `officer123`
- **Road Officer**: `officer_road@gmail.com` / `officer123`
- **Sanitation Officer**: `officer_sanitation@gmail.com` / `officer123`
- **Electricity Officer**: `officer_electricity@gmail.com` / `officer123`
- **General Officer**: `officer_other@gmail.com` / `officer123`
