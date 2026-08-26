from __future__ import annotations

from src.providers.contracts import ProviderPolicy


PROVIDER_POLICIES: dict[str, ProviderPolicy] = {
    'pinterest': ProviderPolicy(
        provider='pinterest',
        default_usage_class='reference_only',
        default_license_state='unknown',
        allow_as_final_asset_without_review=False,
        attribution_default=None,
        notes='Use for reference/mood/composition discovery by default; downstream rights must be verified separately.',
    ),
    'pexels': ProviderPolicy(
        provider='pexels',
        default_usage_class='commercial_candidate',
        default_license_state='needs_review',
        allow_as_final_asset_without_review=False,
        attribution_default=None,
        notes='Stock candidate; preserve source/license metadata and verify current terms before final commercial use.',
    ),
    'flaticon': ProviderPolicy(
        provider='flaticon',
        default_usage_class='commercial_candidate',
        default_license_state='needs_review',
        allow_as_final_asset_without_review=False,
        attribution_default=None,
        notes='Icon/vector discovery; license and attribution requirements vary by account/asset.',
    ),
    'swishy': ProviderPolicy(
        provider='swishy',
        default_usage_class='reference_only',
        default_license_state='unknown',
        allow_as_final_asset_without_review=False,
        attribution_default=None,
        notes='Treat as code/composition-pattern reference; do not blindly copy templates or assume redistribution rights.',
    ),
    'local': ProviderPolicy('local', 'owned', 'owned', True, False, 'Locally owned asset when provenance confirms ownership.'),
    'drive': ProviderPolicy('drive', 'owned', 'owned', True, False, 'Drive asset is only treated as owned when project provenance says so.'),
    'generated': ProviderPolicy('generated', 'generated', 'needs_review', False, None, 'Generated output still requires model/provider policy and source-input provenance.'),
    'web_other': ProviderPolicy('web_other', 'reference_only', 'unknown', False, None, 'Unknown web sources default to reference-only.'),
}


def policy_for_provider(provider: str) -> ProviderPolicy:
    try:
        return PROVIDER_POLICIES[provider]
    except KeyError:
        raise KeyError(f'unknown provider policy: {provider}') from None
