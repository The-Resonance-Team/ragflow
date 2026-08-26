import en from '../en';
import vi from '../vi';

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
];

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
      expect(viKeys).toEqual(enKeys);
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
});
