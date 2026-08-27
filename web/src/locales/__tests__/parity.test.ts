import ar from '../ar';
import bg from '../bg';
import de from '../de';
import en from '../en';
import es from '../es';
import fr from '../fr';
import id from '../id';
import it from '../it';
import ja from '../ja';
import ko from '../ko';
import ptBr from '../pt-br';
import ru from '../ru';
import tr from '../tr';
import vi from '../vi';
import zh from '../zh';
import zhTraditional from '../zh-traditional';

type LocaleTree = Record<string, unknown>;
type TranslationModule = { translation: LocaleTree };

const enRoot = en as TranslationModule;
const viRoot = vi as TranslationModule;

const FULL_NAMESPACES = [
  'common',
  'login',
  'header',
  'knowledgeList',
  'knowledgeDetails',
  'knowledgeConfiguration',
  'message',
  'fileManager',
  'modal',
  'pagination',
  'deleteModal',
  'empty',
] as const;

function leafPaths(node: LocaleTree, prefix = ''): string[] {
  return Object.entries(node).flatMap(([key, value]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return value !== null && typeof value === 'object'
      ? leafPaths(value as LocaleTree, path)
      : [path];
  });
}

function namespaceOf(root: TranslationModule, ns: string): LocaleTree {
  return root.translation[ns] as LocaleTree;
}

// ponytail: vi is the only blocking locale per ADR Q1; other locales emit a non-blocking drift report
const ALL_LOCALES: Record<string, TranslationModule> = {
  ar: ar as TranslationModule,
  bg: bg as TranslationModule,
  de: de as TranslationModule,
  es: es as TranslationModule,
  fr: fr as TranslationModule,
  id: id as TranslationModule,
  it: it as TranslationModule,
  ja: ja as TranslationModule,
  ko: ko as TranslationModule,
  'pt-br': ptBr as TranslationModule,
  ru: ru as TranslationModule,
  tr: tr as TranslationModule,
  zh: zh as TranslationModule,
  'zh-traditional': zhTraditional as TranslationModule,
};

describe('locale parity', () => {
  it('vi does not introduce namespaces that are absent from en', () => {
    const enTop = Object.keys(enRoot.translation);
    const stale = Object.keys(viRoot.translation).filter(
      (ns) => !enTop.includes(ns),
    );
    expect(stale).toEqual([]);
  });

  it.each(FULL_NAMESPACES)(
    '%s has identical key trees in en and vi',
    (ns) => {
      const enKeys = leafPaths(namespaceOf(enRoot, ns)).sort();
      const viKeys = leafPaths(namespaceOf(viRoot, ns)).sort();
      const missing = enKeys.filter((k) => !viKeys.includes(k));
      const extra = viKeys.filter((k) => !enKeys.includes(k));
      if (missing.length || extra.length) {
        // readable per grill Q2: list exactly which keys are missing/stale
        const msg = [
          `namespace ${ns}:`,
          missing.length ? `  missing (${missing.length}): ${missing.join(', ')}` : '',
          extra.length ? `  stale (${extra.length}): ${extra.join(', ')}` : '',
        ]
          .filter(Boolean)
          .join('\n');
        // fail with precise list rather than opaque array diff
        throw new Error(msg);
      }
    },
  );

  it('covered vi values are filled unless the en value is empty', () => {
    const violations: string[] = [];
    for (const ns of FULL_NAMESPACES) {
      const enNs = namespaceOf(enRoot, ns);
      const viNs = namespaceOf(viRoot, ns);
      for (const path of leafPaths(viNs)) {
        const get = (obj: unknown) =>
          path
            .split('.')
            .reduce<unknown>((acc, key) => (acc as LocaleTree)[key], obj);
        const viValue = get(viNs);
        if (
          (typeof viValue !== 'string' || viValue.trim() === '') &&
          viValue !== get(enNs)
        ) {
          violations.push(`${ns}.${path}`);
        }
      }
    }
    expect(violations).toEqual([]);
  });

  // Non-blocking drift report for remaining locales (Q1): logs but does not fail CI
  it('other locales drift report (non-blocking)', () => {
    const drifts: string[] = [];
    for (const [locale, mod] of Object.entries(ALL_LOCALES)) {
      for (const ns of FULL_NAMESPACES) {
        const enKeys = leafPaths(namespaceOf(enRoot, ns)).sort();
        const locKeys = leafPaths(namespaceOf(mod, ns as string)).sort();
        const missing = enKeys.filter((k) => !locKeys.includes(k));
        const extra = locKeys.filter((k) => !enKeys.includes(k));
        if (missing.length || extra.length) {
          drifts.push(
            `${locale}.${ns}: missing ${missing.length}${missing.length ? ` [${missing.slice(0, 5).join(', ')}${missing.length > 5 ? ', ...' : ''}]` : ''}; stale ${extra.length}${extra.length ? ` [${extra.slice(0, 5).join(', ')}]` : ''}`,
          );
        }
      }
    }
    if (drifts.length) {
      // eslint-disable-next-line no-console
      console.warn(
        `[i18n drift] ${drifts.length} namespace drifts (non-blocking, Q1):\n` +
          drifts.join('\n'),
      );
    }
    // intentionally not failing — vi is the blocking gate
    expect(true).toBe(true);
  });
});
