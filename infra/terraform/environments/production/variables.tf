# Production Environment Variables

# OCI Authentication (required)
variable "tenancy_ocid" {
  description = "OCID of your OCI tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID of the OCI user"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of the OCI API key"
  type        = string
}

variable "private_key_path" {
  description = "Path to the OCI API private key file"
  type        = string
}

variable "compartment_ocid" {
  description = "OCID of the OCI compartment"
  type        = string
}

variable "region" {
  description = "OCI region (e.g., us-ashburn-1)"
  type        = string
}

# SSH Configuration (required)
variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access"
  type        = string
  default     = "0.0.0.0/0"
}

# K3s Configuration (required)
variable "k3s_token" {
  description = "Token for K3s cluster authentication"
  type        = string
  sensitive   = true
}
