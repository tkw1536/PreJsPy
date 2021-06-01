package prejspy

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"os"
	"path/filepath"
	"reflect"
	"runtime"
	"strings"
	"testing"
)

func TestPreJsPy(t *testing.T) {

	// create a new parser
	parser := NewPreJSPy()

	// list the files in the test directory!
	_, filename, _, _ := runtime.Caller(0)
	testDirectory := filepath.Join(filename, "..", "..", "..", "tests")
	files, err := os.ReadDir(testDirectory)
	if err != nil {
		panic(err)
	}

	for _, f := range files {
		// it has to be a regular file with .json ending!
		if !f.Type().IsRegular() {
			continue
		}
		name := f.Name()
		if !strings.HasSuffix(name, ".json") {
			continue
		}

		testfile := filepath.Join(testDirectory, name)
		t.Run(name, func(t *testing.T) {
			cases, err := readTestFile(testfile)
			if err != nil {
				panic(err)
			}

			for _, c := range cases {
				t.Run(c.Message, func(t *testing.T) {
					result := c.Run(parser)
					if result != nil {
						t.Error(result)
					}
				})
			}
		})
	}

}

type TestCase struct {
	Input   string          `json:"input"`
	Output  json.RawMessage `json:"output"`
	Message string          `json:"message"`
}

// Run a TestCase using the provided parser
func (tc TestCase) Run(parser *PreJSPy) error {
	parsed := parser.Parse(tc.Input)
	data, err := json.Marshal(parsed)
	if err != nil {
		return err
	}
	ok, err := jsonequal(string(data), string(tc.Output))
	if !ok || err != nil {
		return fmt.Errorf("Expected %s, got: %s", string(tc.Output), string(data))
	}
	return nil
}

// readTestFile reads a set of cases from a TestCase!
func readTestFile(path string) (cases []TestCase, err error) {
	asset, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	bytes, err := ioutil.ReadAll(asset)
	if err != nil {
		return nil, err
	}
	err = json.Unmarshal(bytes, &cases)
	return
}

// jsonequal checks if two json strings are equal, without order
func jsonequal(a, b string) (bool, error) {
	var j, j2 interface{}
	d := json.NewDecoder(strings.NewReader(a))
	if err := d.Decode(&j); err != nil {
		return false, err
	}
	d = json.NewDecoder(strings.NewReader(b))
	if err := d.Decode(&j2); err != nil {
		return false, err
	}
	return reflect.DeepEqual(j2, j), nil
}
