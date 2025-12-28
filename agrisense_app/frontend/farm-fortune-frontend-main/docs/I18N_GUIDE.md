# Multi-Language Support (i18n) Documentation

## Overview

AgriSense frontend now supports **5 languages**:
- 🇬🇧 English (en)
- 🇮🇳 हिन्दी Hindi (hi)
- 🇮🇳 தமிழ் Tamil (ta)
- 🇮🇳 తెలుగు Telugu (te)
- 🇮🇳 ಕನ್ನಡ Kannada (kn)

The system uses **react-i18next** and **i18next** for internationalization, providing automatic language detection, persistence, and easy switching.

## Features

✅ **Automatic Language Detection** - Detects user's browser language  
✅ **Local Storage Persistence** - Remembers user's language preference  
✅ **Dynamic Language Switching** - Switch languages without page reload  
✅ **Beautiful UI Component** - Dropdown selector with native language names and flags  
✅ **Backward Compatible** - Works with existing `useI18n` hook calls  
✅ **Type-Safe** - Full TypeScript support

## Usage in Components

### Option 1: Using the new `useTranslation` hook (Recommended)

```tsx
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();
  
  return (
    <div>
      <h1>{t('app_title')}</h1>
      <p>{t('app_tagline')}</p>
    </div>
  );
}
```

### Option 2: Using the backward-compatible `useI18n` hook

```tsx
import { useI18n } from '@/hooks/useTranslation';

function MyComponent() {
  const { t, locale, setLocale } = useI18n();
  
  return (
    <div>
      <h1>{t('app_title')}</h1>
      <p>Current language: {locale}</p>
      <button onClick={() => setLocale('hi')}>Switch to Hindi</button>
    </div>
  );
}
```

### Using with Variables/Interpolation

```tsx
// In translation file (en.json):
// "showing_n_of_m": "Showing {{n}} of {{m}} crops"

const { t } = useTranslation();
const message = t('showing_n_of_m', { n: 10, m: 50 });
// Output: "Showing 10 of 50 crops"
```

## Language Switcher Component

The `<LanguageSwitcher />` component is automatically included in the navigation bar.

### Manual Usage

```tsx
import { LanguageSwitcher } from '@/components/LanguageSwitcher';

function MyLayout() {
  return (
    <div>
      <LanguageSwitcher />
    </div>
  );
}
```

## Adding New Translations

### 1. Add to Translation Files

Add your new key to all language files in `src/locales/`:

**en.json:**
```json
{
  "translation": {
    "my_new_key": "My New Text in English"
  }
}
```

**hi.json:**
```json
{
  "translation": {
    "my_new_key": "हिन्दी में मेरा नया पाठ"
  }
}
```

### 2. Use in Component

```tsx
const { t } = useTranslation();
return <div>{t('my_new_key')}</div>;
```

## Translation File Structure

```
src/
├── locales/
│   ├── en.json  # English translations
│   ├── hi.json  # Hindi translations
│   ├── ta.json  # Tamil translations
│   ├── te.json  # Telugu translations
│   └── kn.json  # Kannada translations
├── i18n.ts      # i18next configuration
└── hooks/
    └── useTranslation.ts  # Custom hooks
```

## Configuration

Main configuration is in `src/i18n.ts`:

```typescript
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',  // Default language
    detection: {
      order: ['localStorage', 'navigator', 'htmlTag'],
      caches: ['localStorage'],
    },
  });
```

## Language Detection Order

1. **localStorage** - Previously selected language
2. **navigator** - Browser language settings
3. **htmlTag** - HTML lang attribute

## API

### useTranslation()

```typescript
const { t, i18n, currentLanguage, changeLanguage } = useTranslation();

// t: Translation function
// i18n: Full i18next instance
// currentLanguage: Current language code
// changeLanguage: Function to change language
```

### useI18n() (Legacy)

```typescript
const { t, locale, setLocale } = useI18n();

// t: Translation function
// locale: Current language code ('en' | 'hi' | 'ta' | 'te' | 'kn')
// setLocale: Function to change language
```

## Testing

To test language switching:

1. Open the app in your browser
2. Click the language selector (Globe icon) in the navigation bar
3. Select a language
4. Verify all text changes to the selected language
5. Refresh the page - your selection should be remembered

## Troubleshooting

### Missing Translation

If a translation key is missing, the system will:
1. Try to use the English (fallback) translation
2. If that's also missing, display the key itself

### Adding More Languages

To add a new language:

1. Create a new JSON file in `src/locales/` (e.g., `fr.json`)
2. Add translations following the existing structure
3. Update `src/i18n.ts`:
   ```typescript
   import fr from './locales/fr.json';
   
   const resources = {
     en: { translation: en.translation },
     // ... existing languages
     fr: { translation: fr.translation },
   };
   
   export const languages = [
     // ... existing languages
     { code: 'fr', name: 'French', nativeName: 'Français', flag: '🇫🇷' },
   ];
   ```

## Migration from Old i18n System

The old `i18n.tsx` system has been backed up to `i18n.old.tsx`. All existing components using `useI18n()` will continue to work with the new system thanks to the compatibility layer in `src/hooks/useTranslation.ts`.

### No Code Changes Required

Components using the old system will work automatically:

```tsx
// Old code - still works!
import { useI18n } from "../i18n";

function MyComponent() {
  const { t } = useI18n();
  return <div>{t('app_title')}</div>;
}
```

Now it will import from `@/hooks/useTranslation` and work with the new system!

## Best Practices

1. **Always use translation keys** - Never hardcode text
2. **Use descriptive keys** - `nav_home` instead of `h1` or `text1`
3. **Group related keys** - Use prefixes like `nav_`, `form_`, `error_`
4. **Keep translations consistent** - Same meaning across all languages
5. **Test all languages** - Verify translations work in context
6. **Use interpolation** - For dynamic content like numbers

## Support

For questions or issues with translations, check:
- i18next documentation: https://www.i18next.com/
- react-i18next documentation: https://react.i18next.com/

---

Created: October 2025  
Last Updated: October 2025
