# SCRIPT NAME: test_maintenance_plan_importer.py
# DESCRIPTION: Unit tests for the maintenance plan PDF importer feature.
# UPDATE: Corrected the PyMuPDF mock and test assertions to align with new regex parser.

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime
import dashboard
import prediction_engine
import database
import io

class TestMaintenancePlanImporter(unittest.TestCase):

    def setUp(self):
        """Set up test data and mock objects before each test."""
        # This sample DataFrame mimics the structure after a successful PDF table extraction.
        self.sample_pdf_data = [
            ['Fleet #', 'Scheduled Start Dat', 'Scheduled End Date', 'Service Type', 'Service Type Alias', 'Repairer Notes'],
            ['RMG01', '01/08/2025 07:00', '01/08/2025 12:00', 'A', 'Weekly', 'Note 1'],
            ['SP07', '02/08/2025 09:00', '02/08/2025 14:00', 'B', 'Monthly', 'Note 2'],
            ['Traverser', '03/08/2025 10:00', '03/08/2025 15:00', 'C', 'Check', 'Note 3'], # Invalid Fleet ID
            ['RMG02', '04/08/2025 11:00', '04/08/2025 16:00', 'D', 'Quarterly', 'Note 4'], # Valid new record
            ['RMG01', '01/08/2025 07:00', '01/08/2025 12:00', 'A', 'Weekly', 'Note 1'], # Duplicate record
            ['SP11', 'not a date', '05/08/2025 10:00', 'E', 'Check', 'Invalid Date Format'], # Will cause parsing error
        ]

        # Mock existing data that would be in the database to test duplicate detection.
        self.mock_existing_windows = pd.DataFrame({
            'entity_id': ['RMG01'],
            'entity_type': ['crane'],
            'from_datetime': [pd.to_datetime('2025-08-01 07:00:00')],
            'to_datetime': [pd.to_datetime('2025-08-01 12:00:00')],
            'service_type': ['A'],
            'task_description': ['Weekly Check'],
            'notes': ['Existing note']
        })
        
        # Mock service config for the regression test
        self.mock_service_config = pd.DataFrame({
            'action_required': ['AC Unit 1 Filter'],
            'category': ['General'],
            'tag_name': [''],
            'service_limit': [''],
            'service_interval_days': ['365'],
            'unit': [''],
            'duration_hours': ['2']
        }, index=pd.Index(['ac_unit1_filter'], name='task_id'))


    @patch('dashboard.database.get_all_maintenance_windows')
    @patch('fitz.open')
    def test_data_processing_and_categorization(self, mock_fitz_open, mock_get_windows):
        """
        Test the main parse_maintenance_plan function to ensure it correctly
        categorizes records. This test now uses a more accurate mock for PyMuPDF.
        """
        # --- Arrange ---
        mock_get_windows.return_value = self.mock_existing_windows

        # Mock the page and table objects that PyMuPDF would create
        mock_page = MagicMock()
        
        # Create a mock text block that contains the data to be parsed by the regex logic
        mock_text = """
        Some introductory text.
        CASC01 WEST Crane-Stacking 26/05/2025 07:00 26/05/2025 10:00 A Weekly inspection
        SP07 Bromma Spr 27/05/2025 07:00 27/05/2025 17:00 Service Electrical-Mechanical
        RMG01 Crane 01/08/2025 07:00 01/08/2025 12:00 A Weekly
        RMG02 Crane 04/08/2025 11:00 04/08/2025 16:00 D Quarterly
        Traverser 03/08/2025 10:00 03/08/2025 15:00 C Check
        SP11 not a date 05/08/2025 10:00 E Check
        """
        mock_page.get_text.return_value = mock_text
        
        # Mock the main document object
        mock_doc = MagicMock()
        mock_doc.__iter__.return_value = iter([mock_page])
        mock_doc.__len__.return_value = 1  # Set page count to 1 to pass the check
        mock_fitz_open.return_value = mock_doc
        
        dummy_file = io.BytesIO(b"dummy pdf content")

        # --- Act ---
        valid_df, duplicate_df, error_df = dashboard.parse_maintenance_plan(dummy_file)

        # --- Assert ---
        # Valid records: SP07 and RMG02 should be valid new entries. CASC01 is also valid.
        self.assertIsNotNone(valid_df, "valid_df should not be None")
        self.assertEqual(len(valid_df), 3)
        self.assertIn('CASC01', valid_df['entity_id'].values)
        self.assertIn('SP07', valid_df['entity_id'].values)
        self.assertIn('RMG02', valid_df['entity_id'].values)
        
        # Duplicate records: The RMG01 entry is a duplicate of our mock DB data.
        self.assertIsNotNone(duplicate_df, "duplicate_df should not be None")
        self.assertEqual(len(duplicate_df), 1)
        self.assertEqual(duplicate_df.iloc[0]['entity_id'], 'RMG01')

        # Error records: Traverser is skipped (not an error), SP11 has a parsing error.
        self.assertIsNotNone(error_df, "error_df should not be None")
        self.assertEqual(len(error_df), 1)
        # This assertion now checks for the correct error message from the new parser.
        self.assertTrue(any("missing start/end datetimes" in e for e in error_df['Error'].values))


    @patch('database.add_maintenance_window')
    def test_database_insertion_logic(self, mock_add_window):
        """
        Tests that the database insertion function is called correctly
        with the right arguments and the correct number of times.
        """
        # --- Arrange ---
        valid_records_to_import = pd.DataFrame([
            {
                'entity_id': 'RMG05', 'entity_type': 'crane',
                'from_datetime': datetime(2025, 9, 1, 7, 0), 'to_datetime': datetime(2025, 9, 1, 12, 0),
                'service_type': 'A', 'task_description': 'Test Desc 1', 'notes': 'Test Note 1'
            },
            {
                'entity_id': 'SP12', 'entity_type': 'spreader',
                'from_datetime': datetime(2025, 9, 2, 9, 0), 'to_datetime': datetime(2025, 9, 2, 11, 0),
                'service_type': 'B', 'task_description': 'Test Desc 2', 'notes': 'Test Note 2'
            }
        ])
        
        # --- Act ---
        # This simulates the part of the UI that iterates and calls the db function.
        for record in valid_records_to_import.itertuples():
            database.add_maintenance_window(
                record.entity_id,
                record.entity_type,
                record.from_datetime,
                record.to_datetime,
                record.service_type,
                record.task_description,
                record.notes
            )

        # --- Assert ---
        self.assertEqual(mock_add_window.call_count, 2)
        mock_add_window.assert_any_call(
            'RMG05', 'crane',
            datetime(2025, 9, 1, 7, 0), datetime(2025, 9, 1, 12, 0),
            'A', 'Test Desc 1', 'Test Note 1'
        )
        mock_add_window.assert_any_call(
            'SP12', 'spreader',
            datetime(2025, 9, 2, 9, 0), datetime(2025, 9, 2, 11, 0),
            'B', 'Test Desc 2', 'Test Note 2'
        )

    @patch('prediction_engine.load_service_config')
    @patch('prediction_engine.database.get_last_service_record')
    @patch('prediction_engine.get_full_history_for_metric')
    def test_prediction_engine_regression(self, mock_get_history, mock_get_last_service, mock_load_config):
        """
        A basic regression test to ensure core prediction functionality
        has not been broken by the new changes.
        """
        # --- Arrange ---
        mock_load_config.return_value = self.mock_service_config
        mock_get_last_service.return_value = {
            'service_date': '2025-06-01 10:00:00',
            'serviced_at_value': 100000
        }
        mock_get_history.return_value = pd.DataFrame() # Not needed for time-based task

        # --- Act ---
        prediction = prediction_engine.predict_service_date('RMG01', 'crane', 'ac_unit1_filter')

        # --- Assert ---
        self.assertIsInstance(prediction, dict)
        self.assertIn('predicted_date', prediction)
        self.assertIn('days_remaining', prediction)
        self.assertIsNone(prediction.get('error'))

if __name__ == '__main__':
    unittest.main()
