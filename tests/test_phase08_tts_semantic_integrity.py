from src.content.tts_integrity import extract_protected_tokens, tts_integrity_errors


def test_same_digits_cannot_cross_percentage_into_currency():
    errors = tts_integrity_errors("Mejora un 10%.", "Mejora 10 euros.")
    assert any("PERCENT" in error for error in errors)


def test_percentage_accepts_equivalent_spoken_spanish_form():
    assert tts_integrity_errors("Mejora un 10%.", "Mejora un diez por ciento.") == []
    assert tts_integrity_errors("Mejora un 10%.", "Mejora un 10 por ciento.") == []


def test_currency_value_and_family_are_both_protected():
    assert tts_integrity_errors("Cuesta $10.", "Cuesta 10 dólares.") == []
    assert tts_integrity_errors("Cuesta €10.", "Cuesta diez euros.") == []
    errors = tts_integrity_errors("Cuesta $10.", "Cuesta 10 euros.")
    assert any("CURRENCY" in error for error in errors)


def test_currency_digits_elsewhere_do_not_satisfy_currency_contract():
    errors = tts_integrity_errors("Cuesta $10.", "La versión 10 ya está lista.")
    assert any("CURRENCY" in error for error in errors)


def test_grouped_currency_cannot_collapse_to_prefix_value():
    assert tts_integrity_errors("Cuesta $1,000.", "Cuesta $1,000.") == []
    assert any("CURRENCY" in error for error in tts_integrity_errors("Cuesta $1,000.", "Cuesta $1."))
    assert any("CURRENCY" in error for error in tts_integrity_errors("Cuesta €1.000.", "Cuesta €1."))


def test_ambiguous_currency_separator_is_not_silently_reinterpreted():
    # Until a locale-aware policy is explicitly qualified, these spellings are
    # intentionally distinct rather than guessed to be equivalent.
    errors = tts_integrity_errors("Cuesta $1,000.", "Cuesta $1.000.")
    assert any("CURRENCY" in error for error in errors)


def test_decimal_preserves_decimal_value_not_digit_concatenation():
    assert tts_integrity_errors("La ratio es 1.5.", "La ratio es 1,5.") == []
    errors = tts_integrity_errors("La ratio es 1.5.", "La ratio es 15.")
    assert any("DECIMAL" in error for error in errors)


def test_prose_decimal_is_not_misclassified_as_version():
    tokens = extract_protected_tokens("La ratio es 1.5.")
    assert [(token.kind, token.original) for token in tokens] == [("DECIMAL", "1.5")]
    assert [(token.kind, token.original) for token in extract_protected_tokens("Usa versión 2.1.")] == [("VERSION", "versión 2.1")]


def test_decimal_cannot_be_satisfied_by_currency_with_same_value():
    errors = tts_integrity_errors("La ratio es 1.5.", "Cuesta 1.5 EUR.")
    assert any("DECIMAL" in error for error in errors)


def test_year_preserves_semantic_token_not_shared_digits_in_currency():
    assert tts_integrity_errors("Llegará en 2026.", "Llegará en 2026.") == []
    errors = tts_integrity_errors("Llegará en 2026.", "Costará 2026 EUR.")
    assert any("DATE_OR_YEAR" in error for error in errors)


def test_version_preserves_label_and_components_not_flat_digits():
    assert tts_integrity_errors("Usa Motion 2.1.", "Usa Motion 2.1.") == []
    assert tts_integrity_errors("Usa versión 2.1.", "Usa versión 2.1.") == []
    errors = tts_integrity_errors("Usa Motion 2.1.", "Usa Motion 21.")
    assert any("VERSION" in error for error in errors)
    errors = tts_integrity_errors("Usa Motion 2.1.", "Usa Other 2.1.")
    assert any("VERSION" in error for error in errors)


def test_existing_changed_year_and_percentage_regression_remains_blocked():
    errors = tts_integrity_errors("Llegará en 2029 y mejora un 18%.", "Llegará en 2019 y mejora un 8%.")
    assert len(errors) >= 2


def test_extra_protected_proper_tokens_require_word_boundaries():
    assert tts_integrity_errors("Hola", "OpenAI crea", extra_protected=["OpenAI"]) == []
    errors = tts_integrity_errors("Hola", "OpenAIX crea", extra_protected=["OpenAI"])
    assert any("proper token" in error for error in errors)


def test_overlap_classification_prefers_more_specific_currency_percent_and_version():
    tokens = extract_protected_tokens("10% $10 Motion 2.1 1.5 2026")
    kinds = [token.kind for token in tokens]
    assert kinds == ["PERCENT", "CURRENCY", "VERSION", "DECIMAL", "DATE_OR_YEAR"]
