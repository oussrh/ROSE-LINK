# ROSE Link Accessibility Guidelines

This document outlines the accessibility standards and practices implemented in ROSE Link to ensure the web interface is usable by all users, including those with disabilities.

## Standards Compliance

ROSE Link aims to conform to **WCAG 2.1 Level AA** guidelines. Key areas of compliance include:

- **Perceivable**: Content is presented in ways users can perceive
- **Operable**: Interface components are operable via keyboard and assistive technologies
- **Understandable**: Information and UI operation are understandable
- **Robust**: Content is compatible with assistive technologies

## Implemented Features

### Keyboard Navigation

All interactive elements are fully keyboard accessible:

| Key | Action |
|-----|--------|
| `Tab` | Navigate to next focusable element |
| `Shift+Tab` | Navigate to previous focusable element |
| `Enter/Space` | Activate buttons and links |
| `Arrow Keys` | Navigate within tab lists, menus |
| `Home/End` | Jump to first/last tab |
| `Escape` | Close modals and dialogs |

#### Skip Link
A "Skip to main content" link appears when pressing Tab, allowing keyboard users to bypass repetitive navigation.

### Screen Reader Support

- **ARIA Landmarks**: `<main>`, `<header>`, `<footer>`, `<nav>` for page structure
- **ARIA Live Regions**: Dynamic content changes are announced
- **ARIA Labels**: All interactive elements have accessible names
- **Role Attributes**: Correct roles for custom components (tabs, dialogs, alerts)

#### Tab Panel Implementation
```html
<nav role="tablist" aria-label="Main navigation">
  <button role="tab" aria-selected="true" aria-controls="content-wifi">WiFi</button>
  ...
</nav>
<section role="tabpanel" aria-labelledby="tab-wifi">...</section>
```

### Visual Accessibility

#### Color Contrast
- All text meets WCAG AA contrast requirements (4.5:1 for normal text, 3:1 for large text)
- Status indicators use both color AND text labels
- Focus indicators have 3:1 contrast against backgrounds

#### High Contrast Mode
CSS media queries support `prefers-contrast: more`:
- Increased border visibility
- Enhanced focus indicators
- System colors in forced-colors mode

#### Reduced Motion
Users who prefer reduced motion (`prefers-reduced-motion: reduce`):
- All animations are disabled
- Transitions are removed
- Status indicators remain visible without animation

### Forms and Inputs

- All inputs have associated `<label>` elements
- Required fields are marked with `aria-required="true"`
- Error messages use `role="alert"` for immediate announcement
- Form validation provides clear error descriptions

### Focus Management

- Visible focus indicators on all interactive elements
- Focus is trapped within modal dialogs
- Focus returns to trigger element when modals close
- Focus order follows logical reading order

## Development Guidelines

### Adding New Components

When adding new UI components, ensure:

1. **Keyboard Accessible**: Can be operated with keyboard alone
2. **Focus Visible**: Has visible focus indicator
3. **Labeled**: Has accessible name (label, aria-label, or aria-labelledby)
4. **Announced**: Dynamic changes are announced to screen readers

### Using the A11y Utilities

Import the accessibility utilities in your components:

```javascript
import { announce, announceLoading, trapFocus } from '../utils/a11y.js';

// Announce status changes
announce('WiFi scan complete. 5 networks found.');

// Announce loading states
announceLoading('WiFi networks');

// Trap focus in modal
const cleanup = trapFocus(modalElement);
// Later: cleanup(); to release
```

### Checklist for Pull Requests

Before submitting UI changes:

- [ ] All interactive elements are keyboard accessible
- [ ] Color is not the only means of conveying information
- [ ] Images have alt text (or `aria-hidden` if decorative)
- [ ] Form inputs have labels
- [ ] Error messages are associated with inputs
- [ ] Dynamic content changes are announced
- [ ] Focus is managed appropriately
- [ ] Components work with browser zoom (up to 200%)

## Testing

### Manual Testing

1. **Keyboard-only**: Navigate entire interface using only keyboard
2. **Screen Reader**: Test with NVDA (Windows), VoiceOver (Mac), or Orca (Linux)
3. **High Contrast**: Enable Windows High Contrast Mode
4. **Zoom**: Test at 200% browser zoom

### Automated Testing

The ESLint configuration includes accessibility rules. Run:

```bash
cd web
npm run lint
```

### Browser DevTools

- Chrome: Lighthouse Accessibility Audit
- Firefox: Accessibility Inspector
- Edge: Accessibility Tree Viewer

## Resources

- [WAI-ARIA Authoring Practices](https://www.w3.org/WAI/ARIA/apg/)
- [WCAG 2.1 Guidelines](https://www.w3.org/TR/WCAG21/)
- [MDN Accessibility Guide](https://developer.mozilla.org/en-US/docs/Web/Accessibility)

## Reporting Issues

If you encounter accessibility barriers, please:

1. Open an issue on GitHub with the "accessibility" label
2. Describe the barrier and how it affects your use
3. Include information about your assistive technology if applicable

We are committed to making ROSE Link accessible to all users.
