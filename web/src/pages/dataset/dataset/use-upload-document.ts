import { UploadFormSchemaType } from '@/components/file-upload-dialog';
import { useSetModalState } from '@/hooks/common-hooks';
import {
  ConflictDirective,
  IUploadConflict,
  useRunDocument,
  useUploadDocument,
} from '@/hooks/use-document-request';
import { getUnSupportedFilesCount } from '@/utils/document-util';
import { useCallback, useState } from 'react';

interface IPendingConflicts {
  files: File[];
  conflicts: IUploadConflict[];
  parserConfig?: Record<string, any>;
}

export const useHandleUploadDocument = () => {
  const {
    visible: documentUploadVisible,
    hideModal: hideDocumentUploadModal,
    showModal: showDocumentUploadModal,
  } = useSetModalState();
  const {
    visible: conflictModalVisible,
    hideModal: hideConflictModal,
    showModal: showConflictModal,
  } = useSetModalState();
  const { uploadDocument, loading } = useUploadDocument();
  const { runDocumentByIds } = useRunDocument();

  const [pendingConflicts, setPendingConflicts] = useState<IPendingConflicts>();
  const [conflictResolving, setConflictResolving] = useState(false);
  const [parseOnCreationPending, setParseOnCreationPending] = useState(false);

  const runCreatedDocuments = useCallback(
    (uploadedIds: string[]) => {
      if (uploadedIds.length > 0) {
        runDocumentByIds({
          documentIds: uploadedIds,
          run: 1,
        });
      }
    },
    [runDocumentByIds],
  );

  const onDocumentUploadOk = useCallback(
    async ({
      fileList,
      parseOnCreation,
      tableColumnMode,
      tableColumnRoles,
    }: UploadFormSchemaType) => {
      if (fileList.length > 0) {
        // Build parser_config if column roles are configured
        let parserConfig: Record<string, any> | undefined;
        if (
          tableColumnMode === 'manual' &&
          tableColumnRoles &&
          Object.keys(tableColumnRoles).length > 0
        ) {
          parserConfig = {
            table_column_mode: 'manual',
            table_column_roles: tableColumnRoles,
          };
        }

        const ret = await uploadDocument(fileList as File[], parserConfig);

        // Check for success (code === 0) or partial success (code === 500 with some files)
        const isSuccess = ret?.code === 0;
        const isPartialSuccess = ret?.code === 500 && ret?.message;

        if (!isSuccess && !isPartialSuccess) {
          return;
        }

        const uploaded = ret.data?.uploaded ?? [];
        const conflicts = ret.data?.conflicts ?? [];
        const replaced = ret.data?.replaced ?? [];

        // Trigger parsing for newly created documents when parseOnCreation is
        // enabled. Replaced documents are re-parsed by the backend itself.
        if ((isSuccess || isPartialSuccess) && parseOnCreation) {
          const createdIds = uploaded.map((x) => x.id).filter((id) => !replaced.some((r) => r.id === id));
          if (conflicts.length === 0 && createdIds.length > 0) {
            runCreatedDocuments(createdIds);
          }
          // With pending conflicts, defer parsing until the conflict dialog resolves.
          if (conflicts.length > 0) {
            setParseOnCreationPending(parseOnCreation);
          }
        }

        if (conflicts.length > 0) {
          setPendingConflicts({
            files: fileList as File[],
            conflicts,
            parserConfig,
          });
          showConflictModal();
          return;
        }

        if (isSuccess) {
          hideDocumentUploadModal();
          return 0;
        }

        // For partial success (code 500), check if any files were uploaded
        const count = getUnSupportedFilesCount(ret?.message);
        if (count !== fileList.length) {
          hideDocumentUploadModal();
          return 0;
        }

        return ret?.code;
      }
    },
    [
      uploadDocument,
      runCreatedDocuments,
      hideDocumentUploadModal,
      showConflictModal,
    ],
  );

  const onConflictsResolved = useCallback(
    async ({
      decisions,
      removed,
    }: {
      decisions: Record<string, 'replace' | 'rename'>;
      removed: string[];
    }) => {
      if (!pendingConflicts) {
        hideConflictModal();
        return;
      }
      const { files, conflicts, parserConfig } = pendingConflicts;

      const groups: Record<Exclude<ConflictDirective, undefined>, string[]> = {
        replace: [],
        rename: [],
      };
      conflicts.forEach((conflict) => {
        const decision = decisions[conflict.id];
        if (!decision || removed.includes(conflict.id)) {
          return; // removed files are skipped entirely
        }
        groups[decision].push(conflict.name);
      });

      setConflictResolving(true);
      try {
        const createdIds: string[] = [];
        for (const directive of ['replace', 'rename'] as const) {
          const names = new Set(groups[directive]);
          if (names.size === 0) {
            continue;
          }
          const retryFiles = files.filter((file) => names.has(file.name));
          const ret = await uploadDocument(retryFiles, parserConfig, directive);
          if (ret.code === 0 || ret.code === 500) {
            (ret.data?.uploaded ?? []).forEach((doc) =>
              createdIds.push(doc.id),
            );
          }
        }
        if (parseOnCreationPending) {
          setParseOnCreationPending(false);
          runCreatedDocuments(createdIds);
        }
      } finally {
        setConflictResolving(false);
        setPendingConflicts(undefined);
        hideConflictModal();
        hideDocumentUploadModal();
      }
    },
    [
      pendingConflicts,
      uploadDocument,
      parseOnCreationPending,
      runCreatedDocuments,
      hideConflictModal,
      hideDocumentUploadModal,
    ],
  );

  return {
    documentUploadLoading: loading,
    onDocumentUploadOk,
    documentUploadVisible,
    hideDocumentUploadModal,
    showDocumentUploadModal,
    conflictModalVisible,
    conflictResolving,
    pendingConflicts: pendingConflicts?.conflicts ?? [],
    onConflictsResolved,
    hideConflictModal,
  };
};
