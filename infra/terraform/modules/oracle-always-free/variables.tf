# Oracle Cloud Infrastructure Variables

# Required OCI Authentication Variables
variable "tenancy_ocid" {
  description = "OCID of your tenancy"
  type        = string
}

variable "user_ocid" {
  description = "OCID of the user"
  type        = string
}

variable "fingerprint" {
  description = "Fingerprint of the API key"
  type        = string
}

variable "private_key_path" {
  description = "Path to the private key file"
  type        = string
}

variable "compartment_ocid" {
  description = "OCID of the compartment"
  type        = string
}

variable "region" {
  description = "OCI region"
  type        = string
}

# Project Configuration
variable "project_name" {
  description = "Name of the project (used for resource naming)"
  type        = string
  default     = "kimberly"
}

variable "tags" {
  description = "Freeform tags to apply to resources"
  type        = map(string)
  default = {
    project     = "kimberly"
    environment = "production"
    managed_by  = "terraform"
  }
}

# Network Configuration
variable "vcn_cidr" {
  description = "CIDR block for the VCN"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.0.1.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR block for the private subnet"
  type        = string
  default     = "10.0.2.0/24"
}

variable "ssh_allowed_cidr" {
  description = "CIDR block allowed for SSH access (restrict to your IP for security)"
  type        = string
  default     = null  # Force user to provide a value
}

variable "k8s_api_allowed_cidr" {
  description = "CIDR block allowed for Kubernetes API access (6443)"
  type        = string
  default     = null  # Force user to provide a value
}

# Compute Configuration (Always Free Tier - Ampere A1)
# Always Free: Up to 4 OCPUs and 24GB memory total across all A1 instances
variable "instance_shape" {
  description = "Shape for compute instances (VM.Standard.A1.Flex for Always Free)"
  type        = string
  default     = "VM.Standard.A1.Flex"
}

variable "instance_ocpus" {
  description = "Number of OCPUs for master instance"
  type        = number
  default     = 2
}

variable "instance_memory_gb" {
  description = "Memory in GB for master instance"
  type        = number
  default     = 12
}

variable "worker_count" {
  description = "Number of worker nodes"
  type        = number
  default     = 1
}

variable "worker_ocpus" {
  description = "Number of OCPUs for each worker instance"
  type        = number
  default     = 2
}

variable "worker_memory_gb" {
  description = "Memory in GB for each worker instance"
  type        = number
  default     = 12
}

variable "boot_volume_size_gb" {
  description = "Boot volume size in GB"
  type        = number
  default     = 50
}

variable "data_volume_size_gb" {
  description = "Data volume size in GB (200GB Always Free)"
  type        = number
  default     = 100
}

# SSH Configuration
variable "ssh_public_key" {
  description = "SSH public key for instance access"
  type        = string
}

# K3s Configuration
variable "k3s_token" {
  description = "Token for K3s cluster authentication"
  type        = string
  sensitive   = true
}

variable "k3s_version" {
  description = "K3s version to install"
  type        = string
  default     = "v1.28.4+k3s2"
}
