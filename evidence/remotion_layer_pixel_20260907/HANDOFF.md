# Remotion Studio layer → pixel — handoff

Status: VERIFIED BRANCH CANDIDATE / NOT PROMOTED

Base PR #136: `8946f34ede9ab96a16f330d5a8304111dc668037`
Implementation: `7b6bb30817949e3e4f2b91a099e71247f7936d9c`
Merge Safe: `34158812435` SUCCESS; 709 passed / 1 skipped / 5 inherited warnings.

## New verified invariant

The Remotion runtime now consumes Studio layers. A TYPOGRAPHY layer's `data.text` is visible in the render, primary layer class/role/asset identity/edit cues are represented, and all layer classes/z-order are visible in the technical runtime surface.

The mandatory sensitivity gate changed only one Studio typography text, rendered a second MP4, restored runtimeSpec byte-for-byte, extracted the same absolute RGB frame and measured 191,614 changed bytes out of 691,200 (27.7219%). Baseline and variant raw-frame SHA256 values differ. This is direct technical evidence that Studio layer input causally changes pixels.

## Authority boundary

This is not creative qualification. AssetRef remains identity/context only; no provider/local media asset itself is rendered yet. Transition types survive into runtimeSpec but do not yet have a distinct transition animation contract.

## Next

1. provenance-bound local Asset media → staged Remotion-safe URL → pixel sensitivity proof, without arbitrary remote URL fetch;
2. transition type → distinct visual entry behavior → differential pixel proof.

Keep #48 OPEN, main untouched, #68 inactive.
