/*
 *  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
 *
 *  Licensed under the Apache License, Version 2.0 (the "License");
 *  you may not use this file except in compliance with the License.
 *  You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 */

import React from 'react';
import ReactDOM from 'react-dom/client';
import '../tailwind.css';
import App from './app';
import './global.less';
import { initLanguage } from './locales/config';
// oxlint-disable-next-line no-restricted-imports -- bootstrap gate: resolve the backend variant before first render
import { fetchBackendLanguage } from './utils/backend-runtime';

const root = ReactDOM.createRoot(document.getElementById('root')!);

// ponytail: paint fallback immediately — was blocked on Promise.all (white screen until /api/v1/language + i18n finished)
root.render(
  <div className="fixed inset-0 z-50 flex items-center justify-center bg-white">
    <div className="h-8 w-8 animate-spin rounded-full border-2 border-gray-300 border-t-gray-600" />
  </div>,
);

Promise.all([initLanguage(), fetchBackendLanguage()])
  .catch(() => {})
  .finally(() => {
    root.render(
      <React.StrictMode>
        <App />
      </React.StrictMode>,
    );
  });
