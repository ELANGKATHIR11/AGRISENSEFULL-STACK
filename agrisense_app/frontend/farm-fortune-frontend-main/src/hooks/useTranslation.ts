import { useTranslation as useTranslationOriginal } from 'react-i18next';

/**
 * Custom hook for translations with type safety and convenience methods
 */
export function useTranslation() {
  const { t, i18n } = useTranslationOriginal();

  return {
    t,
    i18n,
    currentLanguage: i18n.language,
    changeLanguage: (lng: string) => i18n.changeLanguage(lng),
  };
}

/**
 * Hook for backward compatibility with old i18n system
 * Provides the same interface as the old useI18n hook
 */
export function useI18n() {
  const { t, i18n } = useTranslationOriginal();

  return {
    t,
    locale: i18n.language as 'en' | 'hi' | 'ta' | 'te' | 'kn',
    setLocale: (lng: 'en' | 'hi' | 'ta' | 'te' | 'kn') => i18n.changeLanguage(lng),
  };
}
