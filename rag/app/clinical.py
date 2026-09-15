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
"""Clinical chunk method: heading-tree chunking tuned for clinical guidelines.

Reuses the laws heading-tree parser; the only difference is a deeper heading
level so each numbered recommendation stays a distinct chunk under its section,
and the section path rides in the chunk text via tree_merge.
"""

from rag.app import laws

CLINICAL_HEADING_LEVEL = 3


def chunk(filename, binary=None, **kwargs):
    kwargs.setdefault("heading_level", CLINICAL_HEADING_LEVEL)
    return laws.chunk(filename, binary=binary, **kwargs)
