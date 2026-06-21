# Step 6: Terraform Infrastructure as Code

**Goal:** Satisfy the requirement: *"Infrastructure must be provisioned through Terraform... create a cloud-native analytics platform."* Prove infrastructure automation.

## What you are doing on screen:
1. Stay in your **IDE (VS Code)**.
2. Open the `terraform/eks.tf` file.
3. Briefly show `terraform/vpc.tf` as well.

## What you should say exactly:
> "The case study strictly mandated that infrastructure must be provisioned through **Terraform**.
> 
> *(Point to the files)*
> Rather than manually clicking through a cloud console, I wrote modular Infrastructure as Code to provision an AWS EKS (Elastic Kubernetes Service) cluster from scratch. 
> 
> In `vpc.tf`, I am configuring a highly available Virtual Private Cloud spanning 3 Availability Zones with private subnets for security. 
> 
> In `eks.tf`, I define the Kubernetes cluster. Notice that I am utilizing managed node groups optimized with `t3.large` instances to specifically support the compute-heavy Risk Engine calculations required by FinSight."

---
**Next Step -> Open `07_Observability_Security.md`**
