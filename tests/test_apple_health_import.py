import os
import sys
from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.services.extern.apple_health import AppleHealthImporter

# ruff: noqa: E501

# Add the application to the python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestAppleHealthImporter:
    """Tests for the AppleHealthImporter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_storage = MagicMock()
        self.importer = AppleHealthImporter(storage_service=self.mock_storage)
        self.user_id = "test_user"

        # Sample Apple Health XML data
        self.sample_xml = """
        <?xml version="1.0" encoding="UTF-8"?>
        <HealthData locale="en_US">
            <ExportDate value="2023-05-15 10:30:45 -0700"/>
            <Me HKCharacteristicTypeIdentifierDateOfBirth="1990-01-01" HKCharacteristicTypeIdentifierBiologicalSex="HKBiologicalSexMale"/>
            <Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="Sleep Cycle" sourceVersion="1" device="iPhone" unit="" value="HKCategoryValueSleepAnalysisAsleep" startDate="2023-05-01 23:30:45 -0700" endDate="2023-05-02 06:45:23 -0700"/>
            <Record type="HKCategoryTypeIdentifierSleepAnalysis" sourceName="Sleep Cycle" sourceVersion="1" device="iPhone" unit="" value="HKCategoryValueSleepAnalysisAsleep" startDate="2023-05-02 23:15:12 -0700" endDate="2023-05-03 07:05:45 -0700"/>
            <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Apple Watch" sourceVersion="1" device="AppleWatch" unit="count/min" value="62" startDate="2023-05-01 23:45:00 -0700" endDate="2023-05-01 23:45:00 -0700"/>
            <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Apple Watch" sourceVersion="1" device="AppleWatch" unit="count/min" value="58" startDate="2023-05-02 02:15:00 -0700" endDate="2023-05-02 02:15:00 -0700"/>
            <Record type="HKQuantityTypeIdentifierHeartRate" sourceName="Apple Watch" sourceVersion="1" device="AppleWatch" unit="count/min" value="60" startDate="2023-05-02 05:30:00 -0700" endDate="2023-05-02 05:30:00 -0700"/>
            <Record type="HKQuantityTypeIdentifierRespiratoryRate" sourceName="Apple Watch" sourceVersion="1" device="AppleWatch" unit="count/min" value="14" startDate="2023-05-02 01:00:00 -0700" endDate="2023-05-02 01:00:00 -0700"/>
            <Record type="HKQuantityTypeIdentifierEnvironmentalAudioExposure" sourceName="Apple Watch" sourceVersion="1" device="AppleWatch" unit="dBASPL" value="35.5" startDate="2023-05-02 00:30:00 -0700" endDate="2023-05-02 00:30:00 -0700"/>
        </HealthData>
        """

    def test_import_from_xml(self):
        """Test importing sleep data from Apple Health XML."""
        result = self.importer.import_from_xml(self.user_id, self.sample_xml)

        # Verify basic result structure
        assert "user_id" in result
        assert result["user_id"] == self.user_id
        assert "records_imported" in result
        assert result["records_imported"] > 0
        assert "heart_rate_data_points" in result
        assert result["heart_rate_data_points"] > 0

        # Verify storage was called
        self.mock_storage.save_sleep_records.assert_called_once()

    def test_extract_sleep_records(self):
        """Test extracting sleep records from XML."""
        import xml.etree.ElementTree as ET

        root = ET.fromstring(self.sample_xml)

        sleep_records = self.importer._extract_sleep_records(root, self.user_id)

        assert len(sleep_records) == 2  # Two sleep records in the sample data

        # Check first record
        record = sleep_records[0]
        assert record["user_id"] == self.user_id
        assert "date" in record
        assert "sleep_start" in record
        assert "sleep_end" in record
        assert "duration_minutes" in record
        assert "sleep_phases" in record
        assert "time_series" in record
        assert "metadata" in record

        # Verify metadata
        assert record["metadata"]["source"] == "apple_health"
        assert "imported_at" in record["metadata"]
        assert "Sleep Cycle" in record["metadata"]["source_name"]

    def test_extract_heart_rate_data(self):
        """Test extracting heart rate data from XML."""
        import xml.etree.ElementTree as ET

        root = ET.fromstring(self.sample_xml)

        heart_rate_data = self.importer._extract_heart_rate_data(root)

        assert len(heart_rate_data) == 3  # Three heart rate records in sample

        # Check structure
        hr_record = heart_rate_data[0]
        assert "timestamp" in hr_record
        assert "value" in hr_record
        assert "source" in hr_record
        assert hr_record["source"] == "Apple Watch"

    def test_enhance_with_heart_rate(self):
        """Test enhancing sleep records with heart rate data."""
        sleep_records = [
            {
                "sleep_start": "2023-05-01T23:30:45-07:00",
                "sleep_end": "2023-05-02T06:45:23-07:00",
                "time_series": [
                    {"timestamp": "2023-05-02T00:00:00-07:00"},
                    {"timestamp": "2023-05-02T03:00:00-07:00"},
                ],
            }
        ]

        heart_rate_data = [
            {
                "timestamp": datetime.fromisoformat("2023-05-02T00:05:00-07:00"),
                "value": 60,
                "source": "Test",
            },
            {
                "timestamp": datetime.fromisoformat("2023-05-02T03:05:00-07:00"),
                "value": 55,
                "source": "Test",
            },
        ]

        self.importer._enhance_with_heart_rate(sleep_records, heart_rate_data)

        # Verify heart rate data was added
        assert "heart_rate" in sleep_records[0]
        assert "average" in sleep_records[0]["heart_rate"]
        assert sleep_records[0]["heart_rate"]["average"] == 57.5  # Average of 60 and 55

        # Verify time series was enhanced
        assert sleep_records[0]["time_series"][0]["heart_rate"] is not None
        assert sleep_records[0]["time_series"][1]["heart_rate"] is not None

    def test_import_with_invalid_xml(self):
        """Test handling of invalid XML."""
        with pytest.raises(Exception):
            self.importer.import_from_xml(self.user_id, "<invalid>xml</not-closed>")
