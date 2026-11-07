"""Attach test classification and double usage to executed JUnit evidence."""
import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        module = item.path.stem
        if not any(item.get_closest_marker(m) for m in ("contract", "unit", "integration", "e2e")):
            marker = "integration" if module == "test_pdf_table_cells" else "unit"
            item.add_marker(getattr(pytest.mark, marker))
        category = next(m.upper() for m in ("contract", "unit", "integration", "e2e") if item.get_closest_marker(m))
        # This records deterministic doubles/monkeypatches as mocks even when
        # the rest of the pipeline uses real parsing or Chroma modules.
        names_with_doubles = {
            "test_block_text_stream_is_unchanged", "test_end_to_end_claim_binds_and_gate_returns_it",
            "test_jats_and_chroma_round_trip_and_connected_verification",
            "test_missing_full_text_is_distinct_from_failed_extraction",
            "test_project_collection_and_paper_replacement_are_isolated",
            "test_source_identity_change_is_a_failure_on_the_requested_paper",
            "test_five_query_baseline_preserves_executable_parameters",
            "test_real_bm25_fusion_preserves_identity_and_duplicate_prefixes",
            "test_embedding_owner_releases_before_llm_extraction", "test_failed_indexing_releases_owned_model",
            "test_raw_incomplete_model_response_is_observable",
        }
        mocked = module == "test_api" or (module == "test_clients_and_dispatch" and "dispatch" not in item.name)
        mocked = mocked or item.originalname in names_with_doubles
        mocked = mocked or "monkeypatch" in item.fixturenames
        item.user_properties.extend([("classification", category), ("mocks_or_doubles", str(bool(mocked)))])
