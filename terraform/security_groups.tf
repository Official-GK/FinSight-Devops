# ──────────────────────────────────────────────────────────────────────────────
# security_groups.tf — All Security Groups for the Platform
# ──────────────────────────────────────────────────────────────────────────────

# ── Bastion Host SG ───────────────────────────────────────────────────────────
# Allows SSH only from corporate/admin IP ranges
resource "aws_security_group" "bastion" {
  name        = "${var.project_name}-bastion-sg-${var.environment}"
  description = "Security group for the bastion/jump host. SSH from admin CIDRs only."
  vpc_id      = aws_vpc.main.id

  # Port 22: SSH — restricted to admin CIDR blocks
  ingress {
    description = "SSH from admin IP ranges"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.admin_cidr_blocks
  }

  # Allow all outbound traffic from bastion (needed for yum/apt updates)
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-bastion-sg-${var.environment}"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ── Load Balancer SG ──────────────────────────────────────────────────────────
# Internet-facing NLB for the Analytics API
resource "aws_security_group" "alb" {
  name        = "${var.project_name}-alb-sg-${var.environment}"
  description = "Security group for the public-facing Application Load Balancer."
  vpc_id      = aws_vpc.main.id

  # Port 80: HTTP — public internet access
  ingress {
    description = "HTTP from internet"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Port 443: HTTPS — public internet access (TLS termination at LB)
  ingress {
    description = "HTTPS from internet"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "All outbound to VPC"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [var.vpc_cidr]
  }

  tags = {
    Name = "${var.project_name}-alb-sg-${var.environment}"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ── EKS Cluster Control Plane SG ─────────────────────────────────────────────
resource "aws_security_group" "eks_cluster" {
  name        = "${var.project_name}-eks-cluster-sg-${var.environment}"
  description = "Security group for the EKS cluster control plane API server."
  vpc_id      = aws_vpc.main.id

  # API server inbound from worker nodes
  ingress {
    description     = "Kubernetes API from worker nodes"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  # API server inbound from bastion (for kubectl)
  ingress {
    description     = "Kubernetes API from bastion host"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  egress {
    description = "All outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-eks-cluster-sg-${var.environment}"
  }
}

# ── EKS Worker Nodes SG ───────────────────────────────────────────────────────
resource "aws_security_group" "eks_nodes" {
  name        = "${var.project_name}-eks-nodes-sg-${var.environment}"
  description = "Security group for EKS worker nodes. Controls intra-cluster traffic."
  vpc_id      = aws_vpc.main.id

  # Port 22: SSH from bastion only (for emergency node debugging)
  ingress {
    description     = "SSH from bastion host"
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  # Port 80: HTTP traffic from ALB to Analytics API pods
  ingress {
    description     = "HTTP from ALB to Analytics API"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Port 443: HTTPS from ALB
  ingress {
    description     = "HTTPS from ALB"
    from_port       = 443
    to_port         = 443
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # Port 3000: Grafana dashboard
  ingress {
    description = "Grafana dashboard access from VPC"
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Port 9090: Prometheus metrics scraping
  ingress {
    description = "Prometheus metrics scraping"
    from_port   = 9090
    to_port     = 9090
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Port 5601: Kibana dashboard access
  ingress {
    description = "Kibana dashboard from VPC"
    from_port   = 5601
    to_port     = 5601
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Port 8000: Analytics API (internal)
  ingress {
    description = "Analytics API port"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Port 8001: Risk Engine (internal only)
  ingress {
    description = "Risk Engine internal port"
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Port 9200: Elasticsearch REST API
  ingress {
    description = "Elasticsearch REST API"
    from_port   = 9200
    to_port     = 9200
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Port 5044: Logstash Beats input
  ingress {
    description = "Logstash Beats input"
    from_port   = 5044
    to_port     = 5044
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Port 8200: HashiCorp Vault API
  ingress {
    description = "HashiCorp Vault API"
    from_port   = 8200
    to_port     = 8200
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  # Node-to-node communication (all intra-cluster traffic)
  ingress {
    description = "All intra-cluster node communication"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
  }

  # Kubelet API (cluster control plane → nodes)
  ingress {
    description     = "EKS control plane to kubelet"
    from_port       = 10250
    to_port         = 10250
    protocol        = "tcp"
    security_groups = [aws_security_group.eks_cluster.id]
  }

  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-eks-nodes-sg-${var.environment}"
    "kubernetes.io/cluster/${var.eks_cluster_name}" = "owned"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# ── Vault SG ──────────────────────────────────────────────────────────────────
resource "aws_security_group" "vault" {
  name        = "${var.project_name}-vault-sg-${var.environment}"
  description = "Security group for HashiCorp Vault cluster."
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "Vault API from EKS nodes (for Vault Agent)"
    from_port   = 8200
    to_port     = 8200
    protocol    = "tcp"
    security_groups = [aws_security_group.eks_nodes.id]
  }

  ingress {
    description     = "Vault API from bastion"
    from_port       = 8200
    to_port         = 8200
    protocol        = "tcp"
    security_groups = [aws_security_group.bastion.id]
  }

  # Vault cluster port (HA Raft replication)
  ingress {
    description = "Vault cluster replication"
    from_port   = 8201
    to_port     = 8201
    protocol    = "tcp"
    self        = true
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-vault-sg-${var.environment}"
  }
}
