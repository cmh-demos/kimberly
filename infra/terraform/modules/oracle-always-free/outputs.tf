# Output values for Oracle Always Free module

output "vcn_id" {
  description = "OCID of the VCN"
  value       = oci_core_vcn.kimberly_vcn.id
}

output "public_subnet_id" {
  description = "OCID of the public subnet"
  value       = oci_core_subnet.public_subnet.id
}

output "private_subnet_id" {
  description = "OCID of the private subnet"
  value       = oci_core_subnet.private_subnet.id
}

output "k3s_master_public_ip" {
  description = "Public IP address of the K3s master node"
  value       = oci_core_instance.k3s_master.public_ip
}

output "k3s_master_private_ip" {
  description = "Private IP address of the K3s master node"
  value       = oci_core_instance.k3s_master.private_ip
}

output "k3s_worker_private_ips" {
  description = "Private IP addresses of K3s worker nodes"
  value       = oci_core_instance.k3s_worker[*].private_ip
}

output "data_volume_id" {
  description = "OCID of the data block volume"
  value       = oci_core_volume.data_volume.id
}

output "ssh_connection_command" {
  description = "SSH command to connect to the master node"
  value       = "ssh opc@${oci_core_instance.k3s_master.public_ip}"
}

output "kubeconfig_command" {
  description = "Command to get kubeconfig from master node"
  value       = "ssh opc@${oci_core_instance.k3s_master.public_ip} 'sudo cat /etc/rancher/k3s/k3s.yaml'"
}
