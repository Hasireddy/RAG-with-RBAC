variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
  default     = "rag"
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for Auto Scaling instances"
  type        = list(string)
}

variable "app_sg_id" {
  description = "Security group ID for application instances"
  type        = string
}


variable "target_group_arn" {
  description = "ALB target group ARN"
  type        = string
}

 variable "key_name" {
     description = "EC2 key pair name for SSH access"
     type        = string
 }

variable "api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "desired_capacity" {
  description = "Desired number of EC2 instances"
  type        = number
  default     = 2
}

variable "max_size" {
  description = "Maximum number of EC2 instances"
  type        = number
  default     = 4
}

variable "min_size" {
  description = "Minimum number of EC2 instances"
  type        = number
  default     = 2
}

variable "cpu_target_value" {
  description = "Target CPU utilization percentage"
  type        = number
  default     = 70
}