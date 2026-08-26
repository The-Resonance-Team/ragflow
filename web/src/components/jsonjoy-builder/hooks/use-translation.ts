import { useContext } from 'react';
import { useTranslation as useI18NextTranslation } from 'react-i18next';
import { de } from '../i18n/locales/de';
import { en } from '../i18n/locales/en';
import { fr } from '../i18n/locales/fr';
import { ru } from '../i18n/locales/ru';
import { tr } from '../i18n/locales/tr';
import { vi } from '../i18n/locales/vi';
import { TranslationContext } from '../i18n/translation-context';
import type { Translation } from '../i18n/translation-keys';

const locales: Record<string, Translation> = {
  de,
  fr,
  ru,
  tr,
  vi,
};

export function useTranslation() {
  const translation = useContext(TranslationContext);
  const { i18n } = useI18NextTranslation();
  return translation ?? locales[i18n.language] ?? en;
}

export function formatTranslation(
  template: string,
  values: Record<string, string | number>,
) {
  return template.replace(/\{(\w+)\}/g, (_, key) => {
    const value = values[key];
    return value !== undefined ? String(value) : `{${key}}`;
  });
}
