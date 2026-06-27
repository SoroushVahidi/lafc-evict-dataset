from lafc_evict_dataset.schema import BASE_REQUIRED_COLUMNS, CANONICAL_COLUMNS, FEATURE_COLUMNS


def test_schema_columns_exist() -> None:
    assert len(BASE_REQUIRED_COLUMNS) == 12
    assert len(FEATURE_COLUMNS) == 26
    assert len(CANONICAL_COLUMNS) == 38
    assert CANONICAL_COLUMNS[: len(BASE_REQUIRED_COLUMNS)] == BASE_REQUIRED_COLUMNS
