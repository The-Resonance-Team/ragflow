package document

import (
	"context"
	"fmt"
	"math"
	"sort"
	"strings"

	"ragflow/internal/common"
	"ragflow/internal/dao"
	"ragflow/internal/entity"
	"ragflow/internal/entity/models"
	"ragflow/internal/service"
	"ragflow/internal/storage"
)

// ExactDuplicateGroup groups documents with identical content_hash.
type ExactDuplicateGroup struct {
	ContentHash string   `json:"content_hash"`
	DocIDs      []string `json:"doc_ids"`
	DocNames    []string `json:"doc_names"`
	Count       int      `json:"count"`
}

// NearDuplicateGroup groups documents whose embeddings are ≥ threshold.
type NearDuplicateGroup struct {
	DocIDs        []string `json:"doc_ids"`
	DocNames      []string `json:"doc_names"`
	Count         int      `json:"count"`
	MaxSimilarity float64  `json:"max_similarity"`
	Threshold     float64  `json:"threshold"`
}

// DuplicateScanResponse is the read-only report for one dataset.
type DuplicateScanResponse struct {
	ExactGroups      []*ExactDuplicateGroup `json:"exact_groups"`
	NearGroups       []*NearDuplicateGroup  `json:"near_groups"`
	TotalExactGroups int                    `json:"total_exact_groups"`
	TotalNearGroups  int                    `json:"total_near_groups"`
	Mode             string                 `json:"mode"`
	Threshold        float64                `json:"threshold"`
	Warning          *string                `json:"warning,omitempty"`
}

// embedTextsFunc encodes texts into vectors with the dataset's embedding model.
// It is the seam between DuplicateScan and the model provider: production uses
// the provider-backed implementation; tests inject a deterministic double.
type embedTextsFunc func(ctx context.Context, tenantID, embdID string, texts []string) ([][]float32, error)

func cosineSim(a, b []float32) float64 {
	if len(a) != len(b) || len(a) == 0 {
		return 0
	}
	var dot, na, nb float64
	for i := range a {
		dot += float64(a[i]) * float64(b[i])
		na += float64(a[i]) * float64(a[i])
		nb += float64(b[i]) * float64(b[i])
	}
	if na == 0 || nb == 0 {
		return 0
	}
	return dot / (math.Sqrt(na) * math.Sqrt(nb))
}

// exactDuplicateGroups groups docs by non-empty content_hash, sorted by hash.
func exactDuplicateGroups(docs []*entity.Document) []*ExactDuplicateGroup {
	buckets := map[string][]*entity.Document{}
	for _, d := range docs {
		h := ""
		if d.ContentHash != nil {
			h = strings.TrimSpace(*d.ContentHash)
		}
		if h == "" {
			continue
		}
		buckets[h] = append(buckets[h], d)
	}
	groups := []*ExactDuplicateGroup{}
	for h, lst := range buckets {
		if len(lst) < 2 {
			continue
		}
		docIDs := make([]string, len(lst))
		docNames := make([]string, len(lst))
		for i, d := range lst {
			docIDs[i] = d.ID
			if d.Name != nil {
				docNames[i] = *d.Name
			}
		}
		groups = append(groups, &ExactDuplicateGroup{
			ContentHash: h,
			DocIDs:      docIDs,
			DocNames:    docNames,
			Count:       len(lst),
		})
	}
	sort.Slice(groups, func(i, j int) bool { return groups[i].ContentHash < groups[j].ContentHash })
	return groups
}

// nearDuplicateGroups clusters docs whose vectors are cosine >= threshold
// (union-find over the O(n^2) pairwise matrix).
// ponytail: O(n^2) — add cached doc embeddings + ANN if dataset >5k docs.
func nearDuplicateGroups(docs []*entity.Document, vecs [][]float32, threshold float64) []*NearDuplicateGroup {
	n := len(docs)
	parent := make([]int, n)
	for i := range parent {
		parent[i] = i
	}
	var find func(int) int
	find = func(x int) int {
		for parent[x] != x {
			parent[x] = parent[parent[x]]
			x = parent[x]
		}
		return x
	}
	union := func(a, b int) {
		ra, rb := find(a), find(b)
		if ra != rb {
			parent[rb] = ra
		}
	}
	for i := 0; i < n; i++ {
		for j := i + 1; j < n; j++ {
			if cosineSim(vecs[i], vecs[j]) >= threshold {
				union(i, j)
			}
		}
	}
	buckets := map[int][]int{}
	for idx := range docs {
		r := find(idx)
		buckets[r] = append(buckets[r], idx)
	}
	groups := []*NearDuplicateGroup{}
	for _, idxs := range buckets {
		if len(idxs) < 2 {
			continue
		}
		sort.Ints(idxs)
		docIDs := make([]string, len(idxs))
		docNames := make([]string, len(idxs))
		for k, docIdx := range idxs {
			docIDs[k] = docs[docIdx].ID
			if docs[docIdx].Name != nil {
				docNames[k] = *docs[docIdx].Name
			}
		}
		maxS := 0.0
		for a := 0; a < len(idxs); a++ {
			for b := a + 1; b < len(idxs); b++ {
				s := cosineSim(vecs[idxs[a]], vecs[idxs[b]])
				if s > maxS {
					maxS = s
				}
			}
		}
		groups = append(groups, &NearDuplicateGroup{
			DocIDs:        docIDs,
			DocNames:      docNames,
			Count:         len(idxs),
			MaxSimilarity: math.Round(maxS*10000) / 10000,
			Threshold:     threshold,
		})
	}
	sort.Slice(groups, func(i, j int) bool { return groups[i].DocIDs[0] < groups[j].DocIDs[0] })
	return groups
}

// DuplicateScan groups enabled Current-Version documents in one dataset
// into exact (content_hash) and optionally near (embedding cosine) groups.
// ponytail: synchronous, single dataset — see nearDuplicateGroups for the O(n²) ceiling.
func (s *DocumentService) DuplicateScan(ctx context.Context, datasetID, mode string, threshold float64) (*DuplicateScanResponse, common.ErrorCode, error) {
	if mode != "exact" && mode != "embedding" && mode != "both" {
		return nil, common.CodeDataError, fmt.Errorf("mode must be one of exact, embedding, both")
	}
	if threshold < 0.80 || threshold > 0.99 {
		return nil, common.CodeDataError, fmt.Errorf("threshold must be between 0.80 and 0.99")
	}

	kb, err := s.kbDAO.GetByID(ctx, dao.DB, datasetID)
	if err != nil || kb == nil {
		return nil, common.CodeDataError, fmt.Errorf("can't find this dataset")
	}

	docs, _, err := s.documentDAO.GetByKBID(ctx, dao.DB, datasetID)
	if err != nil {
		return nil, common.CodeServerError, err
	}
	enabled := make([]*entity.Document, 0, len(docs))
	for _, d := range docs {
		st := ""
		if d.Status != nil {
			st = *d.Status
		} else {
			st = "1"
		}
		if st == "1" {
			enabled = append(enabled, d)
		}
	}

	exactGroups := []*ExactDuplicateGroup{}
	if mode == "exact" || mode == "both" {
		exactGroups = exactDuplicateGroups(enabled)
	}

	nearGroups := []*NearDuplicateGroup{}
	var warning *string
	if mode == "embedding" || mode == "both" {
		embdID := kb.EmbdID
		if strings.TrimSpace(embdID) == "" {
			msg := "dataset has no embedding model, near-duplicate scan unavailable"
			if mode == "embedding" {
				return nil, common.CodeDataError, fmt.Errorf("%s", msg)
			}
			warning = &msg
		} else {
			texts := currentVersionTexts(ctx, kb.ID, enabled)
			if len(texts) >= 2 {
				vecs, err := s.embedForScan(ctx, kb.TenantID, embdID, texts)
				if err != nil {
					if mode == "embedding" {
						return nil, common.CodeServerError, err
					}
					msg := fmt.Sprintf("embedding scan unavailable: %v", err)
					warning = &msg
				} else {
					nearGroups = nearDuplicateGroups(enabled, vecs, threshold)
				}
			}
		}
	}

	return &DuplicateScanResponse{
		ExactGroups:      exactGroups,
		NearGroups:       nearGroups,
		TotalExactGroups: len(exactGroups),
		TotalNearGroups:  len(nearGroups),
		Mode:             mode,
		Threshold:        threshold,
		Warning:          warning,
	}, common.CodeSuccess, nil
}

// currentVersionTexts reads each document's Current Version bytes, one text
// per doc in doc order, falling back to name/id and truncating to the
// embedding window (8192, matching the Python path).
func currentVersionTexts(ctx context.Context, bucket string, docs []*entity.Document) []string {
	texts := make([]string, len(docs))
	for i, d := range docs {
		txt := ""
		if d.Location != nil && *d.Location != "" {
			if sto := storage.GetStorageFactory().GetStorage(); sto != nil {
				if data, err := sto.Get(ctx, bucket, *d.Location); err == nil && len(data) > 0 {
					if len(data) > 8192 {
						data = data[:8192]
					}
					txt = string(data)
				}
			}
		}
		if strings.TrimSpace(txt) == "" {
			if d.Name != nil && strings.TrimSpace(*d.Name) != "" {
				txt = *d.Name
			} else {
				txt = d.ID
			}
		}
		if len(txt) > 8192 {
			txt = txt[:8192]
		}
		texts[i] = txt
	}
	return texts
}

// embedForScan encodes texts with the dataset's embedding model.
func (s *DocumentService) embedForScan(ctx context.Context, tenantID, embdID string, texts []string) ([][]float32, error) {
	if s.embedTexts != nil {
		return s.embedTexts(ctx, tenantID, embdID, texts)
	}
	prov := service.NewModelProviderService()
	embModel, err := prov.GetEmbeddingModel(ctx, tenantID, embdID)
	if err != nil {
		return nil, err
	}
	if embModel == nil || embModel.ModelDriver == nil {
		return nil, fmt.Errorf("embedding model %q is not available", embdID)
	}
	data, err := embModel.ModelDriver.Embed(ctx, embModel.ModelName, models.EmbedRequest{Texts: texts}, embModel.APIConfig, nil, nil)
	if err != nil {
		return nil, err
	}
	if len(data) != len(texts) {
		return nil, fmt.Errorf("embedding model %q returned %d vectors for %d texts", embdID, len(data), len(texts))
	}
	vecs := make([][]float32, len(data))
	for i, d := range data {
		v := make([]float32, len(d.Embedding))
		for j, x := range d.Embedding {
			v[j] = float32(x)
		}
		vecs[i] = v
	}
	return vecs, nil
}
