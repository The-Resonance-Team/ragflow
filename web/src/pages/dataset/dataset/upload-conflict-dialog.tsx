import { IUploadConflict } from '@/hooks/use-document-request';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { X } from 'lucide-react';
import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

export type ConflictDecision = 'replace' | 'rename';

export interface ConflictResolution {
  decisions: Record<string, ConflictDecision>;
  removed: string[];
}

interface IUploadConflictDialogProps {
  open: boolean;
  loading: boolean;
  conflicts: IUploadConflict[];
  onOpenChange: (open: boolean) => void;
  onResolve: (resolution: ConflictResolution) => void;
}

export function UploadConflictDialog({
  open,
  loading,
  conflicts,
  onOpenChange,
  onResolve,
}: IUploadConflictDialogProps) {
  const { t } = useTranslation();
  const [decisions, setDecisions] = useState<Record<string, ConflictDecision>>({});
  const [removed, setRemoved] = useState<string[]>([]);

  useEffect(() => {
    if (open) {
      setDecisions(
        Object.fromEntries(conflicts.map((c) => [c.id, 'replace' as const])),
      );
      setRemoved([]);
    }
  }, [open, conflicts]);

  const handleResolve = useCallback(() => {
    const kept = Object.fromEntries(
      Object.entries(decisions).filter(([id]) => !removed.includes(id)),
    );
    onResolve({ decisions: kept, removed });
  }, [decisions, removed, onResolve]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[560px]">
        <DialogHeader>
          <DialogTitle>{t('fileManager.conflictDialogTitle')}</DialogTitle>
          <DialogDescription>
            {t('fileManager.conflictDialogDescription')}
          </DialogDescription>
        </DialogHeader>
        <div className="flex max-h-[320px] flex-col gap-3 overflow-y-auto">
          {conflicts.map((conflict) => {
            const isRemoved = removed.includes(conflict.id);
            return (
              <div
                key={conflict.id}
                className="rounded-md border border-border-normal p-3"
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="truncate text-sm font-medium" title={conflict.name}>
                    {conflict.name}
                  </span>
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() =>
                      setRemoved((prev) =>
                        isRemoved
                          ? prev.filter((id) => id !== conflict.id)
                          : [...prev, conflict.id],
                      )
                    }
                    aria-label={t('fileManager.conflictRemove')}
                  >
                    <X className={isRemoved ? 'text-state-error' : ''} />
                  </Button>
                </div>
                {!isRemoved && (
                  <RadioGroup
                    className="mt-2 gap-2"
                    value={decisions[conflict.id] ?? 'replace'}
                    onValueChange={(value) =>
                      setDecisions((prev) => ({
                        ...prev,
                        [conflict.id]: value as ConflictDecision,
                      }))
                    }
                  >
                    <div className="flex items-center gap-2">
                      <RadioGroupItem value="replace" id={`${conflict.id}-replace`} />
                      <Label htmlFor={`${conflict.id}-replace`}>
                        {t('fileManager.conflictReplace')}
                        <span className="ms-2 text-xs text-text-secondary">
                          {t('fileManager.conflictReplaceDescription')}
                        </span>
                      </Label>
                    </div>
                    <div className="flex items-center gap-2">
                      <RadioGroupItem value="rename" id={`${conflict.id}-rename`} />
                      <Label htmlFor={`${conflict.id}-rename`}>
                        {t('fileManager.conflictKeepBoth')}
                        <span className="ms-2 text-xs text-text-secondary">
                          {t('fileManager.conflictKeepBothDescription')}
                        </span>
                      </Label>
                    </div>
                  </RadioGroup>
                )}
              </div>
            );
          })}
        </div>
        <DialogFooter>
          <Button loading={loading} onClick={handleResolve}>
            {t('fileManager.conflictResolve')}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
