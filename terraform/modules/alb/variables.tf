variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "List of public subnet IDs for the ALB"
  type        = list(string)
}

variable "alb_sg_id" {
  description = "Security group ID attached to the ALB"
  type        = string
}

variable "name_prefix" {
  description = "Prefix used for resource naming"
  type        = string
}

variable "app_port" {
  description = "Application port"
  type        = number
  default     = 8000
}

variable "health_check_path" {
  description = "ALB health check path"
  type        = string
  default     = "/"
}