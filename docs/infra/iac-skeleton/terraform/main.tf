// Terraform skeleton for Kimberly
// This is a minimal, provider-agnostic layout. Fill provider blocks and modules per provider.

terraform {
  required_version = ">= 1.3.0"
 }

// Example variable-driven provider block (override in terraform.tfvars)
variable "provider" {
  type    = string
  default = "local"
}

// Example inputs for modules (placeholder modules are expected in a real setup)
variable "project_name" {
  type    = string
  default = "kimberly"
}

// Example module layout (to be implemented per provider)
// module "cluster" {
//   source = "./modules/cluster"
//   provider = var.provider
//   name = var.project_name
// }

// module "postgres" {
//   source = "./modules/postgres"
//   instance_size = var.db_instance_size
// }

// module "redis" { source = "./modules/redis" }
// module "object_store" { source = "./modules/minio" }

// Output placeholders
output "cluster_endpoint" {
  value = "TODO: cluster endpoint"
}
