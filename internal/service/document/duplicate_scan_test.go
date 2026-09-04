package document

import (
	"context"
	"fmt"
	"math"
	"strings"
	"testing"

	"ragflow/internal/entity"
)

func TestDuplicateScan_ExactGroups(t *testing.T) {
	db := setupServiceTestDB(t)
	pushServiceDB(t, db)

	// KB with no embedding (exact scan should work)
	if err := db.Create(&entity.Knowledgebase{ID: "kb-exact", TenantID: "tenant-1", EmbdID: ""}).Error; err != nil {
		t.Fatalf("create kb: %v", err)
	}
	h1 := "abc123"
	h2 := "xyz789"
	docs := []*entity.Document{
		{ID: "d1", KbID: "kb-exact", Name: strPtr("a.pdf"), ContentHash: &h1, Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d2", KbID: "kb-exact", Name: strPtr("b.pdf"), ContentHash: &h1, Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d3", KbID: "kb-exact", Name: strPtr("c.pdf"), ContentHash: &h2, Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d4", KbID: "kb-exact", Name: strPtr("d.pdf"), ContentHash: &h2, Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d5", KbID: "kb-exact", Name: strPtr("e.pdf"), ContentHash: strPtr("unique"), Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d6", KbID: "kb-exact", Name: strPtr("f.pdf"), ContentHash: strPtr(""), Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d7", KbID: "kb-exact", Name: strPtr("g.pdf"), ContentHash: nil, Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d8", KbID: "kb-exact", Name: strPtr("disabled.pdf"), ContentHash: &h1, Status: strPtr("0"), ParserConfig: entity.JSONMap{}},
	}
	for _, d := range docs {
		if err := db.Create(d).Error; err != nil {
			t.Fatalf("create doc %s: %v", d.ID, err)
		}
	}
	svc := testDocumentService(t)
	resp, code, err := svc.DuplicateScan(context.Background(), "kb-exact", "exact", 0.97)
	if err != nil {
		t.Fatalf("DuplicateScan exact: %v", err)
	}
	if code != 0 {
		t.Fatalf("code = %v, want 0", code)
	}
	if len(resp.ExactGroups) != 2 {
		t.Fatalf("exact groups = %d, want 2", len(resp.ExactGroups))
	}
	// sorted by content_hash
	if resp.ExactGroups[0].ContentHash != "abc123" {
		t.Fatalf("first group hash = %s, want abc123", resp.ExactGroups[0].ContentHash)
	}
	if len(resp.ExactGroups[0].DocIDs) != 2 {
		t.Fatalf("group 0 count = %d, want 2", len(resp.ExactGroups[0].DocIDs))
	}
	// disabled doc must not be in any group
	for _, g := range resp.ExactGroups {
		for _, id := range g.DocIDs {
			if id == "d8" {
				t.Fatalf("disabled doc d8 should not appear in exact groups")
			}
		}
	}
	if len(resp.NearGroups) != 0 {
		t.Fatalf("near groups should be empty for mode=exact, got %d", len(resp.NearGroups))
	}
}

func TestDuplicateScan_BothWithInjectedEmbedding(t *testing.T) {
	db := setupServiceTestDB(t)
	pushServiceDB(t, db)

	if err := db.Create(&entity.Knowledgebase{ID: "kb-both", TenantID: "tenant-1", EmbdID: "embd-test"}).Error; err != nil {
		t.Fatalf("create kb: %v", err)
	}
	h := "samehash"
	// two docs with same content_hash (exact) and same name (near via hash-bucket)
	// third doc different
	docs := []*entity.Document{
		{ID: "d1", KbID: "kb-both", Name: strPtr("identical content"), ContentHash: &h, Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d2", KbID: "kb-both", Name: strPtr("identical content"), ContentHash: &h, Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
		{ID: "d3", KbID: "kb-both", Name: strPtr("totally different unique text xyz"), ContentHash: strPtr("other"), Status: strPtr("1"), ParserConfig: entity.JSONMap{}},
	}
	for _, d := range docs {
		if err := db.Create(d).Error; err != nil {
			t.Fatalf("create doc: %v", err)
		}
	}
	svc := testDocumentService(t)
	svc.embedTexts = hashBucketEmbed
	resp, _, err := svc.DuplicateScan(context.Background(), "kb-both", "both", 0.97)
	if err != nil {
		t.Fatalf("DuplicateScan both: %v", err)
	}
	if len(resp.ExactGroups) != 1 {
		t.Fatalf("exact groups = %d, want 1", len(resp.ExactGroups))
	}
	// near: d1 and d2 have identical names -> injected vectors identical -> cosine 1.0 -> grouped
	// d3 is different -> not grouped at 0.97
	if len(resp.NearGroups) != 1 {
		t.Fatalf("near groups = %d, want 1 (d1+d2 identical)", len(resp.NearGroups))
	}
	if len(resp.NearGroups[0].DocIDs) != 2 {
		t.Fatalf("near group size = %d, want 2", len(resp.NearGroups[0].DocIDs))
	}
	if resp.NearGroups[0].MaxSimilarity < 0.99 {
		t.Fatalf("max similarity = %v, want ~1.0", resp.NearGroups[0].MaxSimilarity)
	}
}

func TestDuplicateScan_NoEmbeddingModel(t *testing.T) {
	db := setupServiceTestDB(t)
	pushServiceDB(t, db)
	if err := db.Create(&entity.Knowledgebase{ID: "kb-noembd", TenantID: "tenant-1", EmbdID: ""}).Error; err != nil {
		t.Fatalf("create kb: %v", err)
	}
	if err := db.Create(&entity.Document{ID: "d1", KbID: "kb-noembd", Name: strPtr("a.pdf"), ContentHash: strPtr("h1"), Status: strPtr("1"), ParserConfig: entity.JSONMap{}}).Error; err != nil {
		t.Fatalf("create doc: %v", err)
	}
	svc := testDocumentService(t)
	// embedding mode without model should error
	if _, _, err := svc.DuplicateScan(context.Background(), "kb-noembd", "embedding", 0.97); err == nil {
		t.Fatalf("expected error for embedding without model")
	}
	// both mode with no model should succeed with warning and no near groups
	resp, _, err := svc.DuplicateScan(context.Background(), "kb-noembd", "both", 0.97)
	if err != nil {
		t.Fatalf("both mode without embd should not error: %v", err)
	}
	if resp.Warning == nil {
		t.Fatalf("expected warning for missing embedding in both mode")
	}
	if len(resp.NearGroups) != 0 {
		t.Fatalf("near groups should be empty when no embedding model")
	}
}

func TestDuplicateScan_Validation(t *testing.T) {
	db := setupServiceTestDB(t)
	pushServiceDB(t, db)
	if err := db.Create(&entity.Knowledgebase{ID: "kb-val", TenantID: "tenant-1"}).Error; err != nil {
		t.Fatalf("create kb: %v", err)
	}
	svc := testDocumentService(t)
	if _, _, err := svc.DuplicateScan(context.Background(), "kb-val", "invalid", 0.97); err == nil {
		t.Fatalf("expected error for invalid mode")
	}
	if _, _, err := svc.DuplicateScan(context.Background(), "kb-val", "exact", 0.5); err == nil {
		t.Fatalf("expected error for threshold out of range")
	}
	if _, _, err := svc.DuplicateScan(context.Background(), "kb-val", "exact", 1.5); err == nil {
		t.Fatalf("expected error for threshold out of range")
	}
	if _, _, err := svc.DuplicateScan(context.Background(), "no-such-kb", "exact", 0.97); err == nil {
		t.Fatalf("expected error for missing dataset")
	}
}

func strPtr(s string) *string { return &s }

// hashBucketEmbed is a deterministic test double standing in for the model
// provider at the embed seam: identical texts -> cosine 1.0, no external model.
func hashBucketEmbed(_ context.Context, _, _ string, texts []string) ([][]float32, error) {
	const dim = 32
	vecs := make([][]float32, len(texts))
	for i, t := range texts {
		v := make([]float32, dim)
		words := strings.Fields(strings.ToLower(t))
		if len(words) == 0 {
			words = []string{t}
		}
		for _, w := range words {
			h := 0
			for _, c := range w {
				h = h*31 + int(c)
			}
			if h < 0 {
				h = -h
			}
			v[h%dim] += 1
		}
		var sum float64
		for _, x := range v {
			sum += float64(x) * float64(x)
		}
		if norm := math.Sqrt(sum); norm > 0 {
			for j := range v {
				v[j] = float32(float64(v[j]) / norm)
			}
		}
		vecs[i] = v
	}
	return vecs, nil
}

func TestDuplicateScan_EmbeddingErrorBothModeWarns(t *testing.T) {
	db := setupServiceTestDB(t)
	pushServiceDB(t, db)
	if err := db.Create(&entity.Knowledgebase{ID: "kb-err", TenantID: "tenant-1", EmbdID: "embd-broken"}).Error; err != nil {
		t.Fatalf("create kb: %v", err)
	}
	for i, id := range []string{"d1", "d2"} {
		name := fmt.Sprintf("doc %d", i)
		if err := db.Create(&entity.Document{ID: id, KbID: "kb-err", Name: &name, ContentHash: strPtr("h"), Status: strPtr("1"), ParserConfig: entity.JSONMap{}}).Error; err != nil {
			t.Fatalf("create doc: %v", err)
		}
	}
	svc := testDocumentService(t)
	svc.embedTexts = func(context.Context, string, string, []string) ([][]float32, error) {
		return nil, fmt.Errorf("model down")
	}
	// both mode: embedding failure degrades to a warning, exact groups still returned
	resp, _, err := svc.DuplicateScan(context.Background(), "kb-err", "both", 0.97)
	if err != nil {
		t.Fatalf("both mode with embedding error should not fail: %v", err)
	}
	if resp.Warning == nil {
		t.Fatalf("expected warning when embedding fails in both mode")
	}
	if len(resp.NearGroups) != 0 {
		t.Fatalf("near groups should be empty when embedding fails, got %d", len(resp.NearGroups))
	}
}

func TestNearDuplicateGroupsClustersByThreshold(t *testing.T) {
	docs := []*entity.Document{{ID: "a"}, {ID: "b"}, {ID: "c"}}
	vecs := [][]float32{{1, 0}, {1, 0}, {0, 1}}
	groups := nearDuplicateGroups(docs, vecs, 0.97)
	if len(groups) != 1 || len(groups[0].DocIDs) != 2 || groups[0].DocIDs[0] != "a" || groups[0].DocIDs[1] != "b" {
		t.Fatalf("expected {a,b} clustered, {c} alone; got %+v", groups)
	}
	if groups[0].MaxSimilarity < 0.99 {
		t.Fatalf("max similarity = %v, want ~1.0", groups[0].MaxSimilarity)
	}
}
