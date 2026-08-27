import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useDuplicateScan } from '@/hooks/use-document-request';
import { Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface DuplicateScanDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  datasetId: string;
}

export function DuplicateScanDialog({
  open,
  onOpenChange,
  datasetId,
}: DuplicateScanDialogProps) {
  const { t } = useTranslation();
  const { data, loading } = useDuplicateScan(datasetId, open);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[640px] max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{t('knowledgeDetails.document.duplicateScan')}</DialogTitle>
          <DialogDescription>
            {t('knowledgeDetails.document.duplicateScanDescription')}
          </DialogDescription>
        </DialogHeader>

        {loading && (
          <div className="flex items-center gap-2 py-8 justify-center text-sm text-text-secondary">
            <Loader2 className="size-4 animate-spin" />
            {t('knowledgeDetails.document.scanning')}
          </div>
        )}

        {!loading && data && (
          <div className="space-y-4">
            {data.warning && (
              <div className="rounded-md border border-border-normal bg-bg-card p-3 text-sm text-text-secondary">
                {data.warning}
              </div>
            )}

            <section>
              <h4 className="text-sm font-medium mb-2">
                {t('knowledgeDetails.document.exactGroups')} — {data.total_exact_groups}
              </h4>
              {data.exact_groups.length === 0 ? (
                <p className="text-sm text-text-secondary">
                  {t('knowledgeDetails.document.noDuplicates')}
                </p>
              ) : (
                <div className="space-y-2">
                  {data.exact_groups.map((g, idx) => (
                    <div
                      key={`${g.content_hash}-${idx}`}
                      className="rounded-md border border-border-normal p-3"
                    >
                      <div className="text-xs text-text-secondary mb-1">
                        {t('knowledgeDetails.document.hash')}:{' '}
                        <span className="font-mono break-all">{g.content_hash}</span> · {g.count} {t('knowledgeDetails.document.documents')}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {g.doc_names.map((name, i) => (
                          <span
                            key={`${g.doc_ids[i]}-${i}`}
                            className="inline-flex items-center rounded bg-bg-card border px-2 py-0.5 text-xs"
                            title={g.doc_ids[i]}
                          >
                            {name || g.doc_ids[i]}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>

            <section>
              <h4 className="text-sm font-medium mb-2">
                {t('knowledgeDetails.document.nearGroups', {
                  threshold: data.threshold,
                })}
                {' — '}
                {data.total_near_groups}
              </h4>
              {data.near_groups.length === 0 ? (
                <p className="text-sm text-text-secondary">
                  {t('knowledgeDetails.document.noDuplicates')}
                </p>
              ) : (
                <div className="space-y-2">
                  {data.near_groups.map((g, idx) => (
                    <div
                      key={`near-${idx}`}
                      className="rounded-md border border-border-normal p-3"
                    >
                      <div className="text-xs text-text-secondary mb-1">
                        {t('knowledgeDetails.document.similarity')}:{' '}
                        {g.max_similarity !== undefined
                          ? g.max_similarity.toFixed(3)
                          : '-'}
                        {' · '}
                        {g.count} {t('knowledgeDetails.document.documents')}
                      </div>
                      <div className="flex flex-wrap gap-1">
                        {g.doc_names.map((name, i) => (
                          <span
                            key={`${g.doc_ids[i]}-${i}`}
                            className="inline-flex items-center rounded bg-bg-card border px-2 py-0.5 text-xs"
                            title={g.doc_ids[i]}
                          >
                            {name || g.doc_ids[i]}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </section>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t('common.close')}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
