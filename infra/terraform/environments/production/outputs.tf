# Production Environment Outputs

output "k3s_master_public_ip" {
  description = "Public IP of the K3s master node"
  value       = module.oracle_infra.k3s_master_public_ip
}

output "k3s_master_private_ip" {
  description = "Private IP of the K3s master node"
  value       = module.oracle_infra.k3s_master_private_ip
}

output "k3s_worker_private_ips" {
  description = "Private IPs of K3s worker nodes"
  value       = module.oracle_infra.k3s_worker_private_ips
}

output "ssh_connection" {
  description = "SSH command to connect to master"
  value       = module.oracle_infra.ssh_connection_command
}

output "kubeconfig_command" {
  description = "Command to retrieve kubeconfig"
  value       = module.oracle_infra.kubeconfig_command
}

output "vcn_id" {
  description = "VCN OCID"
  value       = module.oracle_infra.vcn_id
}
