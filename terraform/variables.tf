variable "api_key" {
  type      = string
  sensitive = true
}

variable "aws_region" {
  description = "AWS region where resources will be deployed"
  type        = string
  default     = "eu-central-1"
}