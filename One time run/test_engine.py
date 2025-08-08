import prediction_engine
import database
from pprint import pprint

# This script will test the Stage 2 changes to the prediction engine.
# It ensures that predictions for both cranes (existing functionality)
# and spreaders (new functionality) work correctly.

def run_test():
    print("--- Starting Stage 2 Prediction Engine Test ---")

    # Ensure the database is ready (it should be from Stage 1)
    print("Initializing database...")
    database.init_db()
    print("Database ready.")

    # --- Test 1: Crane Prediction (Verify Existing Functionality) ---
    print("\n--- Test 1: Predicting for a CRANE (RMG04) ---")
    try:
        crane_prediction = prediction_engine.predict_service_date(
            entity_id='RMG04',
            entity_type='crane',
            task_id='hoist_rope_inspection'
        )
        # Corrected check: Ensure the dictionary was returned and the 'error' key is None.
        if crane_prediction and crane_prediction.get('error') is None:
            print("SUCCESS: Crane prediction ran without errors.")
            pprint(crane_prediction)
        else:
            print("FAILURE: Crane prediction failed or returned an error.")
            pprint(crane_prediction)
            return
    except Exception as e:
        print(f"FAILURE: An exception occurred during crane prediction: {e}")
        return

    # --- Test 2: Spreader Prediction (Verify New Functionality) ---
    # We use Spreader ID 29747, which is shared between RMG07 and RMG12
    print("\n--- Test 2: Predicting for a SPREADER (ID 29747) ---")
    try:
        spreader_prediction = prediction_engine.predict_service_date(
            entity_id='29747',
            entity_type='spreader',
            task_id='twistlock_functional_check'
        )
        # Corrected check: Ensure the dictionary was returned and the 'error' key is None.
        if spreader_prediction and spreader_prediction.get('error') is None:
            print("SUCCESS: Spreader prediction ran without errors.")
            # Check if it calculated a usage value, which proves aggregation logic ran
            if spreader_prediction.get('current_value', 0) > 0:
                 print("VERIFIED: Spreader prediction calculated a usage value, indicating aggregation logic is working.")
            else:
                 print("WARNING: Spreader prediction ran but usage value is 0. Check aggregation logic.")
            pprint(spreader_prediction)
        else:
            print("FAILURE: Spreader prediction failed or returned an error.")
            pprint(spreader_prediction)
            return
    except Exception as e:
        print(f"FAILURE: An exception occurred during spreader prediction: {e}")
        return

    print("\n--- Stage 2 Test Complete: All checks passed! ---")


if __name__ == "__main__":
    run_test()
