import sqlite3
import json

def fetch_patterns():
    db_path = "data/compliance.db"
    
    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Query the rules table
        query = """
            SELECT rule_title, category, severity, regex_patterns 
            FROM compliance_rules 
            WHERE is_active = 1
        """
        
        cursor.execute(query)
        rules = cursor.fetchall()
        
        if not rules:
            print("No active rules found in the database. (Did you upload a document?)")
            return

        print(f"--- Fetched {len(rules)} Active Rules ---")
        
        for idx, (title, category, severity, patterns_json) in enumerate(rules, start=1):
            print(f"\n{idx}. [{severity.upper()}] {title} (Category: {category})")
            
            # Parse the JSON array of regex patterns
            try:
                patterns = json.loads(patterns_json)
                for p_idx, pattern in enumerate(patterns, start=1):
                    print(f"   Regex {p_idx}: {pattern}")
            except json.JSONDecodeError:
                print(f"   [Error] Could not parse regex patterns: {patterns_json}")
                
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()

if __name__ == "__main__":
    fetch_patterns()
