"""
Tests for NIST Data Loader
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nist_mcp.data.loader import NISTDataLoader


def async_open_mock(read_data: str):
    """Mock for ``aiofiles.open``.

    The stdlib sync helper builds a *sync* context manager, but aiofiles is used with
    ``async with``, so it raises TypeError. This returns a mock supporting the async
    context-manager protocol.
    """
    handle = AsyncMock()
    handle.read.return_value = read_data
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=handle)
    cm.__aexit__ = AsyncMock(return_value=False)
    return MagicMock(return_value=cm)



class TestNISTDataLoader:
    """Test cases for NISTDataLoader"""

    def test_loader_initialization(self):
        """Test loader initializes with data path"""
        data_path = Path("/test/data")
        loader = NISTDataLoader(data_path)
        assert loader.data_path == data_path

    @pytest.mark.asyncio
    async def test_initialize_missing_data_path(self):
        """Test initialization with missing data path"""
        data_path = Path("/nonexistent/path")
        loader = NISTDataLoader(data_path)

        with pytest.raises(FileNotFoundError):
            await loader.initialize()

    @pytest.mark.asyncio
    async def test_load_controls_from_json(self):
        """Test loading controls from JSON file"""
        data_path = Path("/test/data")
        loader = NISTDataLoader(data_path)

        sample_data = {
            "catalog": {"controls": [{"id": "AC-1", "title": "Access Control Policy"}]}
        }

        with (
            patch("aiofiles.open", async_open_mock(json.dumps(sample_data))),
            patch.object(Path, "exists", return_value=True),
        ):
            result = await loader.load_controls()
            assert result == sample_data
            assert loader._controls_cache == sample_data

    @pytest.mark.asyncio
    async def test_load_controls_cached(self):
        """Test loading controls returns cached data"""
        data_path = Path("/test/data")
        loader = NISTDataLoader(data_path)

        cached_data = {"catalog": {"controls": []}}
        loader._controls_cache = cached_data

        result = await loader.load_controls()
        assert result == cached_data

    def test_get_control_by_id_found(self):
        """Test finding control by ID"""
        loader = NISTDataLoader(Path("/test"))

        controls_data = {
            "catalog": {
                "groups": [
                    {
                        "id": "ac",
                        "title": "Access Control",
                        "controls": [
                            {"id": "AC-1", "title": "Access Control Policy"},
                            {
                                "id": "AC-2",
                                "title": "Account Management",
                                # Enhancements nest inside their base control in OSCAL
                                "controls": [
                                    {
                                        "id": "AC-2.1",
                                        "title": "Automated Account Management",
                                    }
                                ],
                            },
                        ],
                    }
                ]
            }
        }

        result = loader.get_control_by_id(controls_data, "AC-1")
        assert result["id"] == "AC-1"
        assert result["title"] == "Access Control Policy"

        # Enhancements must be findable too, not just group-level base controls
        enhancement = loader.get_control_by_id(controls_data, "AC-2.1")
        assert enhancement["title"] == "Automated Account Management"

    def test_get_control_by_id_not_found(self):
        """Test control not found by ID"""
        loader = NISTDataLoader(Path("/test"))

        controls_data = {"catalog": {"groups": []}}

        result = loader.get_control_by_id(controls_data, "AC-999")
        assert result is None

    def test_search_controls_by_keyword(self):
        """Test searching controls by keyword"""
        loader = NISTDataLoader(Path("/test"))

        controls_data = {
            "catalog": {
                "groups": [
                    {
                        "id": "ac",
                        "title": "Access Control",
                        "controls": [
                            {
                                "id": "AC-1",
                                "title": "Access Control Policy",
                                "parts": [
                                    {
                                        "prose": "The organization develops access control policies"
                                    }
                                ],
                            }
                        ],
                    },
                    {
                        "id": "au",
                        "title": "Audit and Accountability",
                        "controls": [
                            {
                                "id": "AU-1",
                                "title": "Audit Policy",
                                "parts": [
                                    {"prose": "The organization develops audit policies"}
                                ],
                            }
                        ],
                    },
                ]
            }
        }

        results = loader.search_controls_by_keyword(controls_data, "access", limit=10)
        assert len(results) == 1
        assert results[0]["id"] == "AC-1"

    def test_get_controls_by_family(self):
        """Test getting controls by family"""
        loader = NISTDataLoader(Path("/test"))

        controls_data = {
            "catalog": {
                "groups": [
                    {
                        "id": "ac",
                        "title": "Access Control",
                        "controls": [
                            {"id": "AC-1", "title": "Access Control Policy"},
                            {"id": "AC-2", "title": "Account Management"},
                        ],
                    },
                    {
                        "id": "au",
                        "title": "Audit and Accountability",
                        "controls": [{"id": "AU-1", "title": "Audit Policy"}],
                    },
                ]
            }
        }

        results = loader.get_controls_by_family(controls_data, "AC")
        assert len(results) == 2
        assert all(control["id"].startswith("AC") for control in results)
