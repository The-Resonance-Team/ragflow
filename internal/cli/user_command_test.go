package cli

import (
	"net/http"
	"strings"
	"testing"
)

// newTestCLIClients point the CLI's concrete HTTP clients at an httptest
// server so command handlers run end-to-end without a live RAGFlow server.
func newTestAPIModeCLI(t *testing.T, handler http.Handler) *CLI {
	t.Helper()
	return &CLI{
		Config: &CommandLineConfig{
			CLIMode:         APIMode,
			APIClientConfig: APIModeConfig{CurrentAPIServer: "test"},
		},
		APIServerClientMap: map[string]*HTTPClient{"test": newTestHTTPClient(t, handler)},
	}
}

func TestCLI_APIShowVersionCommand(t *testing.T) {
	var gotPath string
	c := newTestAPIModeCLI(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"code": 0, "data": "8.0.0"}`))
	}))

	resp, err := c.ExecuteUserCommand(&Command{Type: "api_show_version"})
	if err != nil {
		t.Fatalf("api_show_version: %v", err)
	}
	kv, ok := resp.(*KeyValueResponse)
	if !ok || kv.Value != "8.0.0" {
		t.Fatalf("resp = %+v, want value 8.0.0", resp)
	}
	if !strings.HasSuffix(gotPath, "/system/version") {
		t.Fatalf("request path = %s, want suffix /system/version", gotPath)
	}
}

func TestCLI_APIShowVariableCommand(t *testing.T) {
	guarded := newTestAPIModeCLI(t, http.HandlerFunc(func(http.ResponseWriter, *http.Request) {
		t.Error("handler must not be reached without credentials")
	}))
	if _, err := guarded.ExecuteUserCommand(&Command{Type: "api_show_variable", Params: map[string]any{"var_name": "memory_size"}}); err == nil {
		t.Fatalf("expected credential guard error, got nil")
	}

	var gotPath, gotAuth string
	c := newTestAPIModeCLI(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotPath = r.URL.Path
		gotAuth = r.Header.Get("Authorization")
		w.Header().Set("Content-Type", "application/json")
		_, _ = w.Write([]byte(`{"code": 0, "data": [{"key": "memory_size", "value": "hello"}]}`))
	}))
	token := "tok"
	c.APIServerClientMap["test"].LoginToken = &token

	if _, err := c.ExecuteUserCommand(&Command{Type: "api_show_variable", Params: map[string]any{"var_name": "memory_size"}}); err != nil {
		t.Fatalf("api_show_variable: %v", err)
	}
	if !strings.Contains(gotPath, "/system/variables/") {
		t.Fatalf("request path = %s, want /system/variables/<encoded name>", gotPath)
	}
	if strings.Contains(gotPath, "memory_size") {
		t.Fatalf("variable name must be base64-encoded in the path, got %s", gotPath)
	}
	if gotAuth != token {
		t.Fatalf("Authorization = %q, want the login token", gotAuth)
	}
}

func TestCLI_AdminListResourcesCommand(t *testing.T) {
	t.Run("requires login", func(t *testing.T) {
		c := &CLI{
			Config:            &CommandLineConfig{CLIMode: AdminMode},
			AdminServerClient: newTestHTTPClient(t, http.HandlerFunc(func(http.ResponseWriter, *http.Request) { t.Error("must not request") })),
		}
		if _, err := c.AdminListResourcesCommand(&Command{Type: "admin_list_resources"}); err == nil {
			t.Fatalf("expected login guard error")
		}
	})

	t.Run("lists resources", func(t *testing.T) {
		token := "admin-tok"
		var gotAuth string
		c := &CLI{
			Config: &CommandLineConfig{CLIMode: AdminMode},
			AdminServerClient: newTestHTTPClient(t, http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				gotAuth = r.Header.Get("Authorization")
				w.Header().Set("Content-Type", "application/json")
				_, _ = w.Write([]byte(`{"code": 0, "data": {"kb.read": true}}`))
			})),
		}
		c.AdminServerClient.LoginToken = &token
		if _, err := c.AdminListResourcesCommand(&Command{Type: "admin_list_resources"}); err != nil {
			t.Fatalf("admin_list_resources: %v", err)
		}
		if gotAuth != token {
			t.Fatalf("Authorization = %q, want the admin login token", gotAuth)
		}
	})
}
