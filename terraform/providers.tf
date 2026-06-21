# ──────────────────────────────────────────────────────────────────────────────
# Terraform Provider & Backend Configuration
# ──────────────────────────────────────────────────────────────────────────────
terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.45"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.29"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.13"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  # ── Remote State Backend (S3 + DynamoDB for state locking) ─────────────────
  # Replace bucket/table names with your own before running terraform init.
  backend "s3" {
    bucket         = "financial-risk-tf-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "financial-risk-tf-lock"  # For state locking

    # Enable server-side encryption with a KMS key
    kms_key_id = "alias/terraform-state-key"
  }
}

# ── AWS Provider ──────────────────────────────────────────────────────────────
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "financial-risk-platform"
      Environment = var.environment
      ManagedBy   = "terraform"
      Team        = "sre"
      CostCenter  = "engineering"
    }
  }
}

# ── Kubernetes Provider (authenticated via EKS cluster endpoint) ──────────────
provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  token                  = data.aws_eks_cluster_auth.cluster.token
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    token                  = data.aws_eks_cluster_auth.cluster.token
  }
}

# ── EKS Auth Data Source ──────────────────────────────────────────────────────
data "aws_eks_cluster_auth" "cluster" {
  name = module.eks.cluster_name
}

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
