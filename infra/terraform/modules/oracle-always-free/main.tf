# Oracle Cloud Always Free Tier Infrastructure
# This module provisions OCI resources within Always Free tier limits

terraform {
  required_version = ">= 1.0.0"
  required_providers {
    oci = {
      source  = "oracle/oci"
      version = ">= 5.0.0"
    }
  }
}

# Data sources for availability domains
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.tenancy_ocid
}

# Virtual Cloud Network (VCN)
resource "oci_core_vcn" "kimberly_vcn" {
  compartment_id = var.compartment_ocid
  display_name   = "${var.project_name}-vcn"
  cidr_blocks    = [var.vcn_cidr]
  dns_label      = var.project_name

  freeform_tags = var.tags
}

# Internet Gateway
resource "oci_core_internet_gateway" "igw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.kimberly_vcn.id
  display_name   = "${var.project_name}-igw"
  enabled        = true

  freeform_tags = var.tags
}

# NAT Gateway (for private subnet outbound access)
resource "oci_core_nat_gateway" "nat_gw" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.kimberly_vcn.id
  display_name   = "${var.project_name}-nat-gw"

  freeform_tags = var.tags
}

# Public Route Table
resource "oci_core_route_table" "public_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.kimberly_vcn.id
  display_name   = "${var.project_name}-public-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.igw.id
  }

  freeform_tags = var.tags
}

# Private Route Table
resource "oci_core_route_table" "private_rt" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.kimberly_vcn.id
  display_name   = "${var.project_name}-private-rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_nat_gateway.nat_gw.id
  }

  freeform_tags = var.tags
}

# Public Security List
resource "oci_core_security_list" "public_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.kimberly_vcn.id
  display_name   = "${var.project_name}-public-sl"

  # Allow SSH from allowed CIDR
  ingress_security_rules {
    protocol  = "6" # TCP
    source    = var.ssh_allowed_cidr
    stateless = false

    tcp_options {
      min = 22
      max = 22
    }
  }

  # Allow HTTP
  ingress_security_rules {
    protocol  = "6"
    source    = "0.0.0.0/0"
    stateless = false

    tcp_options {
      min = 80
      max = 80
    }
  }

  # Allow HTTPS
  ingress_security_rules {
    protocol  = "6"
    source    = "0.0.0.0/0"
    stateless = false

    tcp_options {
      min = 443
      max = 443
    }
  }

  # Allow Kubernetes API (6443)
  ingress_security_rules {
    protocol  = "6"
    source    = var.ssh_allowed_cidr
    stateless = false

    tcp_options {
      min = 6443
      max = 6443
    }
  }

  # Allow all egress
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }

  freeform_tags = var.tags
}

# Private Security List
resource "oci_core_security_list" "private_sl" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.kimberly_vcn.id
  display_name   = "${var.project_name}-private-sl"

  # Allow all traffic from VCN
  ingress_security_rules {
    protocol  = "all"
    source    = var.vcn_cidr
    stateless = false
  }

  # Allow all egress
  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
    stateless   = false
  }

  freeform_tags = var.tags
}

# Public Subnet
resource "oci_core_subnet" "public_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.kimberly_vcn.id
  availability_domain        = data.oci_identity_availability_domains.ads.availability_domains[0].name
  cidr_block                 = var.public_subnet_cidr
  display_name               = "${var.project_name}-public-subnet"
  dns_label                  = "public"
  prohibit_public_ip_on_vnic = false
  route_table_id             = oci_core_route_table.public_rt.id
  security_list_ids          = [oci_core_security_list.public_sl.id]

  freeform_tags = var.tags
}

# Private Subnet
resource "oci_core_subnet" "private_subnet" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.kimberly_vcn.id
  availability_domain        = data.oci_identity_availability_domains.ads.availability_domains[0].name
  cidr_block                 = var.private_subnet_cidr
  display_name               = "${var.project_name}-private-subnet"
  dns_label                  = "private"
  prohibit_public_ip_on_vnic = true
  route_table_id             = oci_core_route_table.private_rt.id
  security_list_ids          = [oci_core_security_list.private_sl.id]

  freeform_tags = var.tags
}

# Get the latest Oracle Linux image (ARM-based for Always Free)
data "oci_core_images" "oracle_linux" {
  compartment_id           = var.compartment_ocid
  operating_system         = "Oracle Linux"
  operating_system_version = "8"
  shape                    = var.instance_shape
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

# K3s Master Node (Ampere ARM - Always Free eligible)
resource "oci_core_instance" "k3s_master" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "${var.project_name}-k3s-master"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.instance_ocpus
    memory_in_gbs = var.instance_memory_gb
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.oracle_linux.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_gb
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.public_subnet.id
    assign_public_ip = true
    display_name     = "${var.project_name}-k3s-master-vnic"
    hostname_label   = "k3s-master"
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/templates/k3s-master-init.sh", {
      k3s_token      = var.k3s_token
      project_name   = var.project_name
      k3s_version    = var.k3s_version
    }))
  }

  freeform_tags = var.tags

  lifecycle {
    ignore_changes = [source_details[0].source_id]
  }
}

# K3s Worker Node (Ampere ARM - Always Free eligible)
resource "oci_core_instance" "k3s_worker" {
  count               = var.worker_count
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "${var.project_name}-k3s-worker-${count.index + 1}"
  shape               = var.instance_shape

  shape_config {
    ocpus         = var.worker_ocpus
    memory_in_gbs = var.worker_memory_gb
  }

  source_details {
    source_type             = "image"
    source_id               = data.oci_core_images.oracle_linux.images[0].id
    boot_volume_size_in_gbs = var.boot_volume_size_gb
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.private_subnet.id
    assign_public_ip = false
    display_name     = "${var.project_name}-k3s-worker-${count.index + 1}-vnic"
    hostname_label   = "k3s-worker-${count.index + 1}"
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data = base64encode(templatefile("${path.module}/templates/k3s-worker-init.sh", {
      k3s_token      = var.k3s_token
      master_ip      = oci_core_instance.k3s_master.private_ip
      k3s_version    = var.k3s_version
    }))
  }

  freeform_tags = var.tags

  depends_on = [oci_core_instance.k3s_master]

  lifecycle {
    ignore_changes = [source_details[0].source_id]
  }
}

# Block Volume for persistent storage (200GB Always Free)
resource "oci_core_volume" "data_volume" {
  compartment_id      = var.compartment_ocid
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "${var.project_name}-data-volume"
  size_in_gbs         = var.data_volume_size_gb

  freeform_tags = var.tags
}

# Attach block volume to master node
resource "oci_core_volume_attachment" "data_volume_attachment" {
  attachment_type = "paravirtualized"
  instance_id     = oci_core_instance.k3s_master.id
  volume_id       = oci_core_volume.data_volume.id
  display_name    = "${var.project_name}-data-volume-attachment"
}
