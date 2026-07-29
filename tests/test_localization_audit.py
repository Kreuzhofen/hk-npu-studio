from tools.audit_localization import audit, load_locales, placeholders


def test_all_locales_have_identical_keys_and_placeholders():
    locales = load_locales()
    reference = locales["de_DE"]

    for values in locales.values():
        assert set(values) == set(reference)
        for key, value in values.items():
            assert placeholders(value) == placeholders(reference[key])


def test_product_localization_audit_is_clean():
    assert audit() == []
