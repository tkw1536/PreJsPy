package prejspy

import "fmt"

// ThrowError throws an error
func ThrowError(message string, index int) {
	err := fmt.Sprintf("%s at character %d", message, index)
	panic(err)
}

//     // TODO: Create utility functions for all the other return values also
//     // just so that we are consistent.

// Gets the maximum length of a key in o
func getMaxKeyLen(o map[string]int) (max int) {
	for k := range o {
		if l := strlen(k); l > max {
			max = l
		}
	}
	return
}

// Gets the maximum length of the member of any members of an array.
func getMaxMemLen(ary []string) (max int) {
	for _, k := range ary {
		if l := strlen(k); l > max {
			max = l
		}
	}
	return
}

// substring checks returns a rune-index based substring of expr
func substring(expr string, start, length int) string {
	asRunes := []rune(expr)

	if start >= len(asRunes) {
		return ""
	}

	if start+length > len(asRunes) {
		length = len(asRunes) - start
	}

	return string(asRunes[start : start+length])
}

// strlen returns the rune-based length of string
func strlen(expr string) int {
	return len([]rune(expr))
}

// contains check if haystack contains a substring needle
func contains(haystack []string, needle string) bool {
	for _, hay := range haystack {
		if hay == needle {
			return true
		}
	}
	return false
}
