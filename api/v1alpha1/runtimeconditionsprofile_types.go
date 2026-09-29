/*
Copyright 2026 Runtime Conditions Contributors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

package v1alpha1

import (
	metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
	"k8s.io/apimachinery/pkg/runtime"
)

// Workload identifies the single application a profile describes.
type Workload struct {
	// uri is a stable identifier for the workload, e.g. a repo URL.
	// +required
	// +kubebuilder:validation:MinLength=1
	URI string `json:"uri"`

	// version is the workload version this profile was generated for.
	// +optional
	// +kubebuilder:validation:MinLength=1
	Version string `json:"version,omitempty"`
}

// ConditionInterface is the workload-facing interface requirement for a
// Condition. `type` is the only field the core spec reserves; everything
// else here is extension-defined (operations, engine, etc.), so we don't
// type it - we keep it and let a validating webhook check it against
// whatever extension the profile declared.
type ConditionInterface struct {
	// +required
	// +kubebuilder:validation:MinLength=1
	Type string `json:"type"`
}

// Condition is one external runtime dependency a workload requires.
//
// name/optional/kind/interface.type are the fields the core spec reserves,
// so they're typed and validated here. Everything extension-defined
// (additional interface fields, and any extra condition-level fields an
// extension's conditionFields declare) is left schemaless.
// +kubebuilder:pruning:PreserveUnknownFields
type Condition struct {
	// name is a unique label for this condition within the profile.
	// +optional
	// +kubebuilder:validation:MinLength=1
	Name string `json:"name,omitempty"`

	// +optional
	// +kubebuilder:default=false
	Optional bool `json:"optional,omitempty"`

	// kind is the extension-defined integration classification, e.g.
	// "api", "datastore", "cache". Whether a given value is actually
	// backed by a resolved extension is checked by a webhook, not here.
	// +required
	// +kubebuilder:validation:MinLength=1
	Kind string `json:"kind"`

	// extension picks which extension's kind to use, when more than one
	// resolved extension defines the same kind. Checked by a webhook,
	// not here.
	// +optional
	// +kubebuilder:validation:MinLength=1
	Extension string `json:"extension,omitempty"`

	// +required
	// +kubebuilder:pruning:PreserveUnknownFields
	Interface ConditionInterface `json:"interface"`
}

// +kubebuilder:object:root=true
// +kubebuilder:resource:shortName=rcp;rcprofile;rcprofiles

// RuntimeConditionsProfile is the Schema for the runtimeconditionsprofiles API.
//
// Its shape mirrors the Runtime Conditions Profile document directly:
// workload/extensions/conditions are top-level fields, not nested under a
// spec, the same way ConfigMap's data is top-level.
type RuntimeConditionsProfile struct {
	metav1.TypeMeta `json:",inline"`

	// metadata is a standard object metadata
	// +required
	metav1.ObjectMeta `json:"metadata,omitzero"`

	// +required
	Workload Workload `json:"workload"`

	// extensions is the list of extension identifiers (absolute URIs) this
	// profile depends on. Can be empty, can't have duplicates.
	// +required
	// +kubebuilder:validation:items:Format=uri
	// +kubebuilder:validation:XValidation:rule="self.all(e, e.matches('^[A-Za-z][A-Za-z0-9+.-]*:'))",message="each extension must have a URI scheme"
	// +kubebuilder:validation:XValidation:rule="self.all(x, self.exists_one(y, y == x))",message="extensions must not contain duplicate identifiers"
	Extensions []string `json:"extensions"`

	// conditions is the workload's external runtime dependencies. Can be
	// empty.
	// +required
	// +kubebuilder:validation:XValidation:rule="self.filter(c, has(c.name)).all(c, self.filter(d, has(d.name) && d.name == c.name).size() == 1)",message="condition names must be unique within the profile"
	Conditions []Condition `json:"conditions"`
}

// +kubebuilder:object:root=true

// RuntimeConditionsProfileList contains a list of RuntimeConditionsProfile
type RuntimeConditionsProfileList struct {
	metav1.TypeMeta `json:",inline"`
	metav1.ListMeta `json:"metadata,omitzero"`
	Items           []RuntimeConditionsProfile `json:"items"`
}

func init() {
	SchemeBuilder.Register(func(s *runtime.Scheme) error {
		s.AddKnownTypes(SchemeGroupVersion, &RuntimeConditionsProfile{}, &RuntimeConditionsProfileList{})
		return nil
	})
}
