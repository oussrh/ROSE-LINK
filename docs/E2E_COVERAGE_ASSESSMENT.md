# ROSE-LINK E2E Test Coverage Assessment

## Executive Summary

This document provides a comprehensive assessment of the existing E2E test coverage for ROSE-LINK, identifies gaps, and outlines quality considerations and recommendations for improvement.

**Assessment Date:** November 2025
**Test Framework:** Playwright 1.40.0
**Total E2E Test Lines:** ~2,885 lines across 9 test files

---

## Current Coverage Overview

### Test Suites

| Suite | File | Lines | Purpose |
|-------|------|-------|---------|
| Navigation | `navigation.spec.js` | 196 | Top-level navigation, keyboard controls, tabs |
| WiFi | `wifi.spec.js` | 164 | WiFi scanning, network display |
| VPN | `vpn.spec.js` | 146 | VPN profiles, status display |
| Hotspot | `hotspot.spec.js` | 219 | Hotspot form interactions |
| System | `system.spec.js` | 377 | System info, VPN settings |
| Workflows | `workflows.spec.js` | 491 | User journeys across features |
| Error Handling | `error-handling.spec.js` | 439 | Error conditions, edge cases |
| Real-time | `realtime.spec.js` | 437 | WebSocket, HTMX updates |
| Grafana | `grafana.spec.js` | 416 | Dashboard panel visibility |

### What Is Currently Tested

#### Navigation & UI
- ✅ Page loading and splash screen
- ✅ Tab switching (WiFi/VPN/Hotspot/System)
- ✅ Keyboard navigation (arrow keys)
- ✅ Language toggle (English/French)
- ✅ Responsive viewports (desktop, tablet, mobile)
- ✅ Accessibility roles (ARIA attributes)

#### Workflows
- ✅ WiFi scan triggering
- ✅ VPN profile list display
- ✅ Hotspot form interactions (fill, select, toggle)
- ✅ VPN settings submission
- ✅ Setup wizard dialog opening
- ✅ Language persistence across reload
- ✅ Status cards visibility

#### Error Handling
- ✅ API timeout simulation
- ✅ HTTP 500/404/503 error responses
- ✅ Offline mode detection
- ✅ Empty state handling (no networks, no profiles)
- ✅ Form validation edge cases (SSID length, password length)
- ✅ XSS payload handling in inputs

#### Grafana
- ✅ Dashboard loading
- ✅ Panel visibility (VPN, WAN, Hotspot, CPU, Memory, etc.)
- ✅ Time range picker interaction
- ✅ Responsive design
- ✅ Health endpoint check

---

## Gap Analysis

### 1. Shallow Assertion Depth

**Issue:** Assertions primarily verify element visibility without confirming side effects or data integrity.

**Examples:**
```javascript
// Current: Only checks visibility
await expect(messageArea).toBeVisible();

// Missing: Verify actual content/success message
await expect(messageArea).toContainText('Configuration saved');
```

**Affected Areas:**
- Form submissions don't verify success/error messages
- API calls don't assert request payloads
- Status updates don't confirm data accuracy

### 2. Timing-Based Synchronization

**Issue:** Heavy reliance on `waitForTimeout()` instead of proper state synchronization.

**Current Pattern:**
```javascript
await page.waitForTimeout(1000);  // Arbitrary delay
await expect(networks).toBeVisible();
```

**Better Pattern:**
```javascript
await page.waitForResponse('**/api/wifi/scan');  // Wait for actual response
await expect(networks).toHaveText(/TestNetwork/);  // Assert content
```

**Locations with waitForTimeout:**
- `workflows.spec.js`: Lines 41, 242, 284, 337, 358
- `error-handling.spec.js`: Lines 55, 68, 72, 265, 312, 414, 433
- `test-helpers.js`: Line 31 (setLanguage)

### 3. Missing User Notification Assertions

**Issue:** Error handling tests ensure the page renders but don't verify user-facing messages.

**Gap Examples:**
| Scenario | Current Test | Missing Assertion |
|----------|--------------|-------------------|
| API 500 error | Page visible | Toast shows "Server error" |
| Network offline | Header visible | Offline indicator appears |
| Form validation | Fields unchanged | Error message displayed |
| Timeout | Status cards visible | Retry mechanism triggered |

### 4. No Authentication/Authorization Coverage

**Missing Tests:**
- No login flow tests (if applicable)
- No session expiration handling
- No role-based access verification
- Grafana anonymous access assumed without validation

### 5. No Real Device Connectivity Tests

**Missing Tests:**
- WiFi actual connection establishment
- VPN tunnel bring-up verification
- Hotspot client join detection
- Network interface state changes

### 6. Limited Session Persistence Testing

**Current:** Only language persistence is tested.

**Missing:**
- Tab selection persistence
- Form draft preservation
- User preferences across sessions
- WebSocket reconnection after disconnect

### 7. Grafana Coverage Gaps

**Missing Tests:**
| Area | Gap |
|------|-----|
| Alerting | No alert rule trigger tests |
| Data freshness | No staleness detection |
| Cross-panel correlation | No data consistency checks |
| Role-based views | Anonymous access only |
| Variable filtering | Template variable tests missing |
| Data validation | Panel data not verified, only visibility |

### 8. Request Payload Validation

**Issue:** Mocks fulfill responses without asserting request correctness.

**Current:**
```javascript
await page.route('**/api/hotspot/config', (route) => {
    route.fulfill({ status: 200, body: JSON.stringify({ status: 'success' }) });
});
```

**Missing:**
```javascript
// Assert the request payload is correct
const postData = JSON.parse(route.request().postData());
expect(postData.ssid).toBe('TestSSID');
expect(postData.password).toHaveLength(8);
```

---

## Quality Risk Matrix

| Risk Area | Severity | Likelihood | Impact |
|-----------|----------|------------|--------|
| Flaky tests (timing) | High | High | CI failures, developer frustration |
| Undetected regressions | High | Medium | Production bugs |
| Missing error UX | Medium | High | Poor user experience |
| No persistence tests | Medium | Medium | State loss bugs |
| Shallow validation | Medium | High | False confidence |

---

## Recommendations

### Immediate (High Priority)

1. **Replace waitForTimeout with network synchronization**
   ```javascript
   const responsePromise = page.waitForResponse('**/api/wifi/scan');
   await scanBtn.click();
   await responsePromise;
   ```

2. **Add toast/notification assertions**
   ```javascript
   await expect(page.locator('[role="alert"]')).toContainText('Success');
   ```

3. **Validate request payloads in mocks**
   ```javascript
   await page.route('**/api/hotspot/config', (route) => {
       const body = JSON.parse(route.request().postData());
       expect(body).toHaveProperty('ssid');
       route.fulfill({ ... });
   });
   ```

### Short-Term (Medium Priority)

4. **Add session persistence tests**
   - Tab state across reload
   - WebSocket reconnection
   - Form draft recovery

5. **Enhance error message assertions**
   - Verify specific error messages
   - Test retry mechanisms
   - Check offline indicators

6. **Improve Grafana data validation**
   - Assert panel data format
   - Test alert state queries
   - Verify time range filtering

### Long-Term (Lower Priority)

7. **Add integration tests for device connectivity**
   - Mock system calls for WiFi/VPN
   - Test status polling accuracy

8. **Authentication flow coverage**
   - Session management
   - Token refresh handling

---

## Test Quality Metrics

### Current Metrics

| Metric | Value | Target |
|--------|-------|--------|
| E2E test files | 9 | - |
| Total test cases | ~80 | - |
| waitForTimeout usage | 15+ | 0 |
| Toast assertions | 0 | 100% of error paths |
| Request payload validations | 0 | 100% of form submissions |
| Session persistence tests | 1 | 5+ |

### Recommended Thresholds

- **Assertion depth:** Each test should have ≥2 meaningful assertions
- **Network sync:** No arbitrary timeouts; use response/state waits
- **Error coverage:** Every error mock should verify user notification
- **Payload validation:** Every form submission should verify request data

---

## Implementation Checklist

### Phase 1: Stabilization
- [ ] Replace all `waitForTimeout` with proper waits
- [ ] Add `expectToast` assertions to error handling tests
- [ ] Validate request payloads in workflow tests

### Phase 2: Coverage Expansion
- [ ] Add session persistence test suite
- [ ] Enhance Grafana data validation
- [ ] Add offline indicator tests

### Phase 3: Quality Hardening
- [ ] Add retry mechanism tests
- [ ] Test concurrent operation handling
- [ ] Add cross-browser consistency checks

---

## Appendix: Test Helper Improvements

### Recommended New Helpers

```javascript
/**
 * Wait for API response and validate payload
 */
async function expectApiCall(page, url, expectedPayload, response) {
    let receivedPayload;
    await page.route(url, (route) => {
        receivedPayload = JSON.parse(route.request().postData() || '{}');
        route.fulfill(response);
    });
    // After action...
    expect(receivedPayload).toMatchObject(expectedPayload);
}

/**
 * Wait for specific network state
 */
async function waitForNetworkIdle(page, timeout = 5000) {
    await page.waitForLoadState('networkidle', { timeout });
}

/**
 * Assert offline indicator visibility
 */
async function expectOfflineIndicator(page, visible = true) {
    const indicator = page.locator('[data-testid="offline-indicator"], .offline-badge');
    if (visible) {
        await expect(indicator).toBeVisible();
    } else {
        await expect(indicator).not.toBeVisible();
    }
}
```

---

*This assessment should be reviewed quarterly as the application evolves.*
