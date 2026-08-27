import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  IDocumentVersion,
  useFetchDocumentVersions,
  useRestoreDocumentVersion,
} from '@/hooks/use-document-request';
import api from '@/utils/api';
import { formatDate } from '@/utils/date';
import { downloadFileFromBlob, formatBytes } from '@/utils/file-util';
import request from '@/utils/request';
import { Download, Eye, History, RotateCcw } from 'lucide-react';
import { useCallback } from 'react';
import { useTranslation } from 'react-i18next';

interface Props {
  datasetId: string;
  documentId: string;
  documentName: string;
  open: boolean;
  onOpenChange: (v: boolean) => void;
}

export function DocumentVersionHistoryDrawer({
  datasetId,
  documentId,
  documentName,
  open,
  onOpenChange,
}: Props) {
  const { t } = useTranslation();
  const { data: versions, loading } = useFetchDocumentVersions(
    datasetId,
    documentId,
    open,
  );
  const { restoreDocumentVersion, loading: restoring } =
    useRestoreDocumentVersion(datasetId, documentId);

  const handleDownload = useCallback(
    async (v: IDocumentVersion) => {
      try {
        const res = await request.get(
          api.getDatasetDocumentFileDownload(datasetId!, documentId),
          {
            params: { version_id: v.id },
            responseType: 'blob',
          },
        );
        const blob = new Blob([res.data], {
          type: res.headers?.['content-type'] || 'application/octet-stream',
        });
        downloadFileFromBlob(blob, documentName);
      } catch (e) {
        console.error(e);
      }
    },
    [datasetId, documentId, documentName],
  );

  const handleRestore = useCallback(
    async (v: IDocumentVersion) => {
      if (v.is_current) return;
      const ok = window.confirm(
        `${t('knowledgeDetails.document.restoreConfirmTitle')}\n${t('knowledgeDetails.document.restoreConfirmContent')}`,
      );
      if (!ok) return;
      await restoreDocumentVersion(v.id);
    },
    [restoreDocumentVersion, t],
  );

  const handlePreview = useCallback(
    async (v: IDocumentVersion) => {
      try {
        const res = await request.get(api.documentPreview(documentId), {
          params: { version_id: v.id },
          responseType: 'blob',
        });
        const blob = new Blob([res.data], {
          type: res.headers?.['content-type'] || 'application/octet-stream',
        });
        const url = URL.createObjectURL(blob);
        window.open(url, '_blank');
        setTimeout(() => URL.revokeObjectURL(url), 10_000);
      } catch (e) {
        console.error(e);
      }
    },
    [documentId],
  );

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent className="w-[720px] max-w-[90vw] flex flex-col">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2">
            <History className="size-4" />
            {t('knowledgeDetails.document.versionHistory')}
            <span className="text-sm text-text-secondary font-normal truncate">
              — {documentName}
            </span>
          </SheetTitle>
        </SheetHeader>

        <div className="flex-1 overflow-auto mt-4 border rounded-md">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>{t('knowledgeDetails.document.version')}</TableHead>
                <TableHead>{t('knowledgeDetails.document.origin')}</TableHead>
                <TableHead>{t('knowledgeDetails.document.time')}</TableHead>
                <TableHead>{t('knowledgeDetails.document.actor')}</TableHead>
                <TableHead>{t('knowledgeDetails.document.size')}</TableHead>
                <TableHead>{t('knowledgeDetails.document.hash')}</TableHead>
                <TableHead className="text-right">
                  {t('knowledgeDetails.action')}
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    Loading...
                  </TableCell>
                </TableRow>
              ) : versions.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} className="text-center py-8">
                    {t('knowledgeDetails.document.empty')}
                  </TableCell>
                </TableRow>
              ) : (
                versions.map((v) => (
                  <TableRow key={v.id}>
                    <TableCell>
                      <span className="font-mono">v{v.version_number}</span>{' '}
                      {v.is_current && (
                        <Badge variant="outline" className="ml-1">
                          {t('knowledgeDetails.document.currentBadge')}
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant={v.origin === 'restore' ? 'secondary' : 'default'}>
                        {v.origin === 'restore'
                          ? t('knowledgeDetails.document.originRestore')
                          : t('knowledgeDetails.document.originUpload')}
                      </Badge>
                    </TableCell>
                    <TableCell className="whitespace-nowrap">
                      {formatDate(v.create_time)}
                    </TableCell>
                    <TableCell
                      className="max-w-[100px] truncate"
                      title={v.created_by_nickname || v.created_by}
                    >
                      {v.created_by_nickname || v.created_by.slice(0, 8)}
                    </TableCell>
                    <TableCell>{formatBytes(v.size)}</TableCell>
                    <TableCell
                      className="font-mono text-xs max-w-[90px] truncate"
                      title={v.content_hash}
                    >
                      {v.content_hash.slice(0, 8)}
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex justify-end gap-1">
                        <Button
                          size="icon-xs"
                          variant="ghost"
                          onClick={() => handlePreview(v)}
                          title={t('common.preview')}
                        >
                          <Eye className="size-3" />
                        </Button>
                        <Button
                          size="icon-xs"
                          variant="ghost"
                          onClick={() => handleDownload(v)}
                          title={t('knowledgeDetails.document.download')}
                        >
                          <Download className="size-3" />
                        </Button>
                        <Button
                          size="icon-xs"
                          variant="ghost"
                          disabled={v.is_current || restoring}
                          onClick={() => handleRestore(v)}
                          title={t('knowledgeDetails.document.restore')}
                        >
                          <RotateCcw className="size-3" />
                        </Button>
                      </div>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </div>
      </SheetContent>
    </Sheet>
  );
}
