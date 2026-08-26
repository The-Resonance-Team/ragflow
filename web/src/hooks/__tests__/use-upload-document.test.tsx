import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { renderHook } from '@testing-library/react';
import React from 'react';

import { uploadDocument as uploadDocumentApi } from '@/services/knowledge-service';
import { useUploadDocument } from '../use-document-request';

jest.mock('@/services/knowledge-service', () => ({
  __esModule: true,
  default: {},
  uploadDocument: jest.fn(),
}));

// use-document-request pulls the filter-bar graph (eventsource-parser) that
// jest cannot transform; the upload mutation never calls these, so stub them.
jest.mock('@/components/list-filter-bar/use-handle-filter-submit', () => ({
  useHandleFilterSubmit: jest.fn(() => ({ filterValue: null })),
}));

jest.mock('../logic-hooks', () => ({
  useGetPaginationWithRouter: jest.fn(() => ({ pagination: {}, setPagination: jest.fn() })),
  useHandleSearchChange: jest.fn(() => ({ searchString: '', handleInputChange: jest.fn() })),
}));

jest.mock('../route-hook', () => ({
  useSetPaginationParams: jest.fn(() => jest.fn()),
}));

jest.mock('@/locales/config', () => ({
  __esModule: true,
  default: { t: (key: string) => key, language: 'en' },
}));

jest.mock('react-router', () => ({
  useParams: jest.fn(() => ({ id: 'dataset-1' })),
  useSearchParams: jest.fn(() => [new URLSearchParams()]),
}));

const mockUpload = jest.mocked(uploadDocumentApi);

function makeWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  // esbuild-jest config here loads .ts with the "tsx" loader but .tsx with the
  // plain "ts" loader, so JSX in this test file would not transform. Build the
  // provider element with createElement instead.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const Wrapper = (props: { children: any }) =>
    React.createElement(
      QueryClientProvider,
      { client: queryClient },
      props.children,
    );
  return Wrapper;
}

function makeResponse(data: Record<string, unknown>, code = 0) {
  // The service already unwraps axios' response layer and returns the JSON body.
  return { code, data };
}

describe('useUploadDocument', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('surfaces uploaded, replaced and conflicts from the response payload', async () => {
    const payload = {
      uploaded: [{ id: 'doc-new', name: 'fresh.txt' }],
      replaced: [],
      conflicts: [
        { id: 'doc-old', name: 'dup.txt', size: 3, suffix: 'txt', content_hash: 'h', chunk_count: 0 },
      ],
    };
    mockUpload.mockResolvedValue(makeResponse(payload) as never);

    const { result } = renderHook(() => useUploadDocument(), {
      wrapper: makeWrapper(),
    });

    const ret = await result.current.uploadDocument(
      [new File(['x'], 'dup.txt')],
      undefined,
    );

    expect(ret.code).toBe(0);
    expect(ret.data?.conflicts).toHaveLength(1);
    expect(ret.data?.conflicts[0].name).toBe('dup.txt');
    expect(ret.data?.uploaded[0].name).toBe('fresh.txt');
    expect(mockUpload.mock.calls[0][1] instanceof FormData).toBe(true);
  });

  it('sends the on_conflict form directive on retry', async () => {
    mockUpload.mockResolvedValue(
      makeResponse({ uploaded: [], replaced: [], conflicts: [] }) as never,
    );

    const { result } = renderHook(() => useUploadDocument(), {
      wrapper: makeWrapper(),
    });

    await result.current.uploadDocument(
      [new File(['x'], 'dup.txt')],
      undefined,
      'replace',
    );

    const formData = mockUpload.mock.calls[0][1] as FormData;
    expect(formData.get('on_conflict')).toBe('replace');
  });

  it('omits the on_conflict field for a first attempt', async () => {
    mockUpload.mockResolvedValue(
      makeResponse({ uploaded: [], replaced: [], conflicts: [] }) as never,
    );

    const { result } = renderHook(() => useUploadDocument(), {
      wrapper: makeWrapper(),
    });

    await result.current.uploadDocument([new File(['x'], 'a.txt')]);

    const formData = mockUpload.mock.calls[0][1] as FormData;
    expect(formData.has('on_conflict')).toBe(false);
  });

  it('wraps network failures into a code-500 response', async () => {
    mockUpload.mockRejectedValue(new Error('network down'));

    const { result } = renderHook(() => useUploadDocument(), {
      wrapper: makeWrapper(),
    });

    const ret = await result.current.uploadDocument([
      new File(['x'], 'a.txt'),
    ]);
    expect(ret.code).toBe(500);
    expect(ret.message).toContain('network down');
  });
});
