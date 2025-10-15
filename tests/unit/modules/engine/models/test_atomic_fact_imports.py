# ABOUTME: Tests for verifying AtomicFact model can be imported correctly from various paths
# ABOUTME: Ensures proper module structure and export visibility for other agents

import pytest


class TestAtomicFactImports:
    """Test suite for AtomicFact import paths."""

    def test_import_from_module_directly(self):
        """Test importing AtomicFact directly from its module."""
        from cognee.modules.engine.models.AtomicFact import (
            AtomicFact,
            FactType,
            TemporalType,
        )

        assert AtomicFact is not None
        assert FactType is not None
        assert TemporalType is not None

    def test_import_from_models_package(self):
        """Test importing AtomicFact from models package __init__.py."""
        from cognee.modules.engine.models import (
            AtomicFact,
            FactType,
            TemporalType,
        )

        assert AtomicFact is not None
        assert FactType is not None
        assert TemporalType is not None

    def test_enum_values_accessible(self):
        """Test that enum values are accessible after import."""
        from cognee.modules.engine.models import FactType, TemporalType

        # FactType values
        assert FactType.FACT == "FACT"
        assert FactType.OPINION == "OPINION"
        assert FactType.PREDICTION == "PREDICTION"

        # TemporalType values
        assert TemporalType.ATEMPORAL == "ATEMPORAL"
        assert TemporalType.STATIC == "STATIC"
        assert TemporalType.DYNAMIC == "DYNAMIC"

    def test_atomic_fact_is_datapoint_subclass(self):
        """Test that AtomicFact inherits from DataPoint."""
        from cognee.modules.engine.models import AtomicFact
        from cognee.infrastructure.engine import DataPoint

        assert issubclass(AtomicFact, DataPoint)

    def test_can_create_instance_from_package_import(self):
        """Test creating an AtomicFact instance using package-level import."""
        from uuid import uuid4
        from cognee.modules.engine.models import (
            AtomicFact,
            FactType,
            TemporalType,
        )

        fact = AtomicFact(
            subject="Test",
            predicate="is",
            object="importable",
            source_chunk_id=uuid4(),
            source_text="Test is importable.",
            fact_type=FactType.FACT,
            temporal_type=TemporalType.STATIC,
            confidence=0.95,
        )

        assert fact.subject == "Test"
        assert fact.fact_type == FactType.FACT
        assert fact.temporal_type == TemporalType.STATIC
