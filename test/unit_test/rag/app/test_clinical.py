#
#  Copyright 2026 The InfiniFlow Authors. All Rights Reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.
#
from rag.app import clinical, laws


def test_clinical_chunks_deeper_than_laws_default(monkeypatch):
    # End-to-end through the clinical seam: clinical.chunk must reach laws'
    # tree_merge at a heading level deeper than the laws default (2), so each
    # numbered recommendation stays its own chunk under its section path.
    depths = []
    monkeypatch.setattr(laws, "get_text", lambda filename, binary: "Intro\nRecommendation 1.1 give aspirin\nRecommendation 1.2 give a statin")
    monkeypatch.setattr(laws, "remove_contents_table", lambda *_a, **_k: None)
    monkeypatch.setattr(laws, "make_colon_as_title", lambda *_a, **_k: None)
    monkeypatch.setattr(laws, "bullets_category", lambda *_a, **_k: 0)
    monkeypatch.setattr(laws, "tree_merge", lambda bull, sections, depth: depths.append(depth) or [])
    monkeypatch.setattr(laws, "tokenize_chunks", lambda *a, **k: [])
    monkeypatch.setattr(laws.rag_tokenizer, "tokenize", lambda text: text)
    monkeypatch.setattr(laws.rag_tokenizer, "fine_grained_tokenize", lambda text: text)

    clinical.chunk("guideline.txt", binary=b"x", callback=lambda *_a, **_k: None)

    assert depths == [clinical.CLINICAL_HEADING_LEVEL]
    assert clinical.CLINICAL_HEADING_LEVEL == 3
