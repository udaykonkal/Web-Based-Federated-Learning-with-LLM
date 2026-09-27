import os
import shutil
import sqlite3

DB_PATH = "backend/fl_healthcare.db"
DATA_EXP_DIR = "data/experiments"

def clean_experiments():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all experiments
    cursor.execute("SELECT id, name, created_at FROM experiments ORDER BY id DESC")
    all_exps = cursor.fetchall()
    print(f"Total experiments before cleanup: {len(all_exps)}")

    # We want to preserve:
    # 1. Any experiment named 'MVJ'
    # 2. Any experiment named 'viva demonstration trial'
    # 3. Exactly ONE latest 'Benchmark Diabetes FedAvg Experiment'
    # 4. Exactly ONE latest 'Cardiology FedAvg Trial'
    # 5. Exactly ONE latest 'Final Major Project E2E Verification Trial' or 'Live Browser Verification FL Experiment'
    
    keep_ids = set()
    kept_diabetes = False
    kept_cardio = False
    kept_verification = False

    for exp_id, name, created_at in all_exps:
        clean_name = name.strip()
        if "MVJ" in clean_name:
            keep_ids.add(exp_id)
            print(f"Keeping user experiment: ID {exp_id} - '{clean_name}'")
        elif "viva demonstration" in clean_name.lower():
            keep_ids.add(exp_id)
            print(f"Keeping user experiment: ID {exp_id} - '{clean_name}'")
        elif "benchmark diabetes" in clean_name.lower() and not kept_diabetes:
            keep_ids.add(exp_id)
            kept_diabetes = True
            print(f"Keeping latest benchmark diabetes run: ID {exp_id} - '{clean_name}'")
        elif "cardiology" in clean_name.lower() and not kept_cardio:
            keep_ids.add(exp_id)
            kept_cardio = True
            print(f"Keeping latest cardiology run: ID {exp_id} - '{clean_name}'")
        elif ("e2e" in clean_name.lower() or "live browser" in clean_name.lower()) and not kept_verification:
            keep_ids.add(exp_id)
            kept_verification = True
            print(f"Keeping latest verification run: ID {exp_id} - '{clean_name}'")

    ids_to_delete = [exp_id for exp_id, _, _ in all_exps if exp_id not in keep_ids]
    print(f"\nIdentified {len(ids_to_delete)} experiments to remove. Preserving {len(keep_ids)} experiments.")

    # Foreign key deletion
    for exp_id in ids_to_delete:
        # 1. Get round IDs
        cursor.execute("SELECT id FROM fl_rounds WHERE experiment_id = ?", (exp_id,))
        round_ids = [r[0] for r in cursor.fetchall()]

        if round_ids:
            placeholders = ",".join("?" for _ in round_ids)
            cursor.execute(f"DELETE FROM model_updates WHERE round_id IN ({placeholders})", round_ids)
            cursor.execute(f"DELETE FROM client_participations WHERE round_id IN ({placeholders})", round_ids)
        
        cursor.execute("DELETE FROM security_events WHERE experiment_id = ?", (exp_id,))
        cursor.execute("DELETE FROM llm_recommendations WHERE experiment_id = ?", (exp_id,))
        cursor.execute("DELETE FROM fl_rounds WHERE experiment_id = ?", (exp_id,))
        cursor.execute("DELETE FROM experiments WHERE id = ?", (exp_id,))

        # Remove disk directory
        exp_dir = os.path.join(DATA_EXP_DIR, f"exp_{exp_id}")
        if os.path.exists(exp_dir):
            try:
                shutil.rmtree(exp_dir)
            except Exception as e:
                print(f"Warning deleting directory {exp_dir}: {e}")

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM experiments")
    remaining_count = cursor.fetchone()[0]
    print(f"\nCleanup complete! Remaining experiments: {remaining_count}")

    cursor.execute("SELECT id, name, status, current_round, total_rounds FROM experiments ORDER BY id ASC")
    for row in cursor.fetchall():
        print(f"  [ID {row[0]}] {row[1]} | Status: {row[2]} | Round {row[3]}/{row[4]}")

    conn.close()

if __name__ == "__main__":
    clean_experiments()
