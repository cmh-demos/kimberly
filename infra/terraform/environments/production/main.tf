# Production Environment - Oracle Always Free
# This configuration deploys Kimberly to Oracle Cloud Always Free tier

terraform {
  required_version = ">= 1.0.0"

  # Uncomment and configure for remote state storage
  # backend "s3" {
  #   bucket   = "kimberly-terraform-state"
  #   key      = "production/terraform.tfstate"
  #   region   = "us-ashburn-1"
  #   endpoint = "https://<namespace>.compat.objectstorage.<region>.oraclecloud.com"
  # }
}

# Configure the OCI provider
provider "oci" {
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  region           = var.region
}

# Use the Oracle Always Free module
module "oracle_infra" {
  source = "../../modules/oracle-always-free"

  # OCI Authentication
  tenancy_ocid     = var.tenancy_ocid
  user_ocid        = var.user_ocid
  fingerprint      = var.fingerprint
  private_key_path = var.private_key_path
  compartment_ocid = var.compartment_ocid
  region           = var.region

  # Project Configuration
  project_name = "kimberly"
  tags = {
    project     = "kimberly"
    environment = "production"
    managed_by  = "terraform"
  }

  # Network Configuration
  vcn_cidr             = "10.0.0.0/16"
  public_subnet_cidr   = "10.0.1.0/24"
  private_subnet_cidr  = "10.0.2.0/24"
  ssh_allowed_cidr     = var.ssh_allowed_cidr
  k8s_api_allowed_cidr = var.k8s_api_allowed_cidr

  # Compute Configuration (Always Free limits)
  # Total: 4 OCPUs, 24GB RAM across all A1 instances
  instance_shape   = "VM.Standard.A1.Flex"
  instance_ocpus   = 2
  instance_memory_gb = 12
  worker_count     = 1
  worker_ocpus     = 2
  worker_memory_gb = 12

  # Storage Configuration
  boot_volume_size_gb = 50
  data_volume_size_gb = 100

  # SSH and K3s Configuration
  ssh_public_key = var.ssh_public_key
  k3s_token      = var.k3s_token
  k3s_version    = "v1.28.4+k3s2"
}
